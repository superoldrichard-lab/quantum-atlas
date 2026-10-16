# -*- coding: utf-8 -*-
"""照片重抓 v2（权威来源优先，全量重建）：
优先级：
  机构(大学/公司/投资机构): Wikidata P154 logo → P18 → Clearbit(域名) → favicon → Bing(en-US,官网域名加权) → 字母头像
  人物(学者/学生/创始人):  Wikidata P18 → Bing(en-US, 仅限权威域名: wikipedia/高校/机构官网) → 字母头像
产出: photos.json (id -> dataURL), photos_report.json (id -> 来源/URL/QID)
"""
import json, re, time, sys, io, base64, hashlib
import urllib.request, urllib.parse
import html as htmllib
from pathlib import Path

BASE = Path(__file__).parent
DATA = json.loads((BASE / "quantum_network.json").read_text(encoding="utf-8"))
PHOTOS_FILE = BASE / "photos.json"
REPORT_FILE = BASE / "photos_report.json"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# ---------- 基础工具 ----------
def to_dataURL(data, size=96, ratio=(0.33, 3.0)):
    from PIL import Image
    im = Image.open(io.BytesIO(data)).convert("RGB")
    if min(im.size) < 24:
        raise ValueError("too small")
    r = im.size[0] / im.size[1]
    if not (ratio[0] <= r <= ratio[1]):
        raise ValueError(f"bad ratio {r:.2f}")
    im.thumbnail((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

def http_get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read()

def api_get(url, timeout=20):
    return json.loads(http_get(url, timeout).decode("utf-8", "replace"))

# ---------- 字母头像兜底 ----------
PALETTE = ["#3b5bdb", "#7048e8", "#0b7285", "#2f9e44", "#e8590c", "#c2255c", "#495057", "#1c7ed6"]
def avatar(n):
    from PIL import Image, ImageDraw, ImageFont
    name = n.get("name_en") or n["name"]
    parts = re.findall(r"[A-Za-z]+", name)
    if parts:
        initials = (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()
    else:
        initials = n["name"][0]
    color = PALETTE[int(hashlib.md5(n["id"].encode()).hexdigest(), 16) % len(PALETTE)]
    im = Image.new("RGB", (96, 96), color)
    dr = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 40)
    except Exception:
        font = ImageFont.load_default()
    bb = dr.textbbox((0, 0), initials, font=font)
    dr.text(((96 - bb[2] + bb[0]) / 2, (96 - bb[3] + bb[1]) / 2 - 4), initials, fill="white", font=font)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

# ---------- Wikidata（当前网络被墙，默认关闭；WIKIDATA=1 启用）----------
import os
WIKIDATA_ON = os.environ.get("WIKIDATA") == "1"

def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())

PERSON_DESC = ("physicist", "scientist", "researcher", "professor", "engineer",
               "computer scientist", "chemist", "entrepreneur", "executive", "investor",
               "mathematician", "academic", "物理学家", "科学家", "研究员", "教授", "企业家")
ORG_DESC = ("university", "college", "institute", "company", "corporation", "enterprise",
            "business", "organization", "firm", "fund", "大学", "学院", "研究所", "公司", "企业", "机构")

def wikidata_search(n):
    """返回 (qid, img_prop) 或 None。机构找 P154/P18，人物找 P18。"""
    is_person = n["type"] in ("scholar", "student", "exec")
    cands = []
    for q in [n.get("name_en"), n["name"]]:
        if not q:
            continue
        try:
            r = api_get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
                "action": "wbsearchentities", "search": q, "language": "en",
                "uselang": "en", "format": "json", "limit": 5, "type": "item"}))
            cands.extend(r.get("search", []))
        except Exception:
            pass
        time.sleep(0.15)
    target = norm(n.get("name_en") or n["name"])
    target_zh = n["name"]
    desc_pool = PERSON_DESC if is_person else ORG_DESC
    best = None
    for c in cands:
        label = c.get("label", "")
        desc = (c.get("description") or "").lower()
        aliases = " ".join((c.get("aliases") or []) if isinstance(c.get("aliases"), list) else [])
        hit = (norm(label) == target or norm(label) in target or (target and target in norm(label))
               or label == target_zh or target_zh in aliases)
        if not hit:
            continue
        if is_person and not any(k in desc for k in desc_pool):
            continue
        if not is_person and desc and not any(k in desc for k in desc_pool):
            # 机构描述完全不沾边才跳过（desc 为空时放行）
            continue
        best = c["id"]
        break
    if not best:
        return None
    try:
        ent = api_get("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
            "action": "wbgetentities", "ids": best, "props": "claims", "format": "json"}))["entities"][best]
    except Exception:
        return None
    claims = ent.get("claims", {})
    props = ("P18",) if is_person else ("P154", "P18")
    for p in props:
        for cl in claims.get(p, []):
            try:
                fn = cl["mainsnak"]["datavalue"]["value"]
                if fn and re.search(r"\.(jpe?g|png|svg)$", fn, re.I):
                    return best, p, fn
            except Exception:
                continue
    return best, None, None

