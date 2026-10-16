# -*- coding: utf-8 -*-
"""align_wikidata_v4.py — 修正 v3 的两个召回缺陷，对剩余 149 条做增量再召回

v3 的两处缺陷（本轮实证）：
  1. 发现层显式剔除中文词条（"中文全文索引噪声太大"），把中文交给 v2 的「精确标签」通道。
     但 v2 是字面精确匹配 —— Wikidata 的中文标签常是完整法定名，
     例如 本源量子 的标签是「合肥本源量子计算科技有限责任公司」→ 精确匹配必失手。
  2. 发现层把 10 个词条用 OR 拼成一条查询并 LIMIT 200。
     实测 `'a' OR ('b' AND 'c')` 时，多词 AND 项会召回大量论文标题噪声并吃满 LIMIT，
     真正命中的实体被挤出结果集。

v4 通道：
  A 发现层：镜像 bif:contains 逐词条单查（不 OR 拼接），中文词条一并召回
  B 匹配层：规范化键相等（西文）+ 规范化包含（CJK≥4字 / 西文≥10字符）
  C 消歧层：完全沿用 v3 的 P31 / P17 / 机构一致 三重门

用法：
  python align_wikidata_v4.py --probe   只做发现+匹配，落 _v4_candidates.json
  python align_wikidata_v4.py           决策，落 _v4_accept.json / _v4_review.json
"""
import collections
import json
import os
import sys
import time

import align_wikidata_v3 as V

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

DISC_CACHE = '_v4_disc.json'
LANGS = '("en","zh","zh-hans","zh-cn","zh-hant")'


