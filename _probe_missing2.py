# -*- coding: utf-8 -*-
"""抽查「无候选」桶的中文条目在 Wikidata 镜像里是否真的不存在。"""
import json, urllib.error, urllib.parse, urllib.request

M = 'https://wikidata.demo.openlinksw.com/sparql'
UA = {'User-Agent': 'qg/1.0', 'Accept': 'application/sparql-results+json'}
P = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#/>""".replace('/>', '#>')
P = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>"""


def run(q):
    d = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode()
    r = urllib.request.Request(M, data=d, headers=UA)
    try:
        with urllib.request.urlopen(r, timeout=90) as x:
            return json.loads(x.read().decode())
    except urllib.error.HTTPError as e:
        return {'ERR': e.code, 'body': e.read().decode('utf-8', 'replace')[:200]}


SAMPLE = ['本源量子', '玻色量子', '问天量子', '国仪量子', '图灵量子', '华翊量子',
          '未磁科技', '中科酷原', '启科量子', '国盾量子', '量子', '中科大量子']
for t in SAMPLE:
    q = P + """
SELECT ?item ?lbl ?lang WHERE {
  ?item rdfs:label ?lbl .
  FILTER(bif:contains(?lbl, "%s") && lang(?lbl) IN ("zh","zh-hans","zh-cn","en"))
  BIND(lang(?lbl) AS ?lang)
} LIMIT 8""" % t
    r = run(q)
    if 'ERR' in r:
        print('%-8s ERR %s %s' % (t, r['ERR'], r.get('body', '')[:100]))
        continue
    b = r['results']['bindings']
    print('%-8s -> %s' % (t, ' ; '.join('%s[%s]%s' % (
        x['item']['value'].split('/')[-1], x['lang']['value'], x['lbl']['value'][:20]) for x in b) or '（无）'))
