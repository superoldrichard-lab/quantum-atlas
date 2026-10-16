# -*- coding: utf-8 -*-
"""backfill_wikidata_v3.py — 把 v2/v3/v4/v5 的终裁结果一次性写入 quantum_network.json

终裁输入（优先级从高到低）：
  _final_accept.json  人工逐条裁定后的权威清单 {nid: qid}
  _v4_accept.json     v4 通道（中文全文召回修正版）自动接受
  _v5_accept.json     v5 通道（ORCID 人物消歧）自动接受
  _final_drop.json    显式排除名单 [nid, ...]（覆盖上面所有来源）

来源分级（SCHEMA §6.2 三值枚举，不新增取值）：
  manual      — 人工逐条核实（含本轮人工裁定的争议条目）
  auto-label  — 命中词条是节点主名（name / name_en）
  auto-alias  — 命中词条是节点别名（aliases）或别名通道

安全措施：
  - 写盘前备份 quantum_network.pre-wikidata3.json
  - 同 QID 映射到多个节点 → 拒绝回填
  - 与已有 QID 冲突 → 拒绝回填
  - 不覆盖已有 wikidata 值

用法：python backfill_wikidata_v3.py [--dry-run]
"""
import collections
import json
import re
import shutil
import sys
from pathlib import Path

BASE = Path(r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph')
P = BASE / 'quantum_network.json'
BAK = BASE / 'quantum_network.pre-wikidata3.json'

CJK = re.compile(r'[\u4e00-\u9fff]')


def clean(s):
    s = (s or '').strip()
    s = re.sub(r'[（(][^）)]*[）)]', ' ', s)
    s = re.sub(r'[（(].*$', ' ', s)
    return re.sub(r'\s+', ' ', s).strip(' ·-—/、，,')


def load(name, default):
    p = BASE / name
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding='utf-8'))


def main():
    dry = '--dry-run' in sys.argv
    data = json.loads(P.read_text(encoding='utf-8'))
    nodes = {n['id']: n for n in data['nodes']}

    final = load('_final_accept.json', {})
    final_v6 = load('_final_accept_v6.json', {})
    drops = set(load('_final_drop.json', []))
    manual = set(load('_final_manual.json', []))
    if isinstance(manual, dict):
        manual = set(manual)
    override = load('_final_src_override.json', {})

    merged = dict(final)                     # 终裁清单为唯一权威来源
    merged.update(final_v6)
    src_tag = {k: 'final' for k in merged}

    # 命中词条明细（用于 label / alias 判定）
    cands = {}
    for fn in ('_v2_candidates.json', '_v3_candidates.json', '_v4_candidates.json'):
        for nid, lst in (load(fn, {}) or {}).items():
            for c in lst:
                cands.setdefault(nid, {}).setdefault(c['qid'], set()).update(c.get('terms') or [])
    orc = load('_v5_raw.json', {})
    for nid, q2t in (orc.get('o1') or {}).items():
        for qid, ts in q2t.items():
            cands.setdefault(nid, {}).setdefault(qid, set()).update(ts or [])

    plan, skipped = [], []
    for nid in sorted(merged):
        qid = merged[nid]
        n = nodes.get(nid)
        if n is None:
            skipped.append('%s: 节点不存在' % nid)
            continue
        if nid in drops:
            skipped.append('%s: 显式排除' % nid)
            continue
        if n.get('wikidata'):
            skipped.append('%s: 已有 wikidata=%s，不覆盖' % (nid, n['wikidata']))
            continue
        terms = sorted(cands.get(nid, {}).get(qid, set()))
        prim = {clean(n.get('name', '')), clean(n.get('name_en', ''))}
        is_label = any(t in prim for t in terms)
        src = 'manual' if nid in manual else ('auto-label' if is_label else 'auto-alias')
        src = override.get(nid, src)
        lang = 'zh' if any(CJK.search(t) for t in terms) else 'en'
        plan.append({'nid': nid, 'name': n['name'], 'type': n['type'], 'qid': qid,
                     'src': src, 'lang': lang, 'terms': terms,
                     'via': src_tag.get(nid, '')})

    byqid = collections.defaultdict(list)
    for x in plan:
        byqid[x['qid']].append(x['nid'])
    conflicts = {q: ids for q, ids in byqid.items() if len(ids) > 1}
    existing = {n['wikidata']: n['id'] for n in data['nodes'] if n.get('wikidata')}
    clash = {q: (ids, existing[q]) for q, ids in byqid.items() if q in existing}

    print('=== 终裁回填计划 ===')
    print('  输入：final %d / v4 %d / v5 %d' % (
        len(final), len(load('_v4_accept.json', {}) or {}), len(load('_v5_accept.json', {}) or {})))
    print('  来源分布:', dict(collections.Counter(x['src'] for x in plan)))
    print('  命中语言:', dict(collections.Counter(x['lang'] for x in plan)))
    print('  通道分布:', dict(collections.Counter(x['via'] for x in plan)))
    print('  合计: %d' % len(plan))
    if skipped:
        print('  跳过 %d 条:' % len(skipped))
        for s in skipped:
            print('    -', s)
    if conflicts:
        print('\n!! 内部冲突（同 QID 多节点）%d 组，剔除：' % len(conflicts))
        for q, ids in conflicts.items():
            print('   %s: %s' % (q, ', '.join('%s(%s)' % (i, nodes[i]['name']) for i in ids)))
    if clash:
        print('\n!! 与已有 QID 冲突 %d 组，剔除：' % len(clash))
        for q, (ids, old) in clash.items():
            print('   %s: 新 %s vs 已有 %s' % (q, ids, old))

    bad = set(conflicts) | set(clash)
    if bad:
        plan = [x for x in plan if x['qid'] not in bad]
        print('\n剔除冲突后实际回填: %d' % len(plan))

    print('\n--- 明细 ---')
    for x in plan:
        print('  %-16s %-9s %-18s -> %-11s %-11s %-3s %s' % (
            x['nid'], x['type'], x['name'][:16], x['qid'], x['src'], x['lang'],
            ','.join(x['terms'])[:40]))

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