def disc_one(term, pred, cache, limit=60):
    key = '%s\x1f%s' % (pred, term)
    if key in cache:
        return cache[key]
    expr = "'%s'" % term.replace("'", '').replace('\\', '')
    q = '''SELECT DISTINCT ?item ?l WHERE {
  ?item %s ?l .
  FILTER(bif:contains(?l, "%s") && lang(?l) IN %s)
} LIMIT %d''' % (pred, expr.replace('"', '\\"'), LANGS, limit)
    out = []
    try:
        res = V.sparql(q, V.MIRROR, tag='disc')
        for b in res['results']['bindings']:
            qid = b['item']['value'].rsplit('/', 1)[-1]
            if qid.startswith('Q') and qid[1:].isdigit():
                out.append([qid, b['l']['value']])
    except Exception as e:
        print('    [warn] %s / %s : %s' % (pred, term[:24], str(e)[:70]), flush=True)
        out = None
    cache[key] = out
    if len(cache) % 25 == 0:
        json.dump(cache, open(DISC_CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    time.sleep(0.1)
    return out


def norm_ok(t, ent_labels_norm):
    """规范化相等 或 包含（CJK≥4 / 拉丁≥10）"""
    tk = {k for k in V.key_forms(t) if len(k) >= V.min_key_len(k)}
    if not tk:
        return False
    if tk & ent_labels_norm:
        return True
    nt = V.norm(t)
    need = 4 if V.CJK_RE.search(t) else 10
    if len(nt) >= need:
        for hay in ent_labels_norm:
            if nt in hay:
                return True
    return False


def main():
    mode = 'dry'
    if '--probe' in sys.argv:
        mode = 'probe'

    # 已决定不需要再召回的节点：v2/v3 accept ∪ 人工终裁
    decided = set()
    for f in ('_v2_accept.json', '_v3_accept.json', '_final_accept.json'):
        if os.path.exists(f):
            decided |= set(json.load(open(f, encoding='utf-8')))
    pend = [n for n in V.PEND if n['id'] not in decided]
    print('待再召回节点 %d（已决定 %d，总待配 %d）' % (len(pend), len(decided), len(V.PEND)), flush=True)

    te = collections.defaultdict(set)
    for n in pend:
        for t in V.node_terms(n):
            if len(t) >= 2:
                te[t].add(n['id'])
    terms = sorted(te)
    print('唯一词条 %d（中文 %d / 西文 %d）' % (
        len(terms), sum(1 for t in terms if V.CJK_RE.search(t)),
        sum(1 for t in terms if not V.CJK_RE.search(t))), flush=True)

    cache = json.load(open(DISC_CACHE, encoding='utf-8')) if os.path.exists(DISC_CACHE) else {}
    for pred in ('rdfs:label', 'skos:altLabel'):
        for i, t in enumerate(terms):
            disc_one(t, pred, cache)
            if (i + 1) % 25 == 0:
                print('  %s %d/%d' % (pred.split(':')[-1], i + 1, len(terms)), flush=True)
        json.dump(cache, open(DISC_CACHE, 'w', encoding='utf-8'), ensure_ascii=False)
    print('发现层完成，缓存 %d 条查询' % len(cache), flush=True)

    # 词条 -> 命中实体
    term_hits = {}
    qids = set()
    for t in terms:
        s = set()
        for pred in ('rdfs:label', 'skos:altLabel'):
            for qid, lit in (cache.get('%s\x1f%s' % (pred, t)) or []):
                s.add(qid)
        term_hits[t] = s
        qids |= s
    print('全文召回候选实体 %d 个' % len(qids), flush=True)

    # 取字面量（含中文标签）——v3 的 fetch_literals 已含 zh/zh-hans/zh-hant
    lit = V.fetch_literals(sorted(qids)) if qids else {}

    # 匹配层
    v4c = collections.defaultdict(dict)
    for t, s in term_hits.items():
        if not s:
            continue
        for q in s:
            m = lit.get(q)
            if not m:
                continue
            hay = set()
            for x in m['labels'] + m['alts']:
                nx = V.norm(x)
                if len(nx) >= 3:
                    hay.add(nx)
                hay |= {k for k in V.key_forms(x) if len(k) >= 3}
            if not hay:
                continue
            if norm_ok(t, hay):
                for nid in te[t]:
                    v4c[nid].setdefault(q, []).append(t)
    print('规范化匹配：%d 条节点有候选' % len(v4c), flush=True)

    # 结构化字段
    allq = set(qids)
    for d in v4c.values():
        allq |= set(d)
    meta = V.fetch_meta(allq, tag_extra='v4')
    org_ids = set()
    for q in allq:
        m = meta.get(q, {})
        org_ids |= set(m.get('p108', [])) | set(m.get('p69', [])) | set(m.get('p1416', []))
    org_zh = V.fetch_org_zh(org_ids) if org_ids else {}
    print('机构中文名 %d 个' % len(org_zh), flush=True)

    # 组装候选明细 + v3 判定
    merged = {}
    for n in pend:
        out = []
        for q, ts in v4c.get(n['id'], {}).items():
            m = meta.get(q, {})
            lm = lit.get(q, {})
            out.append({
                'qid': q, 'terms': sorted(set(ts)), 'src_v': 'v4',
                'lbl': m.get('lbl') or (lm.get('labels') or [''])[0],
                'labels': lm.get('labels', []), 'alts': lm.get('alts', []),
                'desc': (m.get('desc') or lm.get('desc') or '')[:130],
                'p31lbl': m.get('p31lbl', []), 'p17': m.get('p17', []),
                'p106': m.get('p106lbl', []), 'p101': m.get('p101lbl', []),
                'p108': m.get('p108lbl', []), 'p69': m.get('p69lbl', []),
                'p1416': m.get('p1416lbl', []),
                'type_ok': V.type_ok(n['type'], m),
                'country_ok': bool(V.country_qids(n.get('country', '')) & set(m.get('p17', []))),
                'country_conflict': V.country_conflict(n, m),
                'occ_ok': V.occ_ok(n['type'], m),
                'affil_ok': V.affil_ok(n, m, org_zh),
                'desc_domain': any(k in (m.get('desc', '') or '').lower() for k in V.DESC_DOMAIN),
            })
        merged[n['id']] = out

    json.dump(merged, open('_v4_candidates.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('候选明细 → _v4_candidates.json', flush=True)
    if mode == 'probe':
        return

    # 决策（与 v3 同规则）
    TL = {'university': '高校', 'scholar': '学者', 'student': '学生', 'exec': '高管',
          'company': '公司', 'investor': '投资', 'gov': '政府'}
    accept, review = {}, {}
    for n in pend:
        nid = n['id']
        lst = merged[nid]
        if not lst:
            review[nid] = ('无候选', [])
            continue
        kept = [c for c in lst if not c['country_conflict']]
        if not kept:
            review[nid] = ('候选全被国别否决', lst[:3])
            continue
        t_ok = [c for c in kept if c['type_ok']]
        if not t_ok:
            review[nid] = ('无类型自洽候选', kept[:3])
            continue
        if n['type'] in V.HUMAN_TYPES:
            cjk_name = bool(V.CJK_RE.search(n.get('name', '')))
            if cjk_name:
                pool = [c for c in t_ok if c['affil_ok']]
                why_gate = '人名(中文名)需机构一致'
            else:
                pool = [c for c in t_ok if c['affil_ok'] or c['occ_ok'] or c['desc_domain']]
                why_gate = '人名(西文名)需领域证据'
            if not pool:
                review[nid] = (why_gate, t_ok[:4])
                continue
        else:
            pool = t_ok
        if len(pool) == 1:
            accept[nid] = (pool[0]['qid'], 'unique')
            continue
        c_ok = [c for c in pool if c['country_ok']]
        if len(c_ok) == 1:
            accept[nid] = (c_ok[0]['qid'], 'country')
            continue
        a_ok = [c for c in pool if c['affil_ok']]
        if len(a_ok) == 1:
            accept[nid] = (a_ok[0]['qid'], 'affiliation')
            continue
        o_ok = [c for c in pool if c['occ_ok']]
        if len(o_ok) == 1:
            accept[nid] = (o_ok[0]['qid'], 'occupation')
            continue
        review[nid] = ('多候选未收敛(%d)' % len(pool), pool[:6])

    print()
    print('=== v4 决策结果 ===')
    print('可回填 %d / 待人工 %d' % (len(accept), len(review)))
    for k, v in collections.Counter(v[1] for v in accept.values()).most_common():
        print('   规则 %-14s %d' % (k, v))
    print('\n--- 可回填 ---')
    for nid, (q, why) in sorted(accept.items()):
        n = V.BY_ID[nid]
        c = next((x for x in merged[nid] if x['qid'] == q), {})
        print('  %-16s %-4s %-16s -> %-11s %-36s %s' % (
            nid, TL.get(n['type'], n['type']), n['name'][:15], q,
            (c.get('lbl') or '')[:34], why))
    print('\n--- 待人工（前 50）---')
    for nid, (why, lst) in sorted(review.items())[:50]:
        n = V.BY_ID[nid]
        print('  %-16s %-4s %-16s %s' % (nid, TL.get(n['type'], n['type']), n['name'][:15], why))

    json.dump({k: v[0] for k, v in accept.items()}, open('_v4_accept.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump({nid: {'why': w, 'cands': [{kk: c[kk] for kk in ('qid', 'lbl', 'desc', 'p31lbl', 'terms')}
                                         for c in (lst or [])[:3]]}
               for nid, (w, lst) in review.items()},
              open('_v4_review.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n接受清单 → _v4_accept.json；复核清单 → _v4_review.json')


if __name__ == '__main__':
    main()
