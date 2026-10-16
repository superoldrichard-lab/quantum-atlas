# -*- coding: utf-8 -*-
"""机构 Logo 重抓（提升准确率）：
1) 从节点 source/lab 提取官网域名，必应结果按 murl 与官网域名的匹配度排序，优先取官网来源图
2) 官网 favicon 兜底
3) 全部走 tse1-mm.cn.bing.net 缩略图下载 → 96px → base64，覆盖 photos.json 中对应条目
"""
import json, re, time, sys
import urllib.request, urllib.parse
import html as htmllib
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from fetch_photos import fetch_image, UA

BASE = Path(__file__).parent
DATA = json.loads((BASE / "quantum_network.json").read_text(encoding="utf-8"))
PHOTOS_FILE = BASE / "photos.json"

def domain_of(n):
    for f in ("lab", "source"):
        u = (n.get(f) or "").strip()
        if u.startswith("http"):
            host = urllib.parse.urlparse(u).netloc.lower()
            host = re.sub(r"^www\.", "", host)
            if host:
                return host
    return ""

def brand_of(n):
    en = (n.get("name_en") or n["name"]).lower()
    w = re.findall(r"[a-z0-9]+", en)
    return w[0] if w else ""

def bing_items(q, want=10):
    url = "https://cn.bing.com/images/search?" + urllib.parse.urlencode({"q": q, "form": "HDRSC2"})
    req = urllib.request.Request(url, headers=UA)
    h = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    items = []
    for m in re.findall(r'm="(\{&quot;.*?&quot;\})"', h):
        try:
            d = json.loads(htmllib.unescape(m))
        except Exception:
            continue
        t = d.get("turl")
        if not t:
            continue
        t = re.sub(r"https://ts\d\.mm\.bing\.net/", "https://tse1-mm.cn.bing.net/", t)
        items.append({"turl": t, "murl": d.get("murl", ""), "title": d.get("t", "")})
        if len(items) >= want:
            break
    return items

def fetch_favicon(domain):
    for path in ("/favicon.ico", "/favicon.png", "/apple-touch-icon.png"):
        try:
            req = urllib.request.Request("https://" + domain + path, headers=UA)
            data = urllib.request.urlopen(req, timeout=10).read()
            if len(data) > 300:
                return fetch_image_bytes(data)
        except Exception:
            continue
    return None

def fetch_image_bytes(data):
    import io, base64
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((96, 96), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def main():
    photos = json.loads(PHOTOS_FILE.read_text(encoding="utf-8"))
    orgs = [n for n in DATA["nodes"] if n["type"] in ("university", "company", "investor")]
    print(f"orgs: {len(orgs)}", flush=True)
    ok, fail = 0, []
    for i, n in enumerate(orgs):
        nid, dom, brand = n["id"], domain_of(n), brand_of(n)
        en = (n.get("name_en") or "").strip()
        q = f"{en} logo" if (n.get("country") != "中国" and en) else f"{n['name']} logo"
        got = None
        try:
            items = bing_items(q)
            def score(it):
                mh = urllib.parse.urlparse(it["murl"]).netloc.lower()
                s = 0
                if dom and (dom in mh): s += 100
                if brand and brand in mh: s += 40
                if brand and brand in it["title"].lower(): s += 10
                if "logo" in it["title"].lower(): s += 6
                return -s
            items.sort(key=score)
            for it in items[:5]:
                try:
                    got = fetch_image(it["turl"]); break
                except Exception:
                    continue
        except Exception:
            pass
        if not got and dom:
            try:
                got = fetch_favicon(dom)
            except Exception:
                got = None
        if got:
            photos[nid] = got; ok += 1
        else:
            fail.append({"id": nid, "name": n["name"], "q": q, "dom": dom})
        if (i + 1) % 25 == 0 or i == len(orgs) - 1:
            print(f"[{i+1}/{len(orgs)}] ok={ok} fail={len(fail)}", flush=True)
            PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.12)
    PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
    (BASE / "logos_failed.json").write_text(json.dumps(fail, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DONE ok={ok} fail={len(fail)}")

if __name__ == "__main__":
    main()
