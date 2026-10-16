# verify_hits.py — 对阶段1回填的 QID 做反向实体类型校验
# 思路：取回每个 QID 的 P31（instance of）+ P17（国家）+ 英文标签，
#      与节点自身 type/country 比对；类型明显冲突的标红，人工复核
import json, sys, time, urllib.parse, urllib.request, collections

EP = 'https://query.wikidata.org/sparql'
UA = {'User-Agent': 'QuantumKG-Align/2.0 (academic research graph alignment)',
      'Accept': 'application/sparql-results+json'}
HITS = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network_wikidata_hits.json'

# 期望的 P31 关键词（宽松：只要命中任一即视为自洽）
EXPECT = {
    'university': ['university', 'college', 'institute', 'research institute', 'higher education',
                   'academy', 'school', 'laboratory', 'organisation', 'organization', 'public research'],
    'scholar':    ['human', 'person', 'researcher', 'scientist', 'physicist'],
    'student':    ['human', 'person', 'researcher', 'scientist', 'physicist'],
    'exec':       ['human', 'person', 'researcher', 'scientist', 'physicist', 'businessperson'],
    'company':    ['business', 'company', 'enterprise', 'corporation', 'organization', 'organisation',
                   'manufacturer', 'startup', 'public company', 'privately held'],
    'investor':   ['business', 'company', 'enterprise', 'organization', 'organisation', 'investment',
                   'fund', 'bank', 'public company', 'private equity', 'venture capital'],
    'gov':        ['agency', 'government', 'organization', 'organisation', 'institute', 'research institute'],
}


def esc(s):
    return (s or '').replace('\\', '\\\\').replace('"', '\\"')


def sparql(q, retries=4):
    last = None
    for a in range(retries):
        try:
            data = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode()
            req = urllib.request.Request(EP, data=data, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=90))
        except Exception as e:
            last = e
            time.sleep(1.5 * (a + 1))
    raise last


def main():
    hits = json.load(open(HITS, encoding='utf-8'))
    qids = sorted({h['qid'] for h in hits})
    print(f'校验 {len(hits)} 条命中，涉及 {len(qids)} 个唯一 QID\n')
    meta = {}
    B = 60
    for i in range(0, len(qids), B):
        chunk = qids[i:i + B]
        values = ' '.join('wd:' + q for q in chunk)
        q = f'''SELECT ?item ?lbl ?p31lbl ?p17lbl WHERE {{
  VALUES ?item {{ {values} }}
  OPTIONAL {{ ?item rdfs:label ?lbl . FILTER(lang(?lbl)="en") }}
  OPTIONAL {{ ?item wdt:P31 ?p31 . ?p31 rdfs:label ?p31lbl . FILTER(lang(?p31lbl)="en") }}
  OPTIONAL {{ ?item wdt:P17 ?p17 . ?p17 rdfs:label ?p17lbl . FILTER(lang(?p17lbl)="en") }}
}}'''
        try:
            r = sparql(q)
        except Exception as e:
            print(f'[批 {i//B+1}] 失败 {e}')
            continue
        for b in r['results']['bindings']:
            qid = b['item']['value'].rsplit('/', 1)[-1]
            m = meta.setdefault(qid, {'lbl': '', 'p31': set(), 'p17': set()})
            if b.get('lbl'):
                m['lbl'] = b['lbl']['value']
            if b.get('p31lbl'):
                m['p31'].add(b['p31lbl']['value'])
            if b.get('p17lbl'):
                m['p17'].add(b['p17lbl']['value'])
        print(f'[批 {i//B+1}] 累计 {len(meta)}')
        time.sleep(0.5)

    ok, warn, bad = [], [], []
    for h in hits:
        m = meta.get(h['qid'], {'lbl': '', 'p31': set(), 'p17': set()})
        p31 = ' | '.join(sorted(m['p31']))
        label_ok = (m['lbl'].lower() == (h['name_en'] or '').lower())
        kws = EXPECT.get(h['type'], [])
        type_ok = any(any(k in p.lower() for p in m['p31']) for k in kws) if m['p31'] else False
        rec = dict(h, wd_label=m['lbl'], p31=p31, p17=' | '.join(sorted(m['p17'])),
                   label_match=label_ok, type_ok=type_ok)
        if not m['p31']:
            warn.append(rec)          # Wikidata 未标 instance of，无法判定
        elif type_ok:
            ok.append(rec)
        else:
            bad.append(rec)

    print(f'\n=== 校验结果 ===')
    print(f'类型自洽（P31 命中期望词）：{len(ok)}')
    print(f'类型冲突（需人工复核）：{len(bad)}')
    print(f'Wikidata 未标 P31，无法判定：{len(warn)}')

    if bad:
        print('\n--- 类型冲突明细 ---')
        for r in bad:
            print(f'  {r["id"]:14s} {r["type"]:9s} {r["name"][:20]:22s} {r["qid"]:12s} '
                  f'P31={r["p31"][:60]}')
    if warn:
        print('\n--- 无 P31（无法判定）明细（前 25）---')
        for r in warn[:25]:
            print(f'  {r["id"]:14s} {r["type"]:9s} {r["name"][:20]:22s} {r["qid"]:12s} {r["desc"][:45]}')

    json.dump({'ok': ok, 'bad': bad, 'warn': warn},
              open(r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/_wikidata_verify.json', 'w',
                   encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n明细 -> _wikidata_verify.json')


if __name__ == '__main__':
    main()
