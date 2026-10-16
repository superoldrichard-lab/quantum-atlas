# -*- coding: utf-8 -*-
"""align_wikidata_v5.py — 人物专用通道：ORCID 双通道消歧

人物是所有类型里最难的一类：同名撞车严重（"John Morton" 有主教、艺术家、板球手…），
而 v3/v4 只能靠 P108/P69 机构字符串比对，一旦 Wikidata 没写机构就无解。

v5 用两条高精度通道：
  O1 标签精确 + P496(ORCID) 存在   —— 「同名里凡是带 ORCID 的，必定是研究者」
     对学者/学生/高管这类人物，直接把政客/歌手/运动员全部剔除。
  O2 ORCID 检索（pub.orcid.org，本机实测可达）—— 按 given/family name 搜人，
     再用其 institution-name 与节点 affiliation 比对锁定唯一，最后 ORCID → P496 → QID 反查。

输出 _v5_accept.json / _v5_review.json，供人工终裁合并。
"""
import collections
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import align_wikidata_v3 as V

V.META_CACHE = '_v5_meta.json'      # 与 v4 并行时隔离结构化字段缓存，避免同文件并发写

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

ORCID_API = 'https://pub.orcid.org/v3.0/expanded-search/'
UA_O = {'Accept': 'application/json', 'User-Agent': 'QuantumKG-Align/5.0 (academic)'}


def orcid_search(given, family, rows=20):
    q = 'given-names:"%s" AND family-name:"%s"' % (given, family)
    url = ORCID_API + '?' + urllib.parse.urlencode({'q': q, 'rows': rows})
    req = urllib.request.Request(url, headers=UA_O)
    for a in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {'expanded-result': [], 'num-found': 0}
            time.sleep(1.5 * (a + 1))
        except Exception:
            time.sleep(1.5 * (a + 1))
    return None


def split_name(n):
    """节点西文名 -> (given, family)。失败返回 None"""
    s = (n.get('name_en') or '').strip()
    if not s or V.CJK_RE.search(s):
        return None
    s = re.sub(r'[（(].*$', '', s).strip()
    s = re.sub(r'\b(jr|sr|iii|ii)\b\.?', '', s, flags=re.I).strip(' ,.')
    parts = [p for p in re.split(r'\s+', s) if p]
    if len(parts) < 2:
        return None
    return parts[0], parts[-1]


def aff_keys(n):
    aff = ' '.join(str(n.get(k, '')) for k in ('affiliation', 'note', 'lab', 'dept', 'org'))
    ks = set()
    for part in re.split(r'[，,、；;/\s]+', aff):
        for k in V.key_forms(part):
            if len(k) >= 3:
                ks.add(k)
    return ks


def org_match(node_keys, insts):
    hit = 0
    for i in insts or []:
        ik = V.key_forms(i)
        for a in node_keys:
            for b in ik:
                if not b:
                    continue
                if a == b and len(a) >= 3:
                    hit += 1
                    break
                if len(a) >= 4 and len(b) >= 4 and (a in b or b in a):
                    hit += 1
                    break
    return hit


