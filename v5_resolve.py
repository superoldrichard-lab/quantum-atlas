# -*- coding: utf-8 -*-
"""v5_resolve.py — 用「图谱自带的双语机构字典」重算 v5 人物消歧

v5 首轮的漏洞：ORCID 返回的机构名是英文（Weizmann Institute of Science），
而节点 affiliation 常是中文（魏茨曼科学研究所）→ 机构一致性比对全部落空。

本脚本不改动任何在线查询，只把 _v5_raw.json 的结果按双语字典重算一遍：
  图谱内 362 个节点自带 name(zh) + name_en，本身就是一本机构中英对照表。
  把 affiliation 的中文片段扩展到英文键，再与 ORCID 机构名比对。
"""
import collections
import json
import os
import re

import align_wikidata_v3 as V

V.META_CACHE = '_v5_meta.json'      # 复用 v5 已抓取的结构化字段缓存

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

# ---------- 双语机构字典 ----------
DATA = json.load(open('quantum_network.json', encoding='utf-8'))
GROUPS = collections.defaultdict(set)


def _keys(*texts):
    ks = set()
    for t in texts:
        for part in re.split(r'[，,、；;/\s()（）]+', str(t or '')):
            for k in V.key_forms(part):
                if len(k) >= 3:
                    ks.add(k)
    return ks


for _n in DATA['nodes']:
    g = _keys(_n.get('name'), _n.get('name_en')) | _keys(*(_n.get('aliases') or []))
    for k in g:
        GROUPS[k] |= g


def expand(text):
    base = _keys(text)
    out = set(base)
    for k in base:
        out |= GROUPS.get(k, set())
    return {x for x in out if len(x) >= 3}


def overlap(a, b):
    for x in a:
        for y in b:
            if x == y:
                return True
            if len(x) >= 4 and len(y) >= 4 and (x in y or y in x):
                return True
    return False