def commons_image(filename, width=300):
    fn = urllib.parse.quote(filename.replace(" ", "_"))
    url = f"https://commons.wikimedia.org/wiki/Special:FilePath/{fn}?width={width}"
    return http_get(url, 20), url

# ---------- 图标服务 / favicon ----------
NEWS_HOSTS = ("10jqka", "stcn", "html5.qq", "news.cn", "sohu", "sina.", "163.com",
              "eastmoney", "qq.com/page", "datadeep.tech", "mpg.de/7098253")
DOMAIN_OVERRIDE = {  # source 是新闻链接时的官网纠正
    "c_origin": "originqc.com", "c_ciqtek": "ciqtek.com", "c_turingq": "turingq.com",
    "c_boseq": "boseq.com", "c_planqc": "planqc.eu", "c_iqm": "iqm.com",
    "i_blackrock": "blackrock.com",
}

def domain_of(n):
    if n["id"] in DOMAIN_OVERRIDE:
        return DOMAIN_OVERRIDE[n["id"]]
    u = (n.get("source") or "").strip()
    if u.startswith("http"):
        host = urllib.parse.urlparse(u).netloc.lower()
        host = re.sub(r"^www\.", "", host)
        if any(b in host for b in NEWS_HOSTS):
            return ""
        return host
    return ""

# icon.horse 对无图标域名也返回 200 + 占位图，预取占位图字节做比对
_HORSE_PLACEHOLDER = None
def icon_horse(domain):
    global _HORSE_PLACEHOLDER
    if _HORSE_PLACEHOLDER is None:
        try:
            _HORSE_PLACEHOLDER = http_get("https://icon.horse/icon/nonexistent-domain-zzz9zzz.invalid", 10)
        except Exception:
            _HORSE_PLACEHOLDER = b""
    data = http_get(f"https://icon.horse/icon/{domain}", 12)
    if _HORSE_PLACEHOLDER and data == _HORSE_PLACEHOLDER:
        raise ValueError("placeholder")
    return data

def unavatar(domain):
    return http_get(f"https://unavatar.io/{domain}?fallback=false", 12)

def favicon_im(domain):
    return http_get(f"https://favicon.im/{domain}?larger=true", 12)

# ---------- 搜狗图片（必应当前被代理污染，改用搜狗）----------
SOGOU_UA = {"User-Agent": UA["User-Agent"], "Referer": "https://pic.sogou.com/"}

def sogou_items(query, want=14):
    url = "https://pic.sogou.com/pics?" + urllib.parse.urlencode({"query": query, "mode": 1})
    req = urllib.request.Request(url, headers=SOGOU_UA)
    h = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")
    pairs = re.findall(r'"title":"(.*?)".*?"picUrl":"(.*?)"', h)
    out = []
    for t, p in pairs:
        t = t.replace('\\"', '"')
        p = p.replace("\\u002F", "/").replace("\\/", "/")
        out.append({"title": t, "pic": p})
        if len(out) >= want:
            break
    return out

