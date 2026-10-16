# -*- coding: utf-8 -*-
"""人物照片重抓（提升准确率）：国外学者优先用中文译名搜索（必应国内版对中文查询结果质量高），
候选按标题相关性过滤；中文无结果回退 英文名+机构关键词。覆盖 photos.json 中 scholar/student/exec 条目。"""
import json, time, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from fetch_photos import fetch_image
from refetch_logos import bing_items

BASE = Path(__file__).parent
DATA = json.loads((BASE / "quantum_network.json").read_text(encoding="utf-8"))
PHOTOS_FILE = BASE / "photos.json"

def queries_of(n):
    zh_name, en = n["name"], (n.get("name_en") or "").strip()
    qs = []
    if n.get("country") != "中国" and en:
        qs.append(zh_name)                       # 中文译名（如 安东·蔡林格）
        aff = (n.get("affiliation") or "").split("（")[0].split("(")[0].strip()
        qs.append(f"{en} {aff}" if aff else en)  # 英文名+机构
        qs.append(f"{en} quantum physicist")
    else:
        qs.append(zh_name)
        if en:
            qs.append(en)
    return qs

def main():
    photos = json.loads(PHOTOS_FILE.read_text(encoding="utf-8"))
    people = [n for n in DATA["nodes"] if n["type"] in ("scholar", "student", "exec")]
    print(f"people: {len(people)}", flush=True)
    ok, fail = 0, []
    for i, n in enumerate(people):
        nid = n["id"]
        zh_key = n["name"].replace("·", "")
        en_key = (n.get("name_en") or "").lower()
        en_last = en_key.split()[-1] if en_key else ""
        got = None
        for q in queries_of(n):
            try:
                items = bing_items(q, want=8)
            except Exception:
                continue
            def score(it):
                t = it["title"].lower()
                s = 0
                if zh_key and zh_key.lower() in t: s += 50
                if en_last and en_last in t: s += 40
                if en_key and en_key in t: s += 20
                return -s
            items.sort(key=score)
            for it in items[:4]:
                try:
                    got = fetch_image(it["turl"])
                    break
                except Exception:
                    continue
            if got:
                break
            time.sleep(0.15)
        if got:
            photos[nid] = got; ok += 1
        else:
            fail.append({"id": nid, "name": n["name"]})
        if (i + 1) % 20 == 0 or i == len(people) - 1:
            print(f"[{i+1}/{len(people)}] ok={ok} fail={len(fail)}", flush=True)
            PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
        time.sleep(0.12)
    PHOTOS_FILE.write_text(json.dumps(photos, ensure_ascii=False), encoding="utf-8")
    (BASE / "people_failed.json").write_text(json.dumps(fail, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"DONE ok={ok} fail={len(fail)}")

if __name__ == "__main__":
    main()