def main():
    raw = json.load(open('_v5_raw.json', encoding='utf-8'))
    o1, o2 = raw.get('o1', {}), raw.get('o2', {})
    meta = json.load(open('_v5_meta.json', encoding='utf-8')) if os.path.exists('_v5_meta.json') else {}
    lit = {}
    dec = set(json.load(open('_final_accept.json', encoding='utf-8')))
    pend = [n for n in V.PEND if n['id'] not in dec and n['type'] in V.HUMAN_TYPES]

    # ORCID -> QID
    allc = set()
    for v in o2.values():
        allc |= set(v)
    orc2q = {}
    if allc:
        vals = ' '.join('"%s"' % x for x in sorted(allc))
        try:
            for b in V.sparql('SELECT ?item ?orc WHERE { VALUES ?orc { %s } ?item wdt:P496 ?orc }' % vals,
                              V.MIRROR, tag='o2q')['results']['bindings']:
                orc2q[b['orc']['value']] = b['item']['value'].rsplit('/', 1)[-1]
        except Exception as e:
            print('[warn] ORCID→QID 失败 %s' % str(e)[:70])
    print('ORCID→QID 命中 %d / %d' % (len(orc2q), len(allc)))

    qids = set()
    for v in o1.values():
        qids |= set(v)
    qids |= set(orc2q.values())
    need = [q for q in qids if q not in meta]
    if need:
        meta.update(V.fetch_meta(need, tag_extra='v5r'))

    accept, review = {}, {}
    for n in pend:
        nid = n['id']
        nk = expand(' '.join(str(n.get(k, '')) for k in ('affiliation', 'note', 'lab', 'dept', 'org')))
        rows = []

        def affil_ok2(m):
            return overlap(nk, _keys(*(list(m.get('p108lbl', [])) + list(m.get('p69lbl', []))
                                      + list(m.get('p1416lbl', [])))))

        # O1
        for qid, terms in o1.get(nid, {}).items():
            m = meta.get(qid, {})
            if 'Q5' not in m.get('p31', []) or V.country_conflict(n, m):
                continue
            rows.append({'qid': qid, 'via': 'O1', 'terms': terms, 'orcid': '',
                         'insts': [], 'score': 0,
                         'lbl': m.get('lbl', ''), 'desc': (m.get('desc') or '')[:110],
                         'p106': m.get('p106lbl', []), 'p108': m.get('p108lbl', []),
                         'p69': m.get('p69lbl', []), 'p31lbl': m.get('p31lbl', []),
                         'affil_ok': affil_ok2(m)})
        # O2
        for oid, info in o2.get(nid, {}).items():
            qid = orc2q.get(oid)
            if not qid:
                continue
            m = meta.get(qid, {})
            if 'Q5' not in m.get('p31', []) or V.country_conflict(n, m):
                continue
            sc = 0
            for i in info.get('insts') or []:
                if overlap(nk, _keys(i)):
                    sc += 1
            tgt = next((r for r in rows if r['qid'] == qid), None)
            if tgt:
                tgt['via'] += '+O2'
                tgt['orcid'], tgt['insts'], tgt['score'] = oid, info.get('insts', []), sc
            else:
                rows.append({'qid': qid, 'via': 'O2', 'terms': [], 'orcid': oid,
                             'insts': info.get('insts', []), 'score': sc,
                             'lbl': m.get('lbl', ''), 'desc': (m.get('desc') or '')[:110],
                             'p106': m.get('p106lbl', []), 'p108': m.get('p108lbl', []),
                             'p69': m.get('p69lbl', []), 'p31lbl': m.get('p31lbl', []),
                             'affil_ok': affil_ok2(m)})
        for r in rows:
            r['ok'] = r['affil_ok'] or r['score'] > 0
        if not rows:
            review[nid] = ('O通道无人物候选', [])
            continue
        good = [r for r in rows if r['ok']]
        if len(good) == 1:
            accept[nid] = good[0]
        elif len(good) > 1:
            review[nid] = ('待裁(%d)' % len(good), sorted(good, key=lambda x: (-x['score'], -len(x['p108'])))[:6])
        else:
            review[nid] = ('单候选无机构证据(%d)' % len(rows),
                           sorted(rows, key=lambda x: -len(x['p108']))[:6])

    print('\n=== v5r 结果 ===')
    print('可回填 %d / 待人工 %d' % (len(accept), len(review)))
    print('\n--- 可回填 ---')
    for nid, r in sorted(accept.items()):
        n = V.BY_ID[nid]
        print('  %-16s %-9s %-16s -> %-11s %-24s via=%-6s score=%d %s' % (
            nid, n['type'], n['name'][:15], r['qid'], (r['lbl'] or '')[:22], r['via'],
            r['score'], 'WEAK' if r.get('weak') else ''))
        if r['p108'] or r['p69']:
            print('        p108=%s | p69=%s' % (str(r['p108'])[:64], str(r['p69'])[:52]))
        if r['insts']:
            print('        ORCID机构=%s' % str(r['insts'])[:90])
    print('\n--- 待人工 ---')
    for nid, (why, lst) in sorted(review.items()):
        n = V.BY_ID[nid]
        print('  %-16s %-9s %-16s %s' % (nid, n['type'], n['name'][:15], why))
        for c in (lst or [])[:4]:
            print('        %-11s %-24s via=%-6s score=%d p108=%s' % (
                c['qid'], (c['lbl'] or '')[:22], c['via'], c['score'], str(c['p108'])[:48]))

    json.dump({k: v['qid'] for k, v in accept.items()},
              open('_v5_accept.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({nid: {'why': w, 'cands': [{kk: c[kk] for kk in
                                          ('qid', 'lbl', 'desc', 'via', 'score', 'orcid',
                                           'insts', 'p106', 'p108', 'p69', 'terms')}
                                         for c in (lst or [])[:6]]}
               for nid, (w, lst) in review.items()},
              open('_v5_review.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n接受 → _v5_accept.json；复核 → _v5_review.json')


if __name__ == '__main__':
    main()
