# -*- coding: utf-8 -*-
"""Inject quantum_network.json into template.html -> index.html; export nodes/edges CSV."""
import json, csv, pathlib

BASE = pathlib.Path(r"D:/WorkBuddy/Workspace/2026-10-03-quantum-graph")
data = json.loads((BASE / "quantum_network.json").read_text(encoding="utf-8"))

# ---- 照片/Logo 合并（photos.json 为抓取产物，不污染基础数据） ----
photos_file = BASE / "photos.json"
if photos_file.exists():
    photos = json.loads(photos_file.read_text(encoding="utf-8"))
    hit = 0
    for n in data["nodes"]:
        if n["id"] in photos:
            n["img"] = photos[n["id"]]
            hit += 1
    print("photos merged:", hit, "/", len(data["nodes"]))

# ---- 技术路线分派合并（判断层，见 docs/tech-route-report.md；不污染基础事实层） ----
routes_file = BASE / "tech_routes.json"
ROUTES_META = {"groups": [], "route_order": [], "group_of": {}}
if routes_file.exists():
    rt = json.loads(routes_file.read_text(encoding="utf-8"))
    rmap = rt.get("routes", {})
    hit = 0
    for n in data["nodes"]:
        r = rmap.get(n["id"])
        if not r:
            continue
        n["route"] = r["route"]
        n["route_group"] = r["route_group"]
        if r.get("route_note"):
            n["route_note"] = r["route_note"]
        hit += 1
    ROUTES_META = {
        "groups": rt.get("groups", []),
        "route_order": rt.get("route_order", []),
        "group_of": rt.get("group_of", {}),
        "version": rt.get("meta", {}).get("version", ""),
        "total": hit,
    }
    print("tech routes merged:", hit, "/", len(data["nodes"]))
else:
    print("!! tech_routes.json missing — 路线下拉框将为空")

tpl = (BASE / "template.html").read_text(encoding="utf-8")
assert "/*__DATA__*/" in tpl, "placeholder missing"
assert "/*__ROUTES__*/" in tpl, "template.html 缺少 /*__ROUTES__*/ 占位符"
out = (tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
          .replace("/*__ROUTES__*/", json.dumps(ROUTES_META, ensure_ascii=False)))
(BASE / "index.html").write_text(out, encoding="utf-8")

# ---- workbench.html：查询工作台（注入基础数据 + 推断层） ----
tpl2 = (BASE / "template_workbench.html").read_text(encoding="utf-8")
assert "/*__DATA__*/" in tpl2 and "/*__INFERRED__*/" in tpl2, "workbench placeholder missing"
assert "/*__ROUTES__*/" in tpl2, "template_workbench.html 缺少 /*__ROUTES__*/ 占位符"
inferred_file = BASE / "quantum_network.inferred.json"
inferred = json.loads(inferred_file.read_text(encoding="utf-8")) if inferred_file.exists() \
    else {"inferred_links": [], "node_annotations": {}, "stats": {}}
out2 = (tpl2.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False))
            .replace("/*__INFERRED__*/", json.dumps(inferred, ensure_ascii=False))
            .replace("/*__ROUTES__*/", json.dumps(ROUTES_META, ensure_ascii=False)))
(BASE / "workbench.html").write_text(out2, encoding="utf-8")
print("workbench.html:", (BASE / "workbench.html").stat().st_size, "bytes")

ids = {n["id"]: n for n in data["nodes"]}

node_cols = ["id","type","name","name_en","aliases","country","region","fields","weight","intro","affiliation","dept","title",
             "lab","founded","hq","funding","business","route","route_group","route_note",
             "source","note","uncertain","verified","verif_note","wikidata","wikidata_src"]
with open(BASE / "nodes.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(node_cols)
    for n in data["nodes"]:
        w.writerow(["; ".join(n[c]) if isinstance(n.get(c), list) else n.get(c, "") for c in node_cols])

with open(BASE / "edges.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["source_id","source_name","target_id","target_name","relation","strength","note","uncertain","verif","start","end"])
    for l in data["links"]:
        w.writerow([l["s"], ids[l["s"]]["name"], l["t"], ids[l["t"]]["name"],
                    l["rel"], l["w"], l.get("note",""), "是" if l.get("unc") else "",
                    l.get("verif",""), l.get("start",""), l.get("end","")])

print("index.html:", (BASE / "index.html").stat().st_size, "bytes")
print("nodes:", len(data["nodes"]), "links:", len(data["links"]))
print("nodes.csv / edges.csv written")
