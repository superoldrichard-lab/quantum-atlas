# -*- coding: utf-8 -*-
"""
量子图谱 · 规则推理层
在人工录入的基础图谱（ground truth）之上，用确定性规则推导隐含知识，
产出独立的推断层文件（不污染主数据文件）：

  R1 同门推断     拥有共同导师的两人 → 推断边 rel="同门"
  R2 共同投资     投了同一家公司的两家机构 → 推断边 rel="共同投资"
  R3 学派谱系传播  旗舰学者（weight>=9 且 >=2 名学生）沿师承边向下传播学派标签 → 节点 school 属性
  R4 中心性计算    degree / betweenness 中心性 → 节点注释（识别结构洞与枢纽）
  R5 跨境桥梁识别  一阶邻居覆盖 >=2 个外国的节点 → bridge 标记（跨国网络节点，投资视角关键）

产出：
  quantum_network.inferred.json   推断边 + 节点注释 + 统计
  inference_report.md             中文推理报告
"""
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import networkx as nx                                    # noqa: E402
from graph_engine import BASE, INFERRED_FILE, load_graph  # noqa: E402

REPORT_FILE = BASE / "inference_report.md"

G, data = load_graph(use_inferred=False)
name = {n["id"]: n["name"] for n in data["nodes"]}
ntype = {n["id"]: n["type"] for n in data["nodes"]}
country = {n["id"]: n.get("country", "") for n in data["nodes"]}
weight = {n["id"]: n.get("weight", 5) for n in data["nodes"]}

inferred_links = []
annotations = defaultdict(dict)

# ---------- R1 同门推断 ----------
mentor_students = defaultdict(set)
for s, t, d in G.edges(data=True):
    if d["rel"] == "师承":
        mentor_students[s].add(t)
r1 = 0
for m, students in mentor_students.items():
    for a, b in combinations(sorted(students), 2):
        inferred_links.append({"s": a, "t": b, "rel": "同门", "w": 1,
                               "note": f"共同导师：{name[m]}", "rule": "R1"})
        r1 += 1

# ---------- R2 共同投资 ----------
company_investors = defaultdict(set)
for s, t, d in G.edges(data=True):
    if d["rel"] == "投资/持股" and ntype.get(t) == "company":
        company_investors[t].add(s)
r2 = 0
for c, invs in company_investors.items():
    for a, b in combinations(sorted(invs), 2):
        inferred_links.append({"s": a, "t": b, "rel": "共同投资", "w": 1,
                               "note": f"共同被投企业：{name[c]}", "rule": "R2"})
        r2 += 1

# ---------- R3 学派谱系传播 ----------
roots = [m for m, stu in mentor_students.items()
         if weight.get(m, 0) >= 9 and len(stu) >= 2 and ntype.get(m) == "scholar"]
school_of = defaultdict(list)
for root in sorted(roots):
    school = f"{name[root]}学派"
    school_of[root].append(school)
    frontier = list(mentor_students[root])
    seen = {root}
    while frontier:
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.add(cur)
        school_of[cur].append(school)
        frontier.extend(mentor_students.get(cur, ()))
for nid, schools in school_of.items():
    uniq = sorted(set(schools))
    annotations[nid]["schools_all"] = "｜".join(uniq)
    # 主学派：学派根本人以自己命名；其余节点取字典序第一个（确定性），便于 Cypher 精确匹配
    annotations[nid]["school"] = f"{name[nid]}学派" if nid in roots else uniq[0]
school_sizes = {f"{name[r]}学派": len([k for k, v in school_of.items() if any(name[r] in s for s in v)])
                for r in roots}

# ---------- R4 中心性 ----------
UG = nx.Graph()
UG.add_nodes_from(G.nodes())
for s, t in G.edges():
    UG.add_edge(s, t)
deg_c = nx.degree_centrality(UG)
btw_c = nx.betweenness_centrality(UG, k=min(80, len(UG)), seed=42)
for nid in G.nodes():
    annotations[nid]["centrality_deg"] = round(deg_c.get(nid, 0), 4)
    annotations[nid]["centrality_btw"] = round(btw_c.get(nid, 0), 4)
top_deg = sorted(deg_c, key=deg_c.get, reverse=True)[:15]
top_btw = sorted(btw_c, key=btw_c.get, reverse=True)[:10]

