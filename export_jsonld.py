# export_jsonld.py — 将 quantum_network.json 导出为 JSON-LD（schema.org 词汇 + 自定义关系命名空间）
import json

P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
OUT = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.jsonld'
NS = 'https://kg.local/quantum#'
d = json.load(open(P, encoding='utf-8'))

TYPE_MAP = {
    'university': 'CollegeOrUniversity',
    'scholar': 'Person', 'student': 'Person', 'exec': 'Person',
    'company': 'Organization', 'investor': 'Organization',
}
REL_MAP = {  # 自定义谓词（中文关系名的 URI 化）
    '师承': NS + 'mentored',
    '联合研究': NS + 'collaboratesWith',
    '学校孵化': NS + 'spunOff',
    '任职': NS + 'affiliatedWith',
    '任职/创办': NS + 'foundedOrLeads',
    '投资/持股': NS + 'investedIn',
}

ctx = {
    '@vocab': NS,
    'schema': 'https://schema.org/',
    'name': 'schema:name', 'alternateName': 'schema:alternateName',
    'description': 'schema:description', 'url': 'schema:url',
    'sameAs': 'schema:sameAs', 'foundingDate': 'schema:foundingDate',
    'address': 'schema:address',
}

graph = []
for n in d['nodes']:
    e = {
        '@id': NS + 'node/' + n['id'],
        '@type': ['schema:' + TYPE_MAP[n['type']], NS + n['type'].capitalize()],
        'name': n['name'],
    }
    if n.get('name_en'): e['alternateName'] = n['name_en']
    if n.get('intro'): e['description'] = n['intro']
    if n.get('source'): e['url'] = n['source']
    if n.get('wikidata'):
        e['sameAs'] = 'https://www.wikidata.org/wiki/' + n['wikidata']
        if n.get('wikidata_src'):
            # 数据治理用：QID 的取得方式（manual / auto-label / auto-alias），非对外语义
            e[NS + 'wikidataSource'] = n['wikidata_src']
    if n.get('founded'): e['foundingDate'] = str(n['founded'])
    if n.get('country'): e['address'] = {'@type': 'schema:PostalAddress', 'schema:addressCountry': n['country']}
    e[NS + 'weight'] = n.get('weight')
    e[NS + 'region'] = n.get('region')
    if n.get('fields'): e[NS + 'researchField'] = n['fields']
    if n.get('uncertain'): e[NS + 'uncertain'] = True
    graph.append(e)

edges = []
for i, l in enumerate(d['links']):
    e = {
        '@id': NS + f'edge/{i}',
        '@type': NS + 'Relationship',
        NS + 'subject': {'@id': NS + 'node/' + l['s']},
        NS + 'predicate': REL_MAP.get(l['rel'], NS + 'relatedTo'),
        NS + 'object': {'@id': NS + 'node/' + l['t']},
        NS + 'strength': l.get('w'),
    }
    if l.get('note'): e[NS + 'note'] = l['note']
    if l.get('unc'): e[NS + 'uncertain'] = True
    edges.append(e)

doc = {'@context': ctx, '@graph': graph + edges}
json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'jsonld written: {len(graph)} entities + {len(edges)} relationships -> {OUT}')
