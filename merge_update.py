# -*- coding: utf-8 -*-
"""合并上传的 v7.0 边核实轮数据到基础库 quantum_network.json：
- 节点源：Downloads/nods.csv（363 节点，全富字段 + aliases/verified/verif_note）
- 边源：  Downloads/data.json edges（486 边：r→rel, nt→note, u→unc, v→verif, st→start, en→end）
- 保留原 meta 体系，版本升级为 v8；旧库备份 quantum_network.v7.281.json
"""
import csv, json, shutil
from pathlib import Path

BASE = Path(__file__).parent
CSV_IN = Path(r"C:/Users/Boss/Downloads/nods.csv")
JSON_IN = Path(r"C:/Users/Boss/Downloads/data.json")
OUT = BASE / "quantum_network.json"

def clean(v):
    return (v or "").strip()

def maybe(d, k, v):
    """空值不落字段，保持"缺失留空"约定"""
    if v not in ("", None, [], {}):
        d[k] = v

# ---- 节点 ----
rows = list(csv.DictReader(open(CSV_IN, encoding="utf-8-sig")))
nodes = []
for r in rows:
    n = {"id": r["id"], "type": r["type"], "name": r["name"]}
    maybe(n, "name_en", clean(r.get("name_en")))
    maybe(n, "weight", int(r["weight"])) if clean(r.get("weight")) else None
    maybe(n, "country", clean(r.get("country")))
    maybe(n, "region", clean(r.get("region")))
    for f in ("intro", "affiliation", "dept", "title", "lab", "founded", "hq",
              "funding", "business", "source", "note", "wikidata", "verified", "verif_note"):
        maybe(n, f, clean(r.get(f)))
    for f in ("fields", "aliases", "uncertain"):
        v = clean(r.get(f))
        if v:
            maybe(n, f, [x.strip() for x in v.split(";") if x.strip()])
    nodes.append(n)

# ---- 边 ----
dj = json.loads(JSON_IN.read_text(encoding="utf-8"))
nodemap = {n["id"]: n for n in nodes}
links = []
for e in dj["edges"]:
    s, t, r = e["s"], e["t"], e["r"]
    # 方向纠正：任职类边须 人 -> 机构（上传数据中 5 条大学->学者为方向笔误）
    if r in ("任职",) and nodemap[s]["type"] == "university" and nodemap[t]["type"] in ("scholar", "exec", "student"):
        s, t = t, s
    l = {"s": s, "t": t, "rel": r, "w": int(e.get("w") or 1)}
    maybe(l, "note", clean(e.get("nt")))
    maybe(l, "unc", e.get("u") if e.get("u") else None)
    maybe(l, "verif", e.get("v") or None)
    maybe(l, "start", clean(e.get("st")))
    maybe(l, "end", clean(e.get("en")))
    links.append(l)

# ---- meta（沿用旧体系 + 升级） ----
old = json.loads(OUT.read_text(encoding="utf-8"))
meta = dict(old.get("meta", {}))
meta["version"] = "v8（2026-10-08 合并边核实轮：363 节点/486 边，verified 三分级——外部核实 44%/一致核验 44%/未核验 12%）"
meta["compiled"] = "2026-10-08"
meta["verification_rubric"] = {
    "说明": "核实三级制（节点 verified 与边 verif 字段）",
    "是": "外部核实——有官方/权威来源直接支撑",
    "一致": "一致核验——多来源交叉一致但无单一权威来源",
    "否": "未核验——存疑或未能找到可靠来源，边以虚线呈现",
    "边补充字段": "start/end 为关系起止年份（任职起止/投资年份等）",
}

# ---- 完整性自检 ----
ids = {n["id"] for n in nodes}
assert len(ids) == len(nodes) == 363, f"节点数异常 {len(nodes)}"
orphan = [l for l in links if l["s"] not in ids or l["t"] not in ids]
assert not orphan, f"悬空边 {len(orphan)} 条"
types = {n["type"] for n in nodes}
rels = {l["rel"] for l in links}
assert types <= {"university", "scholar", "student", "exec", "company", "investor"}, types
assert rels <= {"师承", "联合研究", "学校孵化", "任职", "任职/创办", "投资/持股"}, rels
from collections import Counter
print("nodes:", len(nodes), Counter(n["type"] for n in nodes))
print("links:", len(links), Counter(l["rel"] for l in links))
print("verif:", Counter(l.get("verif", "") for l in links))
print("verified:", Counter(n.get("verified", "") for n in nodes))

BAK = BASE / "quantum_network.v7.281.json"
if not BAK.exists():  # 幂等：仅首次执行时备份
    shutil.copy(OUT, BAK)
OUT.write_text(json.dumps({"meta": meta, "nodes": nodes, "links": links},
                          ensure_ascii=False, indent=1), encoding="utf-8")
print("written:", OUT, OUT.stat().st_size, "bytes (backup: quantum_network.v7.281.json)")
