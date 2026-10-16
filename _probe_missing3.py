# -*- coding: utf-8 -*-
"""按 v3 的 bif:contains 语法抽查「无候选」桶。"""
import json, urllib.error, urllib.parse, urllib.request

M = 'https://wikidata.demo.openlinksw.com/sparql'
UA = {'User-Agent': 'qg/1.0', 'Accept': 'application/sparql-results+json'}
P = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>"""


def run(q):
    d = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode()
    r = urllib.request.Request(M, data=d, headers=UA)
    try:
        with urllib.request.urlopen(r, timeout=90) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return {'ERR': e.code, 'body': e.read().decode('utf-8', 'replace')[:160]}


def probe(terms, pred='rdfs:label'):
    expr = ' OR '.join("'%s'" % t for t in terms)
    q = P + """
SELECT ?item ?l ?lang WHERE {
  ?item %s ?l .
  FILTER(bif:contains(?l, "%s") && lang(?l) IN ("en","zh","zh-hans","zh-cn"))
  BIND(lang(?l) AS ?lang)
} LIMIT 12""" % (pred, expr)
    return run(q)


TESTS = [
    ('本源量子', ['本源量子']),
    ('问天量子', ['问天量子']),
    ('国仪量子', ['国仪量子']),
    ('玻色量子', ['玻色量子']),
    ('图灵量子', ['图灵量子']),
    ('华翊量子', ['华翊量子']),
    ('jic', ['JIC Investment', '建投投资']),
    ('kets', ['KETS Quantum Security', 'KETS']),
    ('origin', ['Origin Quantum', '本源量子 computing']),
]
for name, terms in TESTS:
    r = probe(terms)
    if 'ERR' in r:
        print('%-10s ERR %s %s' % (name, r['ERR'], r.get('body', '')[:90]))
        continue
    b = r['results']['bindings']
    print('%-10s -> %s' % (name, ' ; '.join('%s[%s]%s' % (
        x['item']['value'].split('/')[-1], x['lang']['value'], x['l']['value'][:26]) for x in b) or '（无）'))
