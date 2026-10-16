# -*- coding: utf-8 -*-
"""align_wikidata_v6.py — 收尾扫描：对仍未对齐的节点做高上限、包含式发现

v4 的残余漏洞：发现层 LIMIT 60。像 "Temasek" 这种常见词，前 60 条是被
船名/顶级域名/消歧页吃满的，真正的 "Temasek Holdings" 被挤出结果集。

v6 做法：
  - 每个残余节点取 ≤3 个最有辨识度的词条（优先西文长词），逐个单独查询
  - LIMIT 250，且要求「候选实体的规范化标签包含该词条」（包含式匹配，兼顾
    "Temasek Holdings" ⊃ "Temasek"、"合肥本源量子计算科技有限责任公司" ⊃ "本源量子"）
  - 判定沿用 v3：P31 类型门 + P17 国别门 + 人名的西文/中文机构门
  - 仅接受 type_ok 且（唯一 或 国别唯一命中）的候选，其余留复核
"""
import collections
import json
import os
import re
import sys
import time

import align_wikidata_v3 as V

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

LIMIT = 250
LANGS = '("en","zh","zh-hans","zh-cn","zh-hant")'


def pick_terms(n):
    raw = []
    for s in [n.get('name_en'), n.get('name')] + list(n.get('aliases') or []):
        for part in re.split(r'[/；;（）()]', str(s or '')):
            p = V.clean(part)
            if not p:
                continue
            nrm = V.norm(p)
            if V.CJK_RE.search(p):
                if len(nrm) >= 3:
                    raw.append((2, p))
            elif len(nrm) >= 5:
                raw.append((1, p))
    # 西文优先、长词优先
    raw.sort(key=lambda x: (x[0], -len(V.norm(x[1]))))
    out, seen = [], set()
    for _, p in raw:
        k = V.norm(p)
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
        if len(out) >= 3:
            break
    return out


def discover(term, pred):
    q = '''SELECT DISTINCT ?item ?l WHERE {
  ?item %s ?l .
  FILTER(bif:contains(?l, "'%s'") && lang(?l) IN %s)
} LIMIT %d''' % (pred, term.replace("'", ''), LANGS, LIMIT)
    try:
        res = V.sparql(q, V.MIRROR, tag='v6')
    except Exception as e:
        print('    [warn] %s / %s: %s' % (pred, term[:22], str(e)[:60]), flush=True)
        return {}
    out = {}
    for b in res['results']['bindings']:
        qid = b['item']['value'].rsplit('/', 1)[-1]
        if re.fullmatch(r'Q\d+', qid):
            out.setdefault(qid, b['l']['value'])
    return out


def contained(term, label):
    nt = V.norm(term)
    nl = V.norm(label)
    if not nt or not nl:
        return False
    if nt == nl:
        return True
    need = 3 if V.CJK_RE.search(term) else 5
    if len(nt) < need:
        return False
    if nt in nl:
        return True
    # 剥后缀后的实体名也可比
    for k in V.key_forms(label):
        if k and (nt == k or (len(nt) >= need and nt in k)):
            return True
    return False


