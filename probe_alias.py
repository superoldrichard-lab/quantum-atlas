# probe_alias.py — 阶段2探测：用 skos:altLabel（别名）+ 节点自带 aliases 做二次匹配
# 目的：量化"无精确标签匹配"的 134 个节点中，有多少可通过别名通道救回
import json, re, sys, time, urllib.parse, urllib.request, collections

P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
RP = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network_wikidata_review.json'
EP = 'https://query.wikidata.org/sparql'
UA = {'User-Agent': 'QuantumKG-Align/2.0 (academic research graph alignment)',
      'Accept': 'application/sparql-results+json'}
BATCH = 30

TYPE_HINT = {
    'university': ['university', 'institute', 'research', 'laboratory', 'academy', 'college', 'school', 'center', 'centre', 'polytechnic'],
    'scholar':    ['physicist', 'researcher', 'scientist', 'professor', 'mathematician', 'computer scientist', 'engineer', 'academic', 'chemist'],
    'student':    ['physicist', 'researcher', 'scientist', 'engineer', 'entrepreneur', 'executive', 'founder', 'student'],
    'exec':       ['executive', 'entrepreneur', 'founder', 'businessperson', 'physicist', 'engineer', 'computer scientist', 'chief executive'],
    'company':    ['company', 'enterprise', 'startup', 'corporation', 'manufacturer', 'firm', 'business', 'organization', 'organisation'],
    'investor':   ['company', 'fund', 'investment', 'venture', 'capital', 'telecom', 'corporation', 'bank', 'enterprise'],
    'gov':        ['agency', 'ministry', 'government', 'administration', 'laboratory', 'institute', 'organization', 'organisation'],
}


def esc(s):
    return (s or '').replace('\\', '\\\\').replace('"', '\\"')


def sparql(q, retries=4):
    last = None
    for a in range(retries):
        try:
            data = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode()
            req = urllib.request.Request(EP, data=data, headers=UA)
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:
            last = e
            time.sleep(1.5 * (a + 1))
    raise last


def fetch_alias(terms):
    values = ' '.join(f'"{esc(t)}"@en' for t in terms)
    q = f'''SELECT ?item ?term ?desc WHERE {{
  VALUES ?term {{ {values} }}
  {{ ?item rdfs:label ?term }} UNION {{ ?item skos:altLabel ?term }}
  OPTIONAL {{ ?item schema:description ?desc . FILTER(lang(?desc)="en") }}
}}'''
    r = sparql(q)
    out = {}
    for b in r['results']['bindings']:
        t = b['term']['value']
        out.setdefault(t, set()).add((b['item']['value'].rsplit('/', 1)[-1],
                                      b.get('desc', {}).get('value', '')))
    return {k: list(v) for k, v in out.items()}


def main():
    d = json.load(open(P, encoding='utf-8'))
    rv = json.load(open(RP, encoding='utf-8'))
    by_id = {n['id']: n for n in d['nodes']}
    review_ids = [r['id'] for r in rv]

    # 构建探测词：节点英文名 + 自带 aliases
    work = []
    for nid in review_ids:
        n = by_id.get(nid)
        if not n:
            continue
        terms = set()
        en = (n.get('name_en') or '').strip()
        if en:
            terms.add(en)
        for a in (n.get('aliases') or []):
            a = (a or '').strip()
            if a and re.fullmatch(r'[A-Za-z0-9 \-\.\'&]+', a) and len(a) >= 3:
                terms.add(a)
        if terms:
            work.append((n, sorted(terms)))

    allterms = sorted({t for _, ts in work for t in ts})
    print(f'复核节点 {len(work)}，展开探测词 {len(allterms)} 个，分 {((len(allterms)-1)//BATCH)+1} 批\n')

    hit = {}
    for i in range(0, len(allterms), BATCH):
        chunk = allterms[i:i + BATCH]
        try:
            res = fetch_alias(chunk)
        except Exception as e:
            print(f'[批 {i//BATCH+1}] 失败: {e}')
            continue
        for t, cands in res.items():
            hit[t] = cands
        print(f'[批 {i//BATCH+1}] 累计标签命中 {len(hit)}')
        time.sleep(0.5)

    saved, still = [], []
    for n, terms in work:
        hints = TYPE_HINT.get(n['type'], [])
        pool = []
        for t in terms:
            for qid, desc in hit.get(t, []):
                pool.append((qid, desc, t))
        # 去重
        seen, uniq = set(), []
        for qid, desc, t in pool:
            if qid in seen:
                continue
            seen.add(qid)
            uniq.append((qid, desc, t))
        ok = [c for c in uniq if any(h in c[1].lower() for h in hints)]
        if len(ok) == 1:
            saved.append((n, ok[0][0], ok[0][1]))
        elif len(ok) > 1:
            still.append((n['id'], n['type'], terms[0], f'{len(ok)} 个候选均命中类型词'))
        else:
            still.append((n['id'], n['type'], terms[0],
                          f'无类型词命中（池 {len(uniq)} 个）' if uniq else '别名也无命中'))

    print(f'\n=== 阶段2结果 ===')
    print(f'可救回（别名通道唯一类型命中）：{len(saved)}')
    print(f'仍需人工复核：{len(still)}')
    print('\n救回样例（前 30）：')
    for n, qid, desc in saved[:30]:
        print(f'  {n["id"]:14s} {n["name"][:22]:24s} -> {qid:12s} {desc[:48]}')
    print('\n仍待处理样例（前 20）：')
    for row in still[:20]:
        print(f'  {row[0]:14s} {row[1]:9s} {str(row[2])[:26]:28s} {row[3]}')

    json.dump({'saved': [[n['id'], qid, desc] for n, qid, desc in saved],
               'still': still},
              open(r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/_alias_probe.json', 'w',
                   encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
