# -*- coding: utf-8 -*-
"""backfill_wikidata_v2.py — 把 v2（中文标签通道 + P31 结构化消歧）结果写入 quantum_network.json

来源分级沿用 SCHEMA §6.2 的三值枚举，不新增取值：
  manual      — 人工逐条核实（原 11 个旗舰节点）
  auto-label  — 命中词条是节点主名（name / name_en）→ 走 rdfs:label 通道
  auto-alias  — 命中词条是节点别名（aliases）→ 走 skos:altLabel 通道

安全措施（与 v1 一致，另加）：
  - 写盘前备份 quantum_network.pre-wikidata2.json
  - 同 QID 映射到多个节点 → 拒绝回填
  - 与已有 QID 冲突 → 拒绝回填
  - 不覆盖已有 wikidata 值

用法：python backfill_wikidata_v2.py [--dry-run]
"""
import json
import re
import shutil
import sys
import collections
from pathlib import Path

BASE = Path(r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph')
P = BASE / 'quantum_network.json'
BAK = BASE / 'quantum_network.pre-wikidata2.json'
ACCEPT = BASE / '_v2_accept.json'
CANDS = BASE / '_v2_candidates.json'

CJK = re.compile(r'[\u4e00-\u9fff]')


def clean(s):
    s = (s or '').strip()
    s = re.sub(r'[（(][^）)]*[）)]', ' ', s)
    s = re.sub(r'[（(].*$', ' ', s)
    return re.sub(r'\s+', ' ', s).strip(' ·-—/、，,')


def main():
    dry = '--dry-run' in sys.argv
    data = json.loads(P.read_text(encoding='utf-8'))
    nodes = {n['id']: n for n in data['nodes']}
    accept = json.loads(ACCEPT.read_text(encoding='utf-8'))       # {nid: qid}
    cands = json.loads(CANDS.read_text(encoding='utf-8'))         # {nid: [cand,...]}

    plan, skipped = [], []
    for nid, qid in sorted(accept.items()):
        n = nodes.get(nid)
        if n is None:
            skipped.append('%s: 节点不存在' % nid)
            continue
        if n.get('wikidata'):
            skipped.append('%s: 已有 wikidata=%s，不覆盖' % (nid, n['wikidata']))
            continue
        # 取该候选的命中词条，判定 label / alias
        c = next((x for x in cands.get(nid, []) if x['qid'] == qid), None)
        if c is None:
            skipped.append('%s: 候选明细缺失' % nid)
            continue
        prim = {clean(n.get('name', '')), clean(n.get('name_en', ''))}
        terms = [t for t in c.get('terms', []) if t]
        is_label = any(t in prim for t in terms)
        src = 'auto-label' if is_label else 'auto-alias'
        lang = 'zh' if any(CJK.search(t) for t in terms) else 'en'
        plan.append({'nid': nid, 'name': n['name'], 'type': n['type'],
                     'qid': qid, 'src': src, 'lang': lang,
                     'terms': terms, 'lbl': c.get('lbl', ''),
                     'desc': c.get('desc', ''), 'p31': c.get('p31lbl', [])})

    byqid = collections.defaultdict(list)
    for x in plan:
        byqid[x['qid']].append(x['nid'])
    conflicts = {q: ids for q, ids in byqid.items() if len(ids) > 1}
    existing = {n['wikidata']: n['id'] for n in data['nodes'] if n.get('wikidata')}
    clash = {q: (ids, existing[q]) for q, ids in byqid.items() if q in existing}

    print('=== v2 回填计划 ===')
    print('  候选来源分布:', dict(collections.Counter(x['src'] for x in plan)))
    print('  命中语言分布:', dict(collections.Counter(x['lang'] for x in plan)))
    print('  合计: %d' % len(plan))
    if skipped:
        print('  跳过 %d 条:' % len(skipped))
        for s in skipped:
            print('    -', s)
    if conflicts:
        print('\n!! 内部冲突（同 QID 多节点）%d 组，不予回填：' % len(conflicts))
        for q, ids in conflicts.items():
            print('   %s: %s' % (q, ', '.join('%s(%s)' % (i, nodes[i]['name']) for i in ids)))
    if clash:
        print('\n!! 与已有 QID 冲突 %d 组，不予回填：' % len(clash))
        for q, (ids, old) in clash.items():
            print('   %s: 新 %s vs 已有 %s' % (q, ids, old))

    bad = set(conflicts) | set(clash)
    if bad:
        plan = [x for x in plan if x['qid'] not in bad]
        print('\n剔除冲突后实际回填: %d' % len(plan))

    print('\n--- 明细 ---')
    for x in plan:
        print('  %-16s %-9s %-18s -> %-11s %-10s %-12s %s' % (
            x['nid'], x['type'], x['name'][:16], x['qid'], x['src'],
            x['lang'], (x['lbl'] or '')[:30]))

    if dry:
        print('\n[DRY RUN] 未写盘')
        return

    shutil.copy2(P, BAK)
    print('\n已备份 -> %s' % BAK.name)
    for x in plan:
        n = nodes[x['nid']]
        n['wikidata'] = x['qid']
        n['wikidata_src'] = x['src']
    P.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')

    cov = sum(1 for n in data['nodes'] if n.get('wikidata'))
    c = collections.Counter(n.get('wikidata_src') for n in data['nodes'] if n.get('wikidata'))
    print('已写入。覆盖 %d/%d (%.1f%%)' % (cov, len(data['nodes']), cov * 100.0 / len(data['nodes'])))
    print('来源分布:', dict(c))


if __name__ == '__main__':
    main()
