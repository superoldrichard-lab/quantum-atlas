# align_wikidata_sparql.py — 通过 SPARQL 端点批量对齐 Wikidata QID
#
# 背景：www.wikidata.org 的 wbsearchentities API 在本机网络下极不稳定（约 1/5 成功率），
#       但 query.wikidata.org/sparql 稳定可达（200 / ~1.6s），故改走 SPARQL。
#       优势：一次请求可用 VALUES 批量匹配多个实体名，352 个待对齐节点仅需 ~8 次请求。
#
# 策略：
#   1. 按英文标签（rdfs:label@en）精确匹配，并取一句话描述
#   2. 按节点类型做描述词过滤（与 align_wikidata.py 同一套 TYPE_HINT）
#   3. 置信度分级：标签精确 + 描述命中类型词 => high（回填）；唯一候选但描述未命中 => medium（进复核清单）；多候选/无候选 => 留空
#   4. 绝不强行回填低置信项，全部进 review 清单
#
# 用法：
#   python align_wikidata_sparql.py --dry-run          # 只报告，不写文件
#   python align_wikidata_sparql.py --limit 30         # 只处理前 30 个
#   python align_wikidata_sparql.py                    # 全量回填高置信项
import json, re, sys, time, urllib.parse, urllib.request

P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
EP = 'https://query.wikidata.org/sparql'
UA = {'User-Agent': 'QuantumKG-Align/2.0 (academic research graph alignment; contact: local)',
      'Accept': 'application/sparql-results+json'}
BATCH = 40

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
    """POST 查询，带重试（端点偶发抖动）"""
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


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def fetch_batch(terms):
    """terms: [(name, label)]；返回 {label: [(qid, label, desc), ...]}"""
    values = ' '.join(f'"{esc(lb)}"@en' for _, lb in terms)
    q = f'''SELECT ?item ?lbl ?desc WHERE {{
  VALUES ?lbl {{ {values} }}
  ?item rdfs:label ?lbl .
  OPTIONAL {{ ?item schema:description ?desc . FILTER(lang(?desc)="en") }}
}}'''
    r = sparql(q)
    out = {}
    for b in r['results']['bindings']:
        lb = b['lbl']['value']
        qid = b['item']['value'].rsplit('/', 1)[-1]
        out.setdefault(lb, []).append((qid, lb, b.get('desc', {}).get('value', '')))
    return out


def main():
    dry = '--dry-run' in sys.argv
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])
    d = json.load(open(P, encoding='utf-8'))
    todo = [n for n in d['nodes'] if not n.get('wikidata')]
    if limit:
        todo = todo[:limit]
    todo = [n for n in todo if (n.get('name_en') or n.get('name'))]

    # 用英文名做标签匹配；无 name_en 的落到中文名（@en 标签不会有结果，会在复核里体现）
    work = [(n, (n.get('name_en') or n['name']).strip()) for n in todo]
    print(f'待对齐 {len(work)} 个节点，分 {((len(work)-1)//BATCH)+1} 批\n')

    hits, review, errors = [], [], []
    for i in range(0, len(work), BATCH):
        chunk = work[i:i + BATCH]
        terms = [(n['id'], lb) for n, lb in chunk]
        try:
            res = fetch_batch(terms)
        except Exception as e:
            errors.append(f'批 {i//BATCH+1} 失败: {e}')
            print(f'[批 {i//BATCH+1}] SPARQL 失败: {e}')
            continue
        for n, lb in chunk:
            cands = res.get(lb, [])
            hints = TYPE_HINT.get(n['type'], [])
            if len(cands) == 1:
                qid, cl, desc = cands[0]
                if any(h in desc.lower() for h in hints):
                    hits.append((n, qid, desc))
                    continue
                review.append({'id': n['id'], 'type': n['type'], 'term': lb,
                               'why': '唯一候选但描述未命中类型词',
                               'candidates': cands[:3]})
            elif len(cands) > 1:
                # 多个同名实体：只有恰好一个描述命中类型词才回填
                ok = [c for c in cands if any(h in c[2].lower() for h in hints)]
                if len(ok) == 1:
                    hits.append((n, ok[0][0], ok[0][2]))
                else:
                    review.append({'id': n['id'], 'type': n['type'], 'term': lb,
                                   'why': f'{len(cands)} 个同名候选',
                                   'candidates': cands[:5]})
            else:
                review.append({'id': n['id'], 'type': n['type'], 'term': lb,
                               'why': '无精确标签匹配', 'candidates': []})
        print(f'[批 {i//BATCH+1}/{(len(work)-1)//BATCH+1}] 累计回填 {len(hits)}，复核 {len(review)}')
        time.sleep(0.5)

    if not dry:
        for n, qid, _ in hits:
            n['wikidata'] = qid
        json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    rp = P.replace('.json', '_wikidata_review.json')
    json.dump(review, open(rp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    # 无论是否 dry-run，都落一份命中清单，便于反向校验
    hp = P.replace('.json', '_wikidata_hits.json')
    json.dump([{'id': n['id'], 'type': n['type'], 'name': n['name'],
                'name_en': n.get('name_en', ''), 'qid': qid, 'desc': desc}
               for n, qid, desc in hits],
              open(hp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    print(f'\n=== 结果 ===')
    print(f'回填 {len(hits)}，待复核 {len(review)}，失败批次 {len(errors)}')
    print(f'复核清单 -> {rp}' + ('  [DRY RUN，数据未写盘]' if dry else '  [已写盘]'))
    print('\n回填样例（前 25）：')
    for n, qid, desc in hits[:25]:
        print(f'  {n["id"]:12s} {n["name"]:24s} -> {qid:12s} {desc[:55]}')


if __name__ == '__main__':
    main()
