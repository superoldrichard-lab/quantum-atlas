# -*- coding: utf-8 -*-
"""
量子图谱 · 一体服务（页面托管 + 大模型接口转发 · 服务端代持 Key）

两种用法：

【本地】双击 start_local_server.bat（或 python llm_proxy.py）
  解决 WorkBuddy 应用内预览面板的 CSP 拦截：预览服务下发的 connect-src 只放行
  'self' 与 http://127.0.0.1:*，不含 api.moonshot.cn。本服务在 127.0.0.1:8790 上
  同时托管页面并转发接口。浏览器打开 http://127.0.0.1:8790/ 即全功能可用。

【线上】发布为 Python 服务（沙箱注入 PORT 环境变量，需绑定 0.0.0.0）
  关键点：**API Key 只存在于服务端进程，浏览器端拿不到、发布包内也不含任何密钥文件。**
  线上问答走云服务代持（前端 `llmMode: cloud`），本服务的 /v1/chat/completions 仅作本地开发用。

【密钥读取顺序 —— 全部在项目目录之外】
    1) 环境变量 MOONSHOT_API_KEY / LLM_API_KEY / KIMI_API_KEY
    2) 环境变量 LLM_CONFIG_FILE 指向的 JSON 文件（形如 {"api_key": "sk-..."}）
    3) 用户目录 ~/.quantum-graph/llm_server_config.json
  ⚠ 本项目目录内的 llm_server_config.json 会被**忽略**（只告警）：该文件会随发布包上传到沙箱，
    属于泄露面，故不再支持。迁移：把文件移到 ~/.quantum-graph/ 即可。
  浏览器端不再发送任何凭据；本服务未配置 Key 时直接返回 401 并给出运维提示。

可选环境变量：
  PORT            监听端口（发布沙箱自动注入；本地默认 8790）
  HOST            绑定地址（默认：检测到 PORT 时用 0.0.0.0，否则 127.0.0.1）
  RATE_LIMIT      每 IP 每分钟最大问答次数（默认 30，设 0 关闭限流）

零第三方依赖（Python 标准库）。
"""
import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

UPSTREAM = "https://api.moonshot.cn/v1/chat/completions"
ROOT = os.path.dirname(os.path.abspath(__file__))
SERVICE_TAG = "quantum-graph-llm-proxy"

# —— 密钥只从项目目录之外读取（见模块 docstring）——
HOME_CONFIG = os.path.join(os.path.expanduser("~"), ".quantum-graph", "llm_server_config.json")
# 历史遗留位置：项目目录内。会随发布包上传，属于泄露面 → 只告警、不使用
LEGACY_CONFIG = os.path.join(ROOT, "llm_server_config.json")
# 静态服务层再兜一道：这些名字即使落在允许后缀里也拒绝
SECRET_NAMES = {"llm_server_config.json", ".env", "secrets.json", "credentials.json"}

# 仅这些后缀可被 HTTP 读取；.py / .json / .csv / .bat 等一律拒绝（含含 Key 的配置文件与数据导出）
ALLOWED_EXT = {".html", ".htm", ".js", ".css", ".png", ".jpg", ".jpeg",
               ".svg", ".ico", ".webp", ".woff2"}
CT = {
    ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
    ".json": "application/json; charset=utf-8", ".csv": "text/csv; charset=utf-8",
    ".md": "text/plain; charset=utf-8", ".txt": "text/plain; charset=utf-8",
    ".js": "application/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml", ".ico": "image/x-icon", ".webp": "image/webp",
}


def _read_config(path):
    """从 JSON 文件里取 api_key；失败返回空串。"""
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        return str(cfg.get("api_key") or "").strip()
    except FileNotFoundError:
        return ""
    except Exception as e:                       # 配置损坏不应导致服务起不来
        sys.stderr.write("[proxy] 读取 %s 失败：%s\n" % (path, e))
        return ""


def load_server_key():
    """返回 (key, 来源说明)。只从项目目录之外读取，环境变量优先。

    顺序：环境变量 → LLM_CONFIG_FILE → ~/.quantum-graph/llm_server_config.json
    项目目录内的 llm_server_config.json 会被忽略（只告警）——它会被打进发布包上传，属泄露面。
    """
    for name in ("MOONSHOT_API_KEY", "LLM_API_KEY", "KIMI_API_KEY"):
        v = (os.environ.get(name) or "").strip()
        if v:
            return v, "env:" + name
    p = (os.environ.get("LLM_CONFIG_FILE") or "").strip()
    if p:
        v = _read_config(p)
        if v:
            return v, "file:" + p
    v = _read_config(HOME_CONFIG)
    if v:
        return v, "file:~/.quantum-graph/llm_server_config.json"
    return "", "none"


def warn_legacy_config():
    """项目目录内若残留密钥文件，醒目告警（不使用它）。"""
    if os.path.isfile(LEGACY_CONFIG):
        sys.stderr.write(
            "\n[proxy] ⚠⚠ 检测到项目目录内的 %s\n"
            "[proxy] ⚠⚠ 该文件会随发布包上传到沙箱，属于泄露面，**已忽略、未加载**。\n"
            "[proxy] ⚠⚠ 请把它移到项目外：\n"
            "[proxy]       mkdir -p ~/.quantum-graph && mv \"%s\" ~/.quantum-graph/\n\n"
            % (LEGACY_CONFIG, LEGACY_CONFIG)
        )


