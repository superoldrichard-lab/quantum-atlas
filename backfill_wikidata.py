# -*- coding: utf-8 -*-
"""backfill_wikidata.py — 把批量对齐结果写入 quantum_network.json（含来源标注）

来源分级（wikidata_src）：
  manual       — 人工逐条核实（原有 11 个旗舰节点）
  auto-label   — SPARQL rdfs:label 精确匹配 + 描述类型词过滤（阶段1，已过 P31 反向校验）
  auto-alias   — skos:altLabel / 节点自带 aliases 二次匹配（阶段2）

安全措施：
  - 写盘前备份为 quantum_network.pre-wikidata.json
  - 拒绝重复 QID 映射到不同节点（同 QID 多节点 = 误配信号）
  - 不覆盖已有 wikidata 值，只补空字段
用法：python backfill_wikidata.py [--dry-run]
"""
import json, shutil, sys
from collections import defaultdict
from pathlib import Path

BASE = Path(r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph')
P = BASE / 'quantum_network.json'
BAK = BASE / 'quantum_network.pre-wikidata.json'
H1 = BASE / 'quantum_network_wikidata_hits.json'
H2 = BASE / '_alias_probe.json'


def main():
    dry = '--dry-run' in sys.argv
    data = json.loads(P.read_text(encoding='utf-8'))
    nodes = {n['id']: n for n in data['nodes']}

    ph1 = json.loads(H1.read_text(encoding='utf-8'))            # [{id,type,name,name_en,qid,desc}]
    ph2 = json.loads(H2.read_text(encoding='utf-8'))['saved']   # [[id,qid,desc]]

    plan = []       # (node, qid, src)
    skipped = []
    for h in ph1:
        n = nodes.get(h['id'])
        if n is None:
            skipped.append(f'阶段1 {h["id"]}: 节点不存在'); continue
        if n.get('wikidata'):
            skipped.append(f'阶段1 {h["id"]}: 已有 wikidata={n["wikidata"]}，不覆盖'); continue
        plan.append((n, h['qid'], 'auto-label'))
    for nid, qid, _desc in ph2:
        n = nodes.get(nid)
        if n is None:
            skipped.append(f'阶段2 {nid}: 节点不存在'); continue
        if n.get('wikidata'):
            skipped.append(f'阶段2 {nid}: 已有 wikidata={n["wikidata"]}，不覆盖'); continue
        if any(x[0] is n for x in plan):
            skipped.append(f'阶段2 {nid}: 已被阶段1命中，去重'); continue
        plan.append((n, qid, 'auto-alias'))

    # 冲突检测：同一 QID 映射到多个节点
    byqid = defaultdict(list)
    for n, qid, src in plan:
        byqid[qid].append(n['id'])
    conflicts = {q: ids for q, ids in byqid.items() if len(ids) > 1}

    # 与已有 11 条比对
    existing = {n['wikidata']: n['id'] for n in data['nodes'] if n.get('wikidata')}
    clash = {q: (ids, existing[q]) for q, ids in byqid.items() if q in existing}

    print(f'=== 回填计划 ===')
    print(f'  阶段1 auto-label: {sum(1 for x in plan if x[2] == "auto-label")}')
    print(f'  阶段2 auto-alias: {sum(1 for x in plan if x[2] == "auto-alias")}')
    print(f'  合计新增:        {len(plan)}')
    print(f'  跳过:            {len(skipped)}')
    for s in skipped:
        print(f'    - {s}')
    print(f'  已有 manual:     {len(existing)}')

    if conflicts:
        print(f'\n!! 内部冲突（同 QID 多节点，{len(conflicts)} 组）——这些将不予回填：')
        for q, ids in conflicts.items():
            names = ', '.join(f'{i}({nodes[i]["name"]})' for i in ids)
            print(f'   {q}: {names}')
    if clash:
        print(f'\n!! 与已有记录冲突，{len(clash)} 组——不予回填：')
        for q, (ids, old) in clash.items():
            print(f'   {q}: 新 {ids} vs 已有 {old}')

    bad = set(conflicts) | set(clash)
    if bad:
        plan = [x for x in plan if x[1] not in bad]
        print(f'\n剔除冲突后实际回填: {len(plan)}')

    if dry:
        print('\n[DRY RUN] 未写盘')
        return

    shutil.copy2(P, BAK)
    print(f'\n已备份 -> {BAK.name}')

    # 原有 11 条标 manual
    for n in data['nodes']:
        if n.get('wikidata'):
            n['wikidata_src'] = 'manual'
    for n, qid, src in plan:
        n['wikidata'] = qid
        n['wikidata_src'] = src

    P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')

    cov = sum(1 for n in data['nodes'] if n.get('wikidata'))
    from collections import Counter
    c = Counter(n.get('wikidata_src') for n in data['nodes'] if n.get('wikidata'))
    print(f'已写入。覆盖 {cov}/{len(data["nodes"])} ({cov*100/len(data["nodes"]):.1f}%)')
    print('来源分布:', dict(c))


if __name__ == '__main__':
    main()
