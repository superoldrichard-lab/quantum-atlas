# -*- coding: utf-8 -*-
"""
量子图谱 · Cypher 查询控制台
用法：
  python kg/query.py "MATCH (m)-[r]->(s) WHERE r.rel = \"师承\" RETURN m.name, s.name"
  python kg/query.py --inferred "MATCH ..."     # 叠加推断层（同门/共同投资/学派标签）
  python kg/query.py --demo                      # 运行内置示例查询

注意（grandcypher 语法子集）：
  - 字符串字面量必须用双引号
  - 关系类型请用 WHERE r.rel = "..." 过滤，不写 [r:TYPE]
  - 不支持 OPTIONAL MATCH / 聚合函数；聚合类统计请用 Python（见 infer.py / 报告）
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grandcypher import GrandCypher          # noqa: E402
from graph_engine import load_graph          # noqa: E402

DEMO_QUERIES = [
    ("潘建伟的直接学生（师承边，导师→学生）",
     'MATCH (m)-[r]->(s) WHERE r.rel = "师承" AND m.id = "s_pan" RETURN m.name, s.name'),
    ("国盾量子的股东/投资方",
     'MATCH (i)-[r]->(c) WHERE r.rel = "投资/持股" AND c.id = "c_quantumctek" RETURN i.name, i.type'),
    ("英国学者的师承输出",
     'MATCH (m)-[r]->(s) WHERE r.rel = "师承" AND m.country = "英国" RETURN m.name, s.name'),
    ("权重 >= 9 的旗舰学者",
     'MATCH (n) WHERE n.type = "scholar" AND n.weight >= 9 RETURN n.name, n.country, n.weight'),
]


def run_query(G, q):
    res = GrandCypher(G).run(q)
    if not res:
        return "(无结果)"
    cols = list(res.keys())
    rows = list(zip(*[res[c] for c in cols]))
    widths = [max(len(str(c)), *(len(str(r[i])) for r in rows)) for i, c in enumerate(cols)]
    line = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols))
    sep = "-+-".join("-" * widths[i] for i in range(len(cols)))
    body = "\n".join(" | ".join(str(r[i]).ljust(widths[i]) for i in range(len(cols))) for r in rows)
    return f"{line}\n{sep}\n{body}\n({len(rows)} 行)"


def main():
    args = sys.argv[1:]
    use_inferred = "--inferred" in args
    args = [a for a in args if a != "--inferred"]
    G, _ = load_graph(use_inferred=use_inferred)
    tag = "（含推断层）" if use_inferred else ""
    if not args or args[0] == "--demo":
        for title, q in DEMO_QUERIES:
            print(f"\n### {title}{tag}\n{q}")
            try:
                print(run_query(G, q))
            except Exception as e:                # noqa: BLE001
                print(f"[查询失败] {e}")
        return
    q = args[0]
    try:
        print(run_query(G, q))
    except Exception as e:                        # noqa: BLE001
        print(f"[查询失败] {e}\n提示：字符串用双引号；关系类型用 WHERE r.rel = \"...\" 过滤", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
