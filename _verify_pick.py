# -*- coding: utf-8 -*-
"""按 QID 拉取结构化证据（OpenLink Virtuoso Wikidata 镜像），用于人工终裁。"""
import json, urllib.parse, urllib.request, sys

MIRROR = 'https://wikidata.demo.openlinksw.com/sparql'
UA = {'User-Agent': 'qg-align/1.0', 'Accept': 'application/sparql-results+json'}

P = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>"""

QIDS = sys.argv[1].split(',') if len(sys.argv) > 1 else []
if not QIDS:
    QIDS = [
        'Q59504713','Q89313939','Q55416274','Q89586598','Q103147220','Q112360947',
        'Q92090680','Q57132825','Q88187576','Q102256946','Q137539305','Q140703954',
        'Q103228119','Q89696888','Q83259','Q86743373','Q134552079','Q13344','Q20791505',
        'Q168756','Q106658038','Q49471196','Q16192438','Q11093326','Q114818523','Q41911885',
    ]


def run(q):
    data = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode()
    req = urllib.request.Request(MIRROR, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode('utf-8'))


def label(qid, lang):
    return ('http://www.wikidata.org/entity/%s' % qid, lang)


q = P + """
SELECT ?item ?lblen ?lblzh ?desc (GROUP_CONCAT(DISTINCT ?p31l; SEPARATOR='|') AS ?p31)
       (GROUP_CONCAT(DISTINCT ?occ; SEPARATOR='|') AS ?p106)
       (GROUP_CONCAT(DISTINCT ?field; SEPARATOR='|') AS ?p101)
       (GROUP_CONCAT(DISTINCT ?emp; SEPARATOR='|') AS ?p108)
       (GROUP_CONCAT(DISTINCT ?a; SEPARATOR='|') AS ?p69)
       (GROUP_CONCAT(DISTINCT ?orc; SEPARATOR='|') AS ?orcid)
WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item rdfs:label ?lblen FILTER(lang(?lblen)='en') }
  OPTIONAL { ?item rdfs:label ?lblzh FILTER(lang(?lblzh) IN ('zh','zh-hans','zh-cn')) }
  OPTIONAL { ?item schema:description ?desc FILTER(lang(?desc)='en') }
  OPTIONAL { ?item wdt:P31 ?p31v . ?p31v rdfs:label ?p31l FILTER(lang(?p31l)='en') }
  OPTIONAL { ?item wdt:P106 ?ocv . ?ocv rdfs:label ?occ FILTER(lang(?occ)='en') }
  OPTIONAL { ?item wdt:P101 ?fv . ?fv rdfs:label ?field FILTER(lang(?field)='en') }
  OPTIONAL { ?item wdt:P108 ?ev . ?ev rdfs:label ?emp FILTER(lang(?emp)='en') }
  OPTIONAL { ?item wdt:P69 ?av . ?av rdfs:label ?a FILTER(lang(?a)='en') }
  OPTIONAL { ?item wdt:P496 ?orc }
} GROUP BY ?item ?lblen ?lblzh ?desc ORDER BY ?item
""" % ' '.join('wd:' + x for x in QIDS)

try:
    res = run(q)
    for b in res['results']['bindings']:
        g = lambda k: b.get(k, {}).get('value', '')
        print('%-11s %-32s zh=%-16s' % (g('item').split('/')[-1], g('lblen')[:32], g('lblzh')[:16]))
        print('    desc: %s' % g('desc')[:90])
        print('    p31 : %s' % g('p31')[:110])
        print('    p106: %s | p101: %s' % (g('p106')[:70], g('p101')[:40]))
        print('    p108: %s' % g('p108')[:120])
        print('    p69 : %s | orcid: %s' % (g('p69')[:80], g('orcid')[:30]))
except Exception as e:
    print('ERR', type(e).__name__, e)