SERVER_KEY, KEY_SOURCE = load_server_key()
RATE_LIMIT = int(os.environ.get("RATE_LIMIT") or 30)
_hits = {}
_hits_lock = threading.Lock()


def rate_ok(ip):
    """每 IP 每分钟限流，避免公开站点被滥用刷额度。"""
    if RATE_LIMIT <= 0:
        return True, 0
    now = time.time()
    with _hits_lock:
        q = [t for t in _hits.get(ip, []) if now - t < 60]
        if len(q) >= RATE_LIMIT:
            _hits[ip] = q
            return False, 0
        q.append(now)
        _hits[ip] = q
        return True, RATE_LIMIT - len(q)


class Handler(BaseHTTPRequestHandler):
    server_version = "QuantumGraphServer/2.0"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")

    def _send(self, code, data, ctype="application/json; charset=utf-8"):
        if isinstance(data, str):
            data = data.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False))

    # ---------- 路由 ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            # 只暴露「是否已配置 Key」，绝不返回 Key 本身
            return self._json(200, {
                "ok": True, "service": SERVICE_TAG,
                "keyConfigured": bool(SERVER_KEY), "keySource": KEY_SOURCE,
                "rateLimitPerMin": RATE_LIMIT,
            })
        if path in ("/", "/workbench", "/workbench.html"):
            name = "workbench.html"
        elif path in ("/graph", "/index", "/index.html"):
            name = "index.html"
        else:
            name = path.lstrip("/") or "workbench.html"
        # 隐藏文件/目录（.tmp_*、.workbuddy 等）一律不对外，避免临时产物被公开托管
        parts = [p for p in name.split("/") if p not in ("", ".")]
        if any(p == ".." or p.startswith(".") for p in parts):
            return self._send(403, "403 forbidden", "text/plain; charset=utf-8")
        # 密钥类文件名再兜一道（防止将来有人放宽后缀白名单）
        if os.path.basename(name).lower() in SECRET_NAMES:
            return self._send(403, "403 forbidden", "text/plain; charset=utf-8")
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_EXT:
            return self._send(403, "403 forbidden", "text/plain; charset=utf-8")
        fp = os.path.abspath(os.path.join(ROOT, name))
        # 只允许本目录（含子目录）下的文件，避免路径穿越
        if not fp.startswith(ROOT + os.sep) or not os.path.isfile(fp):
            return self._send(404, "404 not found", "text/plain; charset=utf-8")
        with open(fp, "rb") as f:
            data = f.read()
        ctype = CT.get(ext, "application/octet-stream")
        self._send(200, data, ctype)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        if path != "/v1/chat/completions":
            return self._json(404, {"error": {"message": "not found: " + path}})
        ip = self.client_address[0]
        ok, left = rate_ok(ip)
        if not ok:
            return self._json(429, {"error": {"message": "请求过于频繁（每分钟上限 %d 次），请稍后再试" % RATE_LIMIT}})
        # 一律使用服务端代持的 Key。浏览器端不再发送任何凭据（前端已无 Key 输入）。
        if not SERVER_KEY:
            return self._json(401, {"error": {"message": (
                "服务端未配置大模型 API Key。请在服务端设置环境变量 MOONSHOT_API_KEY，"
                "或把 llm_server_config.json 放到 ~/.quantum-graph/ 后重启本服务。"
                "（出于安全考虑，本项目不再支持在浏览器端填写 Key）")}})
        auth = "Bearer " + SERVER_KEY
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        body = self.rfile.read(n)
        req = urllib.request.Request(
            UPSTREAM, data=body,
            headers={"Content-Type": "application/json", "Authorization": auth},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                self._send(r.status, r.read())
        except urllib.error.HTTPError as e:
            self._send(e.code, e.read())
        except Exception as e:  # 网络异常
            self._json(502, {"error": {"message": "转发失败：%s" % e}})

    def log_message(self, fmt, *args):
        sys.stderr.write("[proxy] %s - %s\n" % (self.address_string(), fmt % args))


def main():
    ap = argparse.ArgumentParser(description="量子图谱服务（页面托管 + 大模型接口转发）")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT") or 8790))
    ap.add_argument("--host", default=os.environ.get("HOST") or ("0.0.0.0" if os.environ.get("PORT") else "127.0.0.1"))
    args = ap.parse_args()
    warn_legacy_config()
    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print("量子图谱工作台已启动：")
    print("  页面地址   http://%s:%d/   (根路径即查询工作台)" % (args.host, args.port))
    print("  纯图版     http://%s:%d/graph" % (args.host, args.port))
    print("  接口转发   /v1/chat/completions  ->  %s" % UPSTREAM)
    if SERVER_KEY:
        print("  API Key    服务端代持（来源：%s）；浏览器端不携带任何凭据" % KEY_SOURCE)
    else:
        print("  API Key    ⚠ 未配置：线上请走云服务问答；本地开发请设置环境变量 MOONSHOT_API_KEY")
        print("             或创建 ~/.quantum-graph/llm_server_config.json（**不要**放在项目目录内）")
    print("  限流       %s" % ("每 IP 每分钟 %d 次" % RATE_LIMIT if RATE_LIMIT > 0 else "已关闭"))
    print("  静态目录   %s" % ROOT)
    print("按 Ctrl+C 停止。")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止。")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
