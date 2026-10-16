# -*- coding: utf-8 -*-
"""探测：① i_jiantou 的 Q140703954 到底是什么；② 抽查「无候选」桶的中文条目是否真的缺失。"""
import json, urllib.parse, urllib.request, sys

MIRROR = 'https://wikidata.demo.openlinksw.com/sparql'
UA = {'User-Agent': 'qg-align/1.0', 'Accept': 'application/sparql-results+json'}
P = """PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>"""


def run(q):
    data = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode()
    req = urllib.request.Request(MIRROR, data=data, headers=UA)
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read().decode('utf-8'))


def rows(res):
    return [{k: v['value'] for k, v in b.items()} for b in res['results']['bindings']]


print('### 1. Q140703954 直接解引用（含重定向）')
q = P + """
SELECT ?s ?p ?o WHERE { ?s ?p ?o . FILTER(?s = wd:Q140703954) } LIMIT 5"""
try:
    print(' 三倍组:', json.dumps(rows(run(q)), ensure_ascii=False)[:400])
except Exception as e:
    print(' ERR', e)

q = P + """
SELECT ?item ?lbl ?lang WHERE {
  VALUES ?t { "JIC Investment" "建投投资" "建投投資" }
  ?item rdfs:label ?lbl .
  FILTER(STR(?lbl) = ?t)
  BIND(lang(?lbl) AS ?lang)
} LIMIT 20"""
try:
    print(' 按精确标签搜:', json.dumps(rows(run(q)), ensure_ascii=False)[:600])
except Exception as e:
    print(' ERR', e)

q = P + """
SELECT ?item ?lbl ?lang WHERE {
  ?item rdfs:label ?lbl .
  FILTER(bif:contains(?lbl, "JIC Investment"))
  BIND(lang(?lbl) AS ?lang)
} LIMIT 20"""
try:
    print(' bif:contains "JIC Investment":', json.dumps(rows(run(q)), ensure_ascii=False)[:600])
except Exception as e:
    print(' ERR', e)

print()
print('### 2. 抽查「无候选」桶的中文条目是否真的缺失')
SAMPLE = ['本源量子', '玻色量子', '问天量子', '国仪量子', '图灵量子', '华翊量子',
          '未磁科技', '中科酷原', '国科量子', '启科量子']
for t in SAMPLE:
    q = P + """
    SELECT ?item ?lbl ?lang ?desc WHERE {
      ?item rdfs:label ?lbl .
      FILTER(bif:contains(?lbl, "%s"))
      BIND(lang(?lbl) AS ?lang)
      OPTIONAL { ?item schema:description ?desc FILTER(lang(?desc) IN ('zh','en')) }
    } LIMIT 6""" % t
    try:
        rs = rows(run(q))
        hits = ['%s[%s] %s' % (r.get('item', '').split('/')[-1], r.get('lang', ''), r.get('lbl', '')[:22]) for r in rs]
        print('  %-8s -> %s' % (t, ' ; '.join(hits) if hits else '（无）'))
    except Exception as e:
        print('  %-8s -> ERR %s' % (t, str(e)[:60]))