def sogou_person(n):
    """人物：标题须包含姓名（中文全名 / 英文姓氏）才采纳。"""
    zh, en = n["name"], (n.get("name_en") or "").strip()
    last = (re.findall(r"[A-Za-z]+", en) or [""])[-1].lower()
    queries = []
    if zh and re.search(r"[一-鿿]", zh):
        queries.append(f"{zh} 教授" if n["type"] != "student" else f"{zh} 量子")
        if en:
            queries.append(f"{en} physicist")
    elif en:
        queries += [f"{en} quantum physicist", f'"{en}" professor']
    for q in queries:
        try:
            items = sogou_items(q)
        except Exception:
            continue
        for it in items:
            tl = it["title"].lower()
            hit = (zh and zh in it["title"]) or (en and en.lower() in tl) or (last and last in tl)
            if not hit:
                continue
            try:
                return http_get(it["pic"], 15), it["pic"]
            except Exception:
                continue
    return None, None

def sogou_logo(n):
    """机构兜底：名称 + logo，标题需含品牌词或中文名。"""
    en = (n.get("name_en") or "").strip()
    brand = (re.findall(r"[a-z0-9]+", en.lower()) or [""])[0]
    zh = n["name"]
    for q in [f"{zh} logo", f"{en} logo" if en else None]:
        if not q:
            continue
        try:
            items = sogou_items(q, 10)
        except Exception:
            continue
        for it in items:
            tl = it["title"].lower()
            if (zh and zh in it["title"]) or (brand and brand in tl) or "logo" in tl:
                try:
                    return http_get(it["pic"], 15), it["pic"]
                except Exception:
                    continue
    return None, None


TRUSTED_RE = re.compile(
    r"(wikipedia\.org|wikimedia\.org|\.edu\b|\.ac\.|\.edu\.|researchgate\.net|ieee\.org|"
    r"nature\.com|science\.org|aps\.org|arxiv\.org|linkedin\.com|crunchbase\.com|"
    r"quantum|qubit|phys\.org)", re.I)

def bing_person(n):
    """人物必应搜索：en-US 市场 + 安全搜索 + 来源域名白名单 + 姓氏需出现在标题/URL。"""
    en = (n.get("name_en") or "").strip()
    if not en:
        return None, None
    last = re.findall(r"[A-Za-z]+", en)
    last = last[-1].lower() if last else ""
    q = f'"{en}" quantum'
    url = "https://www.bing.com/images/search?" + urllib.parse.urlencode(
        {"q": q, "mkt": "en-US", "safeSearch": "strict", "form": "HDRSC2"})
    try:
        h = http_get(url, 20).decode("utf-8", "replace")
    except Exception:
        return None, None
    for m in re.findall(r'm="(\{&quot;.*?&quot;\})"', h):
        try:
            d = json.loads(htmllib.unescape(m))
        except Exception:
            continue
        murl, title, turl = d.get("murl", ""), (d.get("t") or "").lower(), d.get("turl")
        if not turl:
            continue
        host = urllib.parse.urlparse(murl).netloc.lower()
        if not TRUSTED_RE.search(host):
            continue
        if last and last not in title and last not in murl.lower():
            continue
        turl = re.sub(r"https://ts\d\.mm\.bing\.net/", "https://tse1-mm.cn.bing.net/", turl)
        try:
            return http_get(turl, 15), murl
        except Exception:
            continue
    return None, None

