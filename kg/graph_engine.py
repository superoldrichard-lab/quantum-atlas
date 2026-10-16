# -*- coding: utf-8 -*-
"""
量子图谱 · 图引擎加载器
把 quantum_network.json（+ 可选推断层）加载为 networkx MultiDiGraph 属性图，
供 grandcypher 执行 Cypher 查询、infer.py 执行规则推理使用。

节点属性：id/type/name/name_en/country/region/weight/intro/... （fields 列表转 '|' 拼接字符串）
边属性：  rel（关系类型）/w（强度 1-3）/unc（不确定）/note/inferred（推断层标记）
"""
import json
from pathlib import Path

import networkx as nx

BASE = Path(__file__).resolve().parent.parent          # 项目根目录（kg/ 的上一级）
DATA_FILE = BASE / "quantum_network.json"
INFERRED_FILE = BASE / "quantum_network.inferred.json"


def load_data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def load_graph(use_inferred=False):
    """返回 (G, data)。use_inferred=True 时叠加推断层边与节点注释。"""
    data = load_data()
    G = nx.MultiDiGraph()
    for n in data["nodes"]:
        attrs = {k: v for k, v in n.items() if not isinstance(v, (list, dict))}
        attrs["fields"] = "|".join(n.get("fields") or [])
        G.add_node(n["id"], **attrs)
    for l in data["links"]:
        G.add_edge(l["s"], l["t"], rel=l["rel"], w=l.get("w", 1),
                   unc=bool(l.get("unc")), note=l.get("note", ""), inferred=False)
    if use_inferred and INFERRED_FILE.exists():
        inf = json.loads(INFERRED_FILE.read_text(encoding="utf-8"))
        for l in inf.get("inferred_links", []):
            G.add_edge(l["s"], l["t"], rel=l["rel"], w=l.get("w", 1),
                       unc=False, note=l.get("note", ""), inferred=True)
        for nid, anno in inf.get("node_annotations", {}).items():
            if nid in G:
                for k, v in anno.items():
                    if not isinstance(v, (list, dict)):
                        G.nodes[nid][k] = v
        # 给所有节点补齐推断层属性的默认值，避免 Cypher 查询空属性报错
        for nid in G.nodes():
            nd = G.nodes[nid]
            nd.setdefault("school", "")
            nd.setdefault("schools_all", "")
            nd.setdefault("bridge", 0)
            nd.setdefault("bridge_countries", "")
            nd.setdefault("centrality_deg", 0.0)
            nd.setdefault("centrality_btw", 0.0)
    return G, data


def neighbors_of(G, nid):
    """一阶邻居 id 集合（含出入两个方向）。"""
    out = set(G.successors(nid)) if nid in G else set()
    inn = set(G.predecessors(nid)) if nid in G else set()
    return out | inn
