# -*- coding: utf-8 -*-
"""批量抓取节点照片/Logo：cn.bing.com 图片搜索 → turl 缩略图（改写为 tse1-mm.cn.bing.net 国内可下载域名）
→ 96px JPEG → base64 data URI → photos.json。支持断点续跑；失败记入 photos_failed.json。
手工纠正：在 photos_manual.json 中放 {"节点id": "data:image/..."}，合并时优先于自动抓取。"""
import json, re, time, base64, io, sys
import urllib.request, urllib.parse
import html as htmllib
from pathlib import Path
from PIL import Image

BASE = Path(__file__).parent
DATA = json.loads((BASE / "quantum_network.json").read_text(encoding="utf-8"))
PHOTOS_FILE = BASE / "photos.json"
FAILED_FILE = BASE / "photos_failed.json"
MANUAL_FILE = BASE / "photos_manual.json"

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def query_of(n):
    t = n["type"]
    zh = n.get("country") == "中国"
    en = (n.get("name_en") or "").strip()
    name = n["name"]
    if t in ("scholar", "student", "exec"):
        if not zh and en:
            return f"{en} quantum"
        return name
    # 机构类：logo
    if not zh and en:
        return f"{en} logo"
    return f"{name} logo"

def bing_thumbs(q, want=4):
    url = "https://cn.bing.com/images/search?" + urllib.parse.urlencode({"q": q, "form": "HDRSC2"})
    req = urllib.request.Request(url, headers=UA)
    h = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    ts = [htmllib.unescape(x) for x in re.findall(r'&quot;turl&quot;:&quot;(.*?)&quot;', h)]
    out = []
    for t in ts:
        # 改写为国内可下载的旧域名
        t = re.sub(r"https://ts\d\.mm\.bing\.net/", "https://tse1-mm.cn.bing.net/", t)
        if t not in out:
            out.append(t)
        if len(out) >= want:
            break
    return out

def fetch_image(url):
    req = urllib.request.Request(url, headers={**UA, "Referer": "https://cn.bing.com/"})
    data = urllib.request.urlopen(req, timeout=20).read()
    if len(data) < 800:
        raise ValueError("too small")
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((96, 96), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def main():
    photos = json.loads(PHOTOS_FILE.read_text(encoding="utf-8")) if PHOTOS_FILE.exists() else {}
    manual = json.loads(MANUAL_FILE.read_text(encoding="utf-8")) if MANUAL_FILE.exists() else {}
    failed = []
    nodes = DATA["nodes"]
    todo = [n for n in nodes if n["id"] not in photos and n["id"] not in manual]
    print(f"total {len(nodes)}, already {len(photos)+len(manual)}, todo {len(todo)}", flush=True)
    for i, n in enumerate(todo):
        nid = n["id"]
        q = query_of(n)
        ok = False
        err = ""
        try:
            thumbs = bing_thumbs(q)
            for t in thumbs:
                try:
                    photos[nid] = fetch_image(t)
                    ok = True
                    break
                except Exception as e:
                    err = f"{type(e).__name__}"
                    continue
            if not ok and not thumbs:
                err = "no thumbs"
        except Exception as e:
            err = f"search:{type(e).__name__}"
        if not ok:
            failed.append({"id": nid, "name": n["name"], "q": q, "err": err})
        if (i + 1) % 20 == 0 or i == len(todo) - 1:
            print(f"[{i+1}/{len(todo)}] ok={len(photos)} fail={len(failed)}", flush=True)
            PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.12)
    photos.update(manual)
    PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
    FAILED_FILE.write_text(json.dumps(failed, ensure_ascii=False, indent=1), encoding="utf-8")
    total_b64 = sum(len(v) for v in photos.values())
    print(f"DONE photos={len(photos)} failed={len(failed)} b64_total={total_b64/1024:.0f}KB")

if __name__ == "__main__":
    main()