def main():
    d = json.load(open('quantum_network.json', encoding='utf-8'))
    res = [n for n in d['nodes'] if not n.get('wikidata')]
    print('残余未对齐 %d 个节点' % len(res), flush=True)

    cache = {}
    cpath = '_v6_disc.json'
    if os.path.exists(cpath):
        cache = json.load(open(cpath, encoding='utf-8'))

    hits = {}       # nid -> {qid: [terms]}
    for i, n in enumerate(res):
        terms = pick_terms(n)
        rec = collections.defaultdict(list)
        for t in terms:
            key = 'L\x1f%s' % t
            if key not in cache:
                cache[key] = discover(t, 'rdfs:label')
                time.sleep(0.1)
            cand = cache[key]
            if not cand:
                key2 = 'A\x1f%s' % t
                if key2 not in cache:
                    cache[key2] = discover(t, 'skos:altLabel')
                    time.sleep(0.1)
                cand = cache[key2]
            for qid, lbl in (cand or {}).items():
                if contained(t, lbl):
                    rec[qid].append(t)
        hits[n['id']] = dict(rec)
        print('  %-18s %-10s %d 候选' % (n['id'], n['type'], len(rec)), flush=True)
        if (i + 1) % 20 == 0:
            json.dump(cache, open(cpath, 'w', encoding='utf-8'), ensure_ascii=False)

    json.dump(cache, open(cpath, 'w', encoding='utf-8'), ensure_ascii=False)
    hits = {k: v for k, v in hits.items() if v}
    print('有候选节点 %d 个，候选实体 %d 个' % (len(hits), len({q for v in hits.values() for q in v})), flush=True)

    qids = sorted({q for v in hits.values() for q in v})
    if not qids:
        print('无新增候选')
        return
    lit = V.fetch_literals(qids)
    meta = V.fetch_meta(qids, tag_extra='v6')
    org_ids = set()
    for q in qids:
        m = meta.get(q, {})
        org_ids |= set(m.get('p108', [])) | set(m.get('p69', [])) | set(m.get('p1416', []))
    org_zh = V.fetch_org_zh(org_ids) if org_ids else {}

    accept, review = {}, {}
    for n in res:
        rec = hits.get(n['id'])
        if not rec:
            continue
        rows = []
        for qid, ts in rec.items():
            m = meta.get(qid, {})
            if V.country_conflict(n, m) or not V.type_ok(n['type'], m):
                continue
            rows.append({
                'qid': qid, 'terms': sorted(set(ts)), 'lbl': m.get('lbl') or lit.get(qid, {}).get('labels', [''])[0],
                'desc': (m.get('desc') or '')[:110], 'p31lbl': m.get('p31lbl', []),
                'p17': m.get('p17', []), 'p106': m.get('p106lbl', []),
                'p108': m.get('p108lbl', []), 'p69': m.get('p69lbl', []),
                'country_ok': bool(V.country_qids(n.get('country', '')) & set(m.get('p17', []))),
                'affil_ok': V.affil_ok(n, m, org_zh),
                'occ_ok': V.occ_ok(n['type'], m),
                'desc_domain': any(k in (m.get('desc', '') or '').lower() for k in V.DESC_DOMAIN),
            })
        if not rows:
            continue
        if n['type'] in V.HUMAN_TYPES:
            pool = [r for r in rows if r['affil_ok'] or r['occ_ok'] or r['desc_domain']]
        else:
            pool = rows
        if len(pool) == 1:
            accept[n['id']] = pool[0]
        elif len(pool) > 1:
            c_ok = [r for r in pool if r['country_ok']]
            if len(c_ok) == 1:
                accept[n['id']] = c_ok[0]
            else:
                review[n['id']] = ('多候选(%d)' % len(pool), pool[:6])

    print('\n=== v6 结果 ===')
    print('可回填 %d / 待裁 %d' % (len(accept), len(review)))
    print('\n--- 可回填 ---')
    for nid, r in sorted(accept.items()):
        n = V.BY_ID[nid]
        print('  %-18s %-9s %-16s -> %-11s %-34s p31=%s' % (
            nid, n['type'], n['name'][:15], r['qid'], (r['lbl'] or '')[:32],
            ','.join(r['p31lbl'])[:34]))
    print('\n--- 待裁 ---')
    for nid, (why, lst) in sorted(review.items()):
        n = V.BY_ID[nid]
        print('  %-18s %-9s %-16s %s' % (nid, n['type'], n['name'][:15], why))
        for c in (lst or [])[:4]:
            print('        %-11s %-32s p31=%s' % (c['qid'], (c['lbl'] or '')[:30], ','.join(c['p31lbl'])[:40]))

    json.dump({k: v['qid'] for k, v in accept.items()},
              open('_v6_accept.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({nid: {'why': w, 'cands': [{kk: c[kk] for kk in
                                          ('qid', 'lbl', 'desc', 'p31lbl', 'terms', 'p108')}
                                         for c in (lst or [])[:6]]}
               for nid, (w, lst) in review.items()},
              open('_v6_review.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n接受 → _v6_accept.json；复核 → _v6_review.json')


if __name__ == '__main__':
    main()
