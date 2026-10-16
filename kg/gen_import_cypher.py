# -*- coding: utf-8 -*-
"""
量子图谱 · Neo4j 导入脚本生成器
生成自包含的 kg/import.cypher：全部 MERGE 语句，无外部文件依赖，
在 Neo4j Browser / cypher-shell 中整段粘贴执行即可建库。

结构：
  1) 约束（id 唯一）
  2) 基础层节点（6 类标签）与关系（6 类，中文类型名，含 w/unc/note 属性）
  3) 推断层边（同门/共同投资，inferred:true，与基础层严格区分）
  4) Cypher 版推理规则（R1/R2/R3 可在库内直接重算）

用法：python kg/gen_import_cypher.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_engine import BASE, INFERRED_FILE, load_data   # noqa: E402

OUT = BASE / "kg" / "import.cypher"
LABEL = {"university": "University", "scholar": "Scholar", "student": "Student",
         "exec": "Exec", "company": "Company", "investor": "Investor"}


def esc(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    s = str(v).replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ").replace("\r", " ")
    return f"'{s}'"


def props(d, skip=()):
    items = [f"{k}: {esc(v)}" for k, v in d.items()
             if k not in skip and not isinstance(v, (list, dict)) and v not in (None, "")]
    return "{" + ", ".join(items) + "}" if items else ""


def main():
    data = load_data()
    L = ["// 量子图谱 · Neo4j 导入脚本（由 kg/gen_import_cypher.py 生成，请勿手改）",
         "// 用法：Neo4j Browser 中整段执行；或 cypher-shell -f import.cypher",
         "",
         "// ---- 0) 约束 ----",
         "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE;",
         ""]
    L.append("// ---- 1) 基础层节点 ----")
    for n in data["nodes"]:
        attrs = dict(n)
        attrs["fields"] = "|".join(n.get("fields") or [])
        L.append(f"MERGE (n:Entity:{LABEL[n['type']]} {{id: {esc(n['id'])}}}) SET n += {props(attrs, skip=('id',))};")
    L.append("")
    L.append("// ---- 2) 基础层关系（人工录入，含溯源）----")
    for l in data["links"]:
        p = props({"w": l.get("w", 1), "unc": bool(l.get("unc")), "note": l.get("note", ""),
                   "inferred": False})
        L.append(f"MATCH (a:Entity {{id: {esc(l['s'])}}}), (b:Entity {{id: {esc(l['t'])}}}) "
                 f"MERGE (a)-[r:`{l['rel']}`]->(b) SET r += {p};")
    if INFERRED_FILE.exists():
        inf = json.loads(INFERRED_FILE.read_text(encoding="utf-8"))
        L.append("")
        L.append("// ---- 3) 推断层关系（机器推导，inferred:true）----")
        for l in inf.get("inferred_links", []):
            p = props({"w": l.get("w", 1), "note": l.get("note", ""), "inferred": True,
                       "rule": l.get("rule", "")})
            L.append(f"MATCH (a:Entity {{id: {esc(l['s'])}}}), (b:Entity {{id: {esc(l['t'])}}}) "
                     f"MERGE (a)-[r:`{l['rel']}`]->(b) SET r += {p};")
        L.append("")
        L.append("// ---- 3b) 推断层节点注释（学派/桥梁/中心性）----")
        for nid, anno in inf.get("node_annotations", {}).items():
            if anno:
                L.append(f"MATCH (n:Entity {{id: {esc(nid)}}}) SET n += {props(anno)};")
    L += ["",
          "// ---- 4) Cypher 版推理规则（导入后可在库内重算，与 Python infer.py 等价）----",
          "// R1 同门推断：",
          "// MATCH (m)-[:`师承`]->(a), (m)-[:`师承`]->(b) WHERE a.id < b.id",
          "// MERGE (a)-[r:`同门`]->(b) SET r.inferred=true, r.w=1, r.note='共同导师：'+m.name;",
          "// R2 共同投资：",
          "// MATCH (i1)-[:`投资/持股`]->(c:Company)<-[:`投资/持股`]-(i2) WHERE i1.id < i2.id",
          "// MERGE (i1)-[r:`共同投资`]->(i2) SET r.inferred=true, r.w=1, r.note='共同被投企业：'+c.name;",
          "// R3 学派传播（简化版；完整版含多重归属，建议用 Python infer.py）：",
          "// MATCH (r:Scholar)-[:`师承`]->(s) WITH r, count(s) AS c WHERE c>=2 AND r.weight>=9",
          "// MATCH (r)-[:`师承`*0..4]->(x) SET x.school = r.name + '学派';",
          ""]
    OUT.write_text("\n".join(L), encoding="utf-8")
    print("written:", OUT, f"({OUT.stat().st_size//1024} KB, {len(L)} lines)")


if __name__ == "__main__":
    main()