def main():
    dec = set()
    for f in ('_final_accept.json',):
        if os.path.exists(f):
            dec |= set(json.load(open(f, encoding='utf-8')))
    pend = [n for n in V.PEND if n['id'] not in dec and n['type'] in V.HUMAN_TYPES]
    print('v5 人物节点 %d 个' % len(pend), flush=True)

    # ---------- O1：标签全文 + P496 ----------
    o1 = collections.defaultdict(dict)          # nid -> {qid: [terms]}
    for n in pend:
        terms = [t for t in V.node_terms(n) if not V.CJK_RE.search(t) and len(t) >= 5]
        for t in terms[:4]:
            q = '''SELECT DISTINCT ?item ?lbl WHERE {
  ?item rdfs:label ?lbl .
  FILTER(bif:contains(?lbl, "'%s'") && lang(?lbl) = "en")
  ?item wdt:P496 ?orc .
} LIMIT 20''' % t.replace("'", '')
            try:
                res = V.sparql(q, V.MIRROR, tag='o1')
            except Exception as e:
                print('   [warn] o1 %s: %s' % (t[:20], str(e)[:70]), flush=True)
                continue
            for b in res['results']['bindings']:
                qid = b['item']['value'].rsplit('/', 1)[-1]
                if re.fullmatch(r'Q\d+', qid):
                    o1[n['id']].setdefault(qid, []).append(t)
            time.sleep(0.1)
        print('  O1 %-16s -> %d 候选' % (n['id'], len(o1[n['id']])), flush=True)

    # ---------- O2：ORCID 检索 ----------
    o2 = collections.defaultdict(dict)          # nid -> {orcid: {insts, score, given, family}}
    for n in pend:
        sf = split_name(n)
        if not sf:
            continue
        given, family = sf
        d = orcid_search(given, family)
        if d is None:
            print('  [warn] O2 %s 检索失败' % n['id'], flush=True)
            continue
        res = d.get('expanded-result') or []
        nk = aff_keys(n)
        for r in res:
            oid = r.get('orcid-id')
            insts = r.get('institution-name') or []
            score = org_match(nk, insts) if nk else 0
            o2[n['id']][oid] = {'insts': insts, 'score': score,
                                'given': r.get('given-names'), 'family': r.get('family-names')}
        print('  O2 %-16s %-22s %d 个 ORCID（机构命中 %d）' % (
            n['id'], '%s %s' % (given, family), len(res),
            sum(1 for v in o2[n['id']].values() if v['score'])), flush=True)
        time.sleep(0.25)

    json.dump({'o1': {k: v for k, v in o1.items()}, 'o2': {k: v for k, v in o2.items()}},
              open('_v5_raw.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('原始结果 → _v5_raw.json', flush=True)

    # ORCID -> QID
    allc = set()
    for v in o2.values():
        allc |= set(v)
    orc2q = {}
    if allc:
        vals = ' '.join('"%s"' % x for x in sorted(allc))
        q = 'SELECT ?item ?orc WHERE { VALUES ?orc { %s } ?item wdt:P496 ?orc }' % vals
        try:
            for b in V.sparql(q, V.MIRROR, tag='orc2q')['results']['bindings']:
                orc2q[b['orc']['value']] = b['item']['value'].rsplit('/', 1)[-1]
        except Exception as e:
            print('   [warn] ORCID→QID 批量失败: %s' % str(e)[:80], flush=True)
    print('ORCID→QID 命中 %d / %d' % (len(orc2q), len(allc)), flush=True)

    # ---------- 汇总 ----------
    cand = {}       # nid -> {qid: {..evidence..}}
    for n in pend:
        rec = {}
        for qid, ts in o1[n['id']].items():
            rec.setdefault(qid, {'qid': qid, 'via': set(), 'terms': set(),
                                 'orcid': '', 'insts': [], 'score': 0})
            rec[qid]['via'].add('O1')
            rec[qid]['terms'] |= set(ts)
        for oid, meta in o2[n['id']].items():
            qid = orc2q.get(oid)
            if not qid:
                continue
            r = rec.setdefault(qid, {'qid': qid, 'via': set(), 'terms': set(),
                                     'orcid': '', 'insts': [], 'score': 0})
            r['via'].add('O2')
            r['orcid'] = oid
            r['insts'] = meta['insts']
            r['score'] = meta['score']
        cand[n['id']] = rec

    qids = set()
    for rec in cand.values():
        qids |= set(rec)
    lit = V.fetch_literals(sorted(qids)) if qids else {}
    meta = V.fetch_meta(sorted(qids), tag_extra='v5') if qids else {}
    org_ids = set()
    for q in qids:
        m = meta.get(q, {})
        org_ids |= set(m.get('p108', [])) | set(m.get('p69', [])) | set(m.get('p1416', []))
    org_zh = V.fetch_org_zh(org_ids) if org_ids else {}

    accept, review = {}, {}
    print()
    print('=== v5 结果 ===')
    for n in pend:
        rec = cand[n['id']]
        rows = []
        for qid, r in rec.items():
            m = meta.get(qid, {})
            lm = lit.get(qid, {})
            if 'Q5' not in m.get('p31', []):
                continue                      # 只要人物
            if V.country_conflict(n, m):
                continue
            ok = V.affil_ok(n, m, org_zh) or r['score'] > 0 or (r['via'] == {'O1'} and len(rec) == 1)
            rows.append({
                'qid': qid, 'via': '+'.join(sorted(r['via'])), 'terms': sorted(r['terms']),
                'orcid': r['orcid'], 'insts': r['insts'][:4], 'score': r['score'],
                'lbl': m.get('lbl') or (lm.get('labels') or [''])[0],
                'desc': (m.get('desc') or lm.get('desc') or '')[:120],
                'p31lbl': m.get('p31lbl', []),
                'p106': m.get('p106lbl', []), 'p108': m.get('p108lbl', []),
                'p69': m.get('p69lbl', []), 'p1416': m.get('p1416lbl', []),
                'affil_ok': V.affil_ok(n, m, org_zh),
                'occ_ok': V.occ_ok(n['type'], m),
                'ok': ok,
            })
        if not rows:
            review[n['id']] = ('O通道无人物候选', [])
            continue
        good = [x for x in rows if x['ok']]
        if len(good) == 1:
            accept[n['id']] = good[0]
        else:
            review[n['id']] = ('待裁(%d)' % len(good or rows), (good or rows)[:5])

    print('可回填 %d / 待人工 %d' % (len(accept), len(review)))
    print('\n--- 可回填 ---')
    for nid, r in sorted(accept.items()):
        n = V.BY_ID[nid]
        print('  %-16s %-9s %-16s -> %-11s %-26s via=%-5s score=%d' % (
            nid, n['type'], n['name'][:15], r['qid'], (r['lbl'] or '')[:24], r['via'], r['score']))
        if r['p108'] or r['p69']:
            print('        p108=%s | p69=%s' % (str(r['p108'])[:70], str(r['p69'])[:60]))
    print('\n--- 待人工 ---')
    for nid, (why, lst) in sorted(review.items()):
        n = V.BY_ID[nid]
        print('  %-16s %-9s %-16s %s' % (nid, n['type'], n['name'][:15], why))
        for c in (lst or [])[:4]:
            print('        %-11s %-26s via=%-5s p108=%s' % (
                c['qid'], (c['lbl'] or '')[:24], c['via'], str(c['p108'])[:56]))

    json.dump({k: v['qid'] for k, v in accept.items()},
              open('_v5_accept.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump({nid: {'why': w, 'cands': [{kk: c[kk] for kk in
                                          ('qid', 'lbl', 'desc', 'via', 'score', 'orcid',
                                           'insts', 'p106', 'p108', 'p69', 'terms')}
                                         for c in (lst or [])[:5]]}
               for nid, (w, lst) in review.items()},
              open('_v5_review.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n接受 → _v5_accept.json；复核 → _v5_review.json')


if __name__ == '__main__':
    main()