# ---------- R5 跨境桥梁 ----------
def cset(nid):
    """国家字段支持 '英国/美国' 复合写法，拆成集合再比较。"""
    return {p for p in (country.get(nid, "") or "").split("/") if p}

bridges = []
for nid in G.nodes():
    my_cs = cset(nid)
    foreign = set()
    for nb in set(G.successors(nid)) | set(G.predecessors(nid)):
        foreign |= (cset(nb) - my_cs)
    if len(foreign) >= 2:
        bridges.append((nid, sorted(foreign)))
        annotations[nid]["bridge"] = 1
        annotations[nid]["bridge_countries"] = "｜".join(sorted(foreign))
bridges.sort(key=lambda x: -len(x[1]))

# ---------- 汇总输出 ----------
stats = {"R1_同门推断边": r1, "R2_共同投资推断边": r2,
         "R3_学派数": len(roots), "R5_跨境桥梁节点": len(bridges)}
out = {"inferred_links": inferred_links,
       "node_annotations": {k: dict(v) for k, v in annotations.items()},
       "stats": stats}
INFERRED_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- 中文报告 ----------
L = []
L.append("# 量子图谱 · 规则推理报告\n")
L.append(f"基础图谱：{len(data['nodes'])} 节点 / {len(data['links'])} 边（人工录入，含溯源）")
L.append(f"推断层：{len(inferred_links)} 条推断边 + {len(annotations)} 个节点注释\n")
L.append("> 推断边为机器推导的弱关系（w=1），与人工录入边严格分离存放；"
         "使用时叠加 `--inferred` 或在 Neo4j 中按 `inferred` 属性过滤。\n")
L.append("## R1 同门推断\n")
L.append(f"规则：共享同一导师 → 同门关系。共推断 **{r1}** 条。")
top_mentors = sorted(mentor_students, key=lambda m: -len(mentor_students[m]))[:8]
L.append("\n门生最多的导师：\n")
for m in top_mentors:
    L.append(f"- {name[m]}（{country[m]}）：{len(mentor_students[m])} 名学生 → "
             f"{len(mentor_students[m])*(len(mentor_students[m])-1)//2} 条同门边")
L.append("\n## R2 共同投资\n")
L.append(f"规则：共同出现在一家公司股东名单 → 共同投资关系。共推断 **{r2}** 条。")
multi = [(c, invs) for c, invs in company_investors.items() if len(invs) >= 2]
multi.sort(key=lambda x: -len(x[1]))
L.append("\n多家机构共同持股的公司：\n")
for c, invs in multi[:10]:
    L.append(f"- {name[c]}：{'、'.join(name[i] for i in sorted(invs))}")
L.append("\n## R3 学派谱系传播\n")
L.append(f"以「权重≥9 且至少 2 名在录学生」的旗舰学者为学派根，沿师承边向下传播，共识别 **{len(roots)}** 个学派：\n")
for r in sorted(roots):
    members = [nid for nid, v in school_of.items() if any(name[r] in s for s in v)]
    members_names = "、".join(name[m] for m in sorted(members) if m != r)
    L.append(f"- **{name[r]}学派**（{len(members)} 人）：{members_names}")
L.append("\n## R4 中心性（结构枢纽）\n")
L.append("度中心性 Top 15（连接最广的节点）：\n")
for nid in top_deg:
    L.append(f"- {name[nid]}（{ntype[nid]}/{country[nid]}）：{deg_c[nid]:.3f}")
L.append("\n中介中心性 Top 10（信息/资本流动的桥梁位置）：\n")
for nid in top_btw:
    L.append(f"- {name[nid]}（{ntype[nid]}/{country[nid]}）：{btw_c[nid]:.3f}")
L.append("\n## R5 跨境桥梁节点\n")
L.append(f"一阶邻居覆盖 ≥2 个外国的节点共 **{len(bridges)}** 个"
         "（投资视角：这些节点是跨国技术-资本流动的关键通道）：\n")
for nid, fc in bridges[:20]:
    L.append(f"- {name[nid]}（{country[nid]}）→ 连接：{'、'.join(fc)}")
L.append("\n---\n*推断规则均为确定性结构规则，不含概率模型；所有推断结果可追溯至基础边。*")
REPORT_FILE.write_text("\n".join(L), encoding="utf-8")

print("inferred links:", len(inferred_links), stats)
print("roots:", [name[r] for r in sorted(roots)])
print("report ->", REPORT_FILE.name, "| layer ->", INFERRED_FILE.name)