def bing_logo(n, dom):
    """机构必应兜底：en-US + 官网域名/品牌词加权。"""
    en = (n.get("name_en") or "").strip() or n["name"]
    brand = (re.findall(r"[a-z0-9]+", en.lower()) or [""])[0]
    q = f"{en} logo"
    url = "https://www.bing.com/images/search?" + urllib.parse.urlencode(
        {"q": q, "mkt": "en-US", "safeSearch": "strict", "form": "HDRSC2"})
    try:
        h = http_get(url, 20).decode("utf-8", "replace")
    except Exception:
        return None, None
    items = []
    for m in re.findall(r'm="(\{&quot;.*?&quot;\})"', h):
        try:
            d = json.loads(htmllib.unescape(m))
        except Exception:
            continue
        if not d.get("turl"):
            continue
        host = urllib.parse.urlparse(d.get("murl", "")).netloc.lower()
        title = (d.get("t") or "").lower()
        s = 0
        if dom and dom in host: s += 100
        if brand and brand in host: s += 40
        if "logo" in title: s += 10
        if brand and brand in title: s += 8
        if s < 40:  # 官网或品牌域名之外的一律不要，宁缺毋滥
            continue
        d["turl"] = re.sub(r"https://ts\d\.mm\.bing\.net/", "https://tse1-mm.cn.bing.net/", d["turl"])
        items.append((s, d))
    items.sort(key=lambda x: -x[0])
    for _, d in items[:5]:
        try:
            return http_get(d["turl"], 15), d.get("murl", "")
        except Exception:
            continue
    return None, None

# ---------- 主流程 ----------
def main():
    photos = {}
    report = {}
    nodes = DATA["nodes"]
    only = set(sys.argv[1:]) if len(sys.argv) > 1 else None
    if only:  # 只重抓指定 id，保留其余
        photos = json.loads(PHOTOS_FILE.read_text(encoding="utf-8"))
        report = json.loads(REPORT_FILE.read_text(encoding="utf-8")) if REPORT_FILE.exists() else {}
        nodes = [n for n in nodes if n["id"] in only]
    stats = {"wikidata": 0, "clearbit": 0, "favicon": 0, "bing": 0, "avatar": 0}
    for i, n in enumerate(nodes):
        nid = n["id"]
        is_person = n["type"] in ("scholar", "student", "exec")
        got, src = None, None
        # 1) Wikidata（网络可达时）
        if WIKIDATA_ON:
            try:
                wd = wikidata_search(n)
                if wd and wd[1]:
                    data, url = commons_image(wd[2])
                    got = to_dataURL(data)
                    src = {"via": f"wikidata-{wd[1]}", "qid": wd[0], "url": url}
                elif wd:
                    src = {"via": "wikidata-qid-only", "qid": wd[0]}
            except Exception:
                pass
        # 2) 机构: icon.horse → unavatar → favicon.im → Bing logo
        dom = domain_of(n)
        if not got and not is_person and dom:
            for fn, via in ((unavatar, "unavatar"), (icon_horse, "icon-horse"), (favicon_im, "favicon-im")):
                try:
                    got = to_dataURL(fn(dom))
                    src = {"via": via, "url": dom}
                    break
                except Exception:
                    continue
        if not got and not is_person:
            data, murl = bing_logo(n, dom)
            if data:
                try:
                    got = to_dataURL(data)
                    src = {"via": "bing", "url": murl}
                except Exception:
                    got = None
        if not got and not is_person:
            data, murl = sogou_logo(n)
            if data:
                try:
                    got = to_dataURL(data)
                    src = {"via": "sogou-logo", "url": murl}
                except Exception:
                    got = None
        # 3) 人物: 搜狗（标题姓名匹配）
        if not got and is_person:
            data, murl = sogou_person(n)
            if data:
                try:
                    got = to_dataURL(data)
                    src = {"via": "sogou", "url": murl}
                except Exception:
                    got = None
        # 4) 头像兜底
        if not got:
            got = avatar(n)
            src = {**(src or {}), "via": (src or {}).get("via", "") + "+avatar" if src else "avatar"}
        photos[nid] = got
        report[nid] = src
        print(f"  {nid}: {src.get('via') if src else '?'}", flush=True)
        stats[src["via"].split("+")[-1] if src["via"].endswith("avatar") else src["via"].split("-")[0]] = \
            stats.get(src["via"].split("+")[-1] if src["via"].endswith("avatar") else src["via"].split("-")[0], 0) + 1
        if (i + 1) % 20 == 0 or i == len(nodes) - 1:
            print(f"[{i+1}/{len(nodes)}] {stats}", flush=True)
            PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
            REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
        time.sleep(0.2)
    PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print("DONE", stats)

if __name__ == "__main__":
    main()
