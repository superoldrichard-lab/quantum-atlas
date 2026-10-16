# -*- coding: utf-8 -*-
"""align_wikidata_v3.py — Wikidata 对齐 v3：消化剩余 149 条

v2 的失败模式（本轮实证）：
  1. 只做「字面精确匹配」→ Wikidata 的同义写法全漏：
       Pasqal 的 en 标签是 "PASQAL"、Riverlane 的 altLabel 是 "riverlane"（小写）、
       planqc 的标签是 "PlanQC GmbH" —— 大小写/后缀差异导致精确匹配全失手
  2. 人名把「关联到任一图谱机构」当身份证据 → 贺羽(中科大/国仪量子) 被误配到哈佛的 "Yu He"

v3 通道：
  A 发现层：OpenLink 托管的 Wikidata 镜像（wikidata.demo.openlinksw.com/sparql，
            WDQS 同源 Virtuoso；官方 query.wikidata.org 本机被网络阻断时的可用替代）
            用 Virtuoso 全文索引 bif:contains 在 rdfs:label / skos:altLabel 上做模糊召回
  B 匹配层：本地「规范化匹配」——小写、去空格标点、剥离公司后缀（GmbH/Ltd/Inc…）
  C 消歧层：P31 结构化类型 + P17 国别 + 人名「机构一致性」（节点 affiliation 对比
            候选人 P108/P69/P1416 的中英文标签），杜绝同名撞车

用法：
  python align_wikidata_v3.py --probe    只发现与匹配，落 _v3_candidates.json
  python align_wikidata_v3.py            决策试算（dry-run）
"""
import json
import os
import re
import sys
import time
import collections
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

MIRROR = 'https://wikidata.demo.openlinksw.com/sparql'      # OpenLink Wikidata 镜像（Virtuoso）
QLEVER = 'https://qlever.dev/api/wikidata'                   # 结构字段走 QLever（快且稳）
UA = {'User-Agent': 'QuantumKG-Align/4.0 (academic knowledge-graph enrichment)',
      'Accept': 'application/sparql-results+json'}

PREFIXES = '''PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
'''


def sparql(q, ep, retries=3, tag=''):
    last = None
    body = q if 'PREFIX' in q[:200] else PREFIXES + q
    for a in range(retries):
        try:
            url = ep + '?' + urllib.parse.urlencode({'query': body, 'format': 'json'})
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                txt = r.read().decode('utf-8')
            j = json.loads(txt)
            if 'results' not in j:
                raise RuntimeError('bad payload: %s' % txt[:160])
            return j
        except Exception as e:
            last = e
            time.sleep(1.5 * (a + 1))
    raise RuntimeError('SPARQL failed [%s]: %s' % (tag, last))


# ---------------- 文本规范化 ----------------
CJK_RE = re.compile(r'[\u4e00-\u9fff]')
# 仅剥离法律/公司形式后缀，不剥离领域词（quantum/科技/量子 等），避免 "Origin Quantum" 撞 "Origin"
LEGAL_SUFFIX = ['incorporated', 'corporation', 'limited', 'gmbh', 'inc', 'ltd', 'llc',
                'plc', 'ag', 'bv', 'nv', 'sas', 'sarl', 'pte', 'corp', 'co', 'oy',
                '有限公司', '股份有限公司', '股份', '公司']


def norm(s):
    s = (s or '').lower()
    return ''.join(ch for ch in s if ch.isalnum() or CJK_RE.match(ch))


def key_forms(s):
    """规范化 + 剥离后缀，返回可比较的键集合"""
    base = norm(s)
    out = set()
    if not base:
        return out
    out.add(base)
    for suf in LEGAL_SUFFIX:
        su = norm(suf)
        if su and base.endswith(su) and len(base) > len(su) + 2:
            out.add(base[:-len(su)])
    if base.startswith('the') and len(base) > 5:
        out.add(base[3:])
    return out


def min_key_len(k):
    return 2 if CJK_RE.search(k) else 3


def clean(s):
    s = (s or '').strip()
    s = re.sub(r'[（(][^）)]*[）)]', ' ', s)
    s = re.sub(r'[（(].*$', ' ', s)
    return re.sub(r'\s+', ' ', s).strip(' ·-—/、，,')


# ---------------- 载入 ----------------
data = json.load(open('quantum_network.json', encoding='utf-8'))
NODES = data['nodes']
BY_ID = {n['id']: n for n in NODES}
PEND = [n for n in NODES if not n.get('wikidata')]

COUNTRY_QID = {
    '中国': 'Q148', '中国大陆': 'Q148', '中国香港': 'Q8646', '中国台湾': 'Q865', '中国澳门': 'Q14773',
    '美国': 'Q30', '英国': 'Q145', '德国': 'Q183', '法国': 'Q142', '荷兰': 'Q55',
    '加拿大': 'Q16', '瑞士': 'Q39', '西班牙': 'Q29', '以色列': 'Q801', '新加坡': 'Q334',
    '日本': 'Q17', '澳大利亚': 'Q408', '奥地利': 'Q40', '芬兰': 'Q33', '瑞典': 'Q34',
    '意大利': 'Q38', '丹麦': 'Q35', '挪威': 'Q20', '比利时': 'Q31', '爱尔兰': 'Q27',
    '韩国': 'Q884', '印度': 'Q668', '俄罗斯': 'Q159', '波兰': 'Q36',
}


def country_qids(c):
    out = set()
    for part in re.split(r'[/、,，]', c or ''):
        part = part.strip()
        if part in COUNTRY_QID:
            out.add(COUNTRY_QID[part])
    return out


TYPE_P31_KW = {
    'university': ['university', 'college', 'institute of technology', 'higher education',
                   'polytechnic', 'grande école', 'normal school', 'engineering school',
                   'academy', 'school', 'educational institution', 'research institute',
                   'laboratory', 'institute', 'faculty'],
    'company': ['business', 'company', 'enterprise', 'organization', 'organisation',
                'manufacturer', 'public company', 'private company', 'startup',
                'corporation', 'subsidiary', 'joint venture', 'limited liability',
                'privately held', 'holding', 'brand', 'spin-off', 'spinout'],
    'investor': ['business', 'company', 'organization', 'organisation', 'investment',
                 'venture capital', 'private equity', 'fund', 'bank', 'financial',
                 'holding', 'sovereign wealth', 'pension', 'family office'],
    'gov': ['agency', 'government', 'organization', 'organisation', 'institute',
            'academy', 'research institute', 'ministry', 'authority', 'council',
            'committee', 'foundation', 'public institution', 'state-owned'],
}
HUMAN_TYPES = {'scholar', 'student', 'exec'}
OCC_KW_SCI = ['physicist', 'researcher', 'scientist', 'professor', 'engineer', 'academic',
              'mathematician', 'chemist', 'computer scientist', 'inventor', 'electrical engineer']
OCC_KW_BIZ = ['businessperson', 'entrepreneur', 'executive', 'manager', 'businessman',
              'businesswoman', 'chief executive', 'banker', 'investor', 'founder', 'director']
FIELD_KW = ['physics', 'quantum', 'optics', 'mathematics', 'computer science',
            'electrical engineering', 'engineering', 'chemistry', 'materials science',
            'quantum information', 'photonics']
DESC_DOMAIN = ['physicist', 'quantum', 'physics', 'researcher', 'professor', 'scientist']


def node_terms(n):
    raw = []
    for s in [n.get('name', ''), n.get('name_en', '')] + list(n.get('aliases') or []):
        for part in re.split(r'[/；;]', s or ''):
            p = clean(part)
            if p:
                raw.append(p)
    out, seen = [], set()
    for p in raw:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


# ---------------- A 发现层：镜像 bif:contains ----------------
def bif_expr(terms):
    parts = []
    for t in terms:
        if CJK_RE.search(t):
            parts.append("'%s'" % t.replace("'", ""))
            continue
        toks = [w for w in re.findall(r'[0-9a-zA-Z]+', t.lower()) if len(w) >= 3]
        if not toks:
            continue
        if len(toks) == 1:
            parts.append("'%s'" % toks[0])
        else:
            parts.append('(' + ' AND '.join("'%s'" % x for x in toks) + ')')
    return ' OR '.join(parts)


def discover(terms, pred, batch=10, limit=200):
    """在 label 或 altLabel 上用全文索引找候选 QID"""
    out = collections.defaultdict(set)      # qid -> {matched term}
    for i in range(0, len(terms), batch):
        chunk = terms[i:i + batch]
        expr = bif_expr(chunk)
        if not expr:
            continue
        q = '''SELECT ?item ?l WHERE {
  ?item %s ?l .
  FILTER(bif:contains(?l, "%s") && lang(?l) IN ("en","zh","zh-hans","zh-cn"))
} LIMIT %d''' % (pred, expr.replace('"', '\\"'), limit)
        try:
            res = sparql(q, MIRROR, tag='discover-%s-%d' % (pred, i))
        except Exception as e:
            print('  [warn] 发现批 %d (%s) 失败: %s' % (i // batch + 1, pred, str(e)[:90]), flush=True)
            continue
        for b in res['results']['bindings']:
            qid = b['item']['value'].rsplit('/', 1)[-1]
            if re.fullmatch(r'Q\d+', qid):
                out[qid].add(b['l']['value'])
        print('  发现批 %d/%d（%s）累计候选 %d' % (i // batch + 1,
              (len(terms) + batch - 1) // batch, pred.split(':')[-1], len(out)), flush=True)
        time.sleep(0.15)
    return out


def fetch_literals(qids, batch=40):
    """取候选实体的 label / altLabel / description（en+zh）"""
    info = {}
    qids = sorted(qids)
    for i in range(0, len(qids), batch):
        chunk = qids[i:i + batch]
        vals = ' '.join('wd:' + q for q in chunk)
        q = '''SELECT ?item ?lbl ?alt ?desc WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item rdfs:label ?lbl . FILTER(lang(?lbl) IN ("en","zh","zh-hans","zh-hant")) }
  OPTIONAL { ?item skos:altLabel ?alt . FILTER(lang(?alt) IN ("en","zh","zh-hans","zh-hant")) }
  OPTIONAL { ?item schema:description ?desc . FILTER(lang(?desc) = "en") }
}''' % vals
        try:
            res = sparql(q, MIRROR, tag='lit-%d' % i)
        except Exception as e:
            print('  [warn] 字面量批 %d 失败: %s' % (i // batch + 1, str(e)[:90]), flush=True)
            continue
        for b in res['results']['bindings']:
            qid = b['item']['value'].rsplit('/', 1)[-1]
            m = info.setdefault(qid, {'labels': [], 'alts': [], 'desc': ''})
            if b.get('lbl'):
                m['labels'].append(b['lbl']['value'])
            if b.get('alt'):
                m['alts'].append(b['alt']['value'])
            if b.get('desc'):
                m['desc'] = b['desc']['value']
        print('  字面量 %d/%d' % (min(i + batch, len(qids)), len(qids)), flush=True)
        time.sleep(0.15)
    return info


# ---------------- C 消歧层：结构化字段 ----------------
META_CACHE = '_v3_meta.json'


def fetch_meta(qids, tag_extra=''):
    cache = json.load(open(META_CACHE, encoding='utf-8')) if os.path.exists(META_CACHE) else {}
    todo = [q for q in sorted(qids) if q not in cache]
    batch = 40
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        vals = ' '.join('wd:' + q for q in chunk)
        q = '''SELECT ?item ?lbl ?desc ?p31 ?p31lbl ?p17 ?p106lbl ?p101lbl ?p108 ?p108lbl ?p69 ?p69lbl ?p1416 ?p1416lbl WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item rdfs:label ?lbl . FILTER(lang(?lbl)="en") }
  OPTIONAL { ?item schema:description ?desc . FILTER(lang(?desc)="en") }
  OPTIONAL { ?item wdt:P31 ?p31 . OPTIONAL { ?p31 rdfs:label ?p31lbl . FILTER(lang(?p31lbl)="en") } }
  OPTIONAL { ?item wdt:P17 ?p17 }
  OPTIONAL { ?item wdt:P106 ?p106 . OPTIONAL { ?p106 rdfs:label ?p106lbl . FILTER(lang(?p106lbl)="en") } }
  OPTIONAL { ?item wdt:P101 ?p101 . OPTIONAL { ?p101 rdfs:label ?p101lbl . FILTER(lang(?p101lbl)="en") } }
  OPTIONAL { ?item wdt:P108 ?p108 . OPTIONAL { ?p108 rdfs:label ?p108lbl . FILTER(lang(?p108lbl)="en") } }
  OPTIONAL { ?item wdt:P69 ?p69 . OPTIONAL { ?p69 rdfs:label ?p69lbl . FILTER(lang(?p69lbl)="en") } }
  OPTIONAL { ?item wdt:P1416 ?p1416 . OPTIONAL { ?p1416 rdfs:label ?p1416lbl . FILTER(lang(?p1416lbl)="en") } }
}''' % vals
        try:
            res = sparql(q, QLEVER, tag='meta-%d' % i)
        except Exception as e:
            print('  [warn] 元数据批 %d 失败: %s' % (i // batch + 1, str(e)[:90]), flush=True)
            continue
        for b in res['results']['bindings']:
            qid = b['item']['value'].rsplit('/', 1)[-1]
            m = cache.setdefault(qid, {'lbl': '', 'desc': '', 'p31': [], 'p31lbl': [], 'p17': [],
                                       'p106lbl': [], 'p101lbl': [], 'p108': [], 'p108lbl': [],
                                       'p69': [], 'p69lbl': [], 'p1416': [], 'p1416lbl': []})
            if b.get('lbl'):
                m['lbl'] = b['lbl']['value']
            if b.get('desc') and not m['desc']:
                m['desc'] = b['desc']['value']
            if b.get('p31'):
                v = b['p31']['value'].rsplit('/', 1)[-1]
                if v not in m['p31']:
                    m['p31'].append(v)
            if b.get('p31lbl') and b['p31lbl']['value'] not in m['p31lbl']:
                m['p31lbl'].append(b['p31lbl']['value'])
            if b.get('p17') and b['p17']['value'].rsplit('/', 1)[-1] not in m['p17']:
                m['p17'].append(b['p17']['value'].rsplit('/', 1)[-1])
            for k, qk in (('p106lbl', 'p106'), ('p101lbl', 'p101'), ('p108lbl', 'p108'),
                          ('p69lbl', 'p69'), ('p1416lbl', 'p1416')):
                if b.get(k) and b[k]['value'] not in m[k]:
                    m[k].append(b[k]['value'])
                if b.get(qk):
                    v = b[qk]['value'].rsplit('/', 1)[-1]
                    if v not in m[qk]:
                        m[qk].append(v)
        print('  元数据 %d/%d' % (min(i + batch, len(todo)), len(todo)), flush=True)
        time.sleep(0.15)
    json.dump(cache, open(META_CACHE, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return cache


def fetch_org_zh(org_qids, batch=50):
    """取机构的 zh 标签与别名 —— 用于把「中科大/清华大学」这类中文 affiliation 对上英文机构实体"""
    out = {}
    org_qids = sorted(set(org_qids))
    for i in range(0, len(org_qids), batch):
        chunk = org_qids[i:i + batch]
        vals = ' '.join('wd:' + q for q in chunk)
        q = '''SELECT ?item ?lbl ?alt WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item rdfs:label ?lbl . FILTER(lang(?lbl) IN ("zh","zh-hans","zh-hant")) }
  OPTIONAL { ?item skos:altLabel ?alt . FILTER(lang(?alt) IN ("zh","zh-hans","zh-hant","en")) }
}''' % vals
        try:
            res = sparql(q, MIRROR, tag='orgzh-%d' % i)
        except Exception as e:
            print('  [warn] 机构中文名批 %d 失败: %s' % (i // batch + 1, str(e)[:80]), flush=True)
            continue
        for b in res['results']['bindings']:
            qid = b['item']['value'].rsplit('/', 1)[-1]
            s = out.setdefault(qid, set())
            if b.get('lbl'):
                s.add(b['lbl']['value'])
            if b.get('alt'):
                s.add(b['alt']['value'])
    return {k: sorted(v) for k, v in out.items()}


# ---------------- 判定 ----------------
def type_ok(ntype, meta):
    if ntype in HUMAN_TYPES:
        return 'Q5' in meta.get('p31', [])
    blob = ' | '.join(meta.get('p31lbl', [])).lower()
    return any(k in blob for k in TYPE_P31_KW.get(ntype, []))


def occ_ok(ntype, meta):
    occ = ' | '.join(meta.get('p106lbl', [])).lower()
    fld = ' | '.join(meta.get('p101lbl', [])).lower()
    if ntype == 'scholar':
        return any(k in occ for k in OCC_KW_SCI) or any(k in fld for k in FIELD_KW)
    if ntype in ('exec', 'student'):
        return (any(k in occ for k in OCC_KW_SCI) or any(k in occ for k in OCC_KW_BIZ)
                or any(k in fld for k in FIELD_KW))
    return False


def country_conflict(n, meta):
    want = country_qids(n.get('country', ''))
    got = set(meta.get('p17', []))
    return bool(want) and bool(got) and not (want & got)


def affil_ok(n, meta, org_zh):
    """节点 affiliation/note/lab 是否与候选人 P108/P69/P1416 机构（含中文名/别名）吻合"""
    aff = ' '.join(str(n.get(k, '')) for k in ('affiliation', 'note', 'lab', 'dept'))
    aff_keys = key_forms(aff)
    if not aff_keys:
        return False
    org_ids = list(meta.get('p108', [])) + list(meta.get('p69', [])) + list(meta.get('p1416', []))
    cand = []
    for k in ('p108lbl', 'p69lbl', 'p1416lbl'):
        cand += list(meta.get(k, []))
    for q in org_ids:
        cand += org_zh.get(q, [])
    for c in cand:
        ck = key_forms(c)
        for a in aff_keys:
            for b in ck:
                if a == b and len(a) >= min_key_len(a):
                    return True
                if len(a) >= 4 and len(b) >= 4 and (a in b or b in a):
                    return True
    return False


def main():
    mode = 'dry'
    if '--probe' in sys.argv:
        mode = 'probe'

    # ---------- 载入 v2 候选（QLever 精确标签通道的结果，保留复用）----------
    v2c = json.load(open('_v2_candidates.json', encoding='utf-8')) if os.path.exists('_v2_candidates.json') else {}
    v2meta = json.load(open('_v2_meta.json', encoding='utf-8')) if os.path.exists('_v2_meta.json') else {}
    print('v2 候选：%d 条节点有候选' % sum(1 for k, v in v2c.items() if v), flush=True)

    # ---------- v3 发现 ----------
    term_owner = collections.defaultdict(set)   # term -> {node_id}
    all_terms = set()
    for n in PEND:
        for t in node_terms(n):
            all_terms.add(t)
            term_owner[t].add(n['id'])
    # CJK 词条交给 v2 的 QLever 中文标签精确通道；这里只做西文模糊召回（中文全文索引噪声太大）
    terms = sorted(t for t in all_terms if not CJK_RE.search(t))
    print('v3 发现：%d 个西文词条（中文词条沿用 v2 通道）' % len(terms), flush=True)

    disc = {}                                   # qid -> set(matched literal)
    for pred in ('rdfs:label', 'skos:altLabel'):
        d = discover(terms, pred)
        for q, s in d.items():
            disc.setdefault(q, set()).update(s)

    qids = sorted(disc)
    print('全文召回候选实体 %d 个' % len(qids), flush=True)
    lit = fetch_literals(qids) if qids else {}

    # ---------- 本地规范化匹配 ----------
    # 先建立 候选实体 -> 规范化键 索引
    ent_keys = {}
    for q, m in lit.items():
        ks = set()
        for s in m['labels'] + m['alts']:
            ks |= key_forms(s)
        ent_keys[q] = {k for k in ks if len(k) >= 3}

    v3c = collections.defaultdict(dict)         # node_id -> {qid: [matched terms]}
    for n in PEND:
        for t in node_terms(n):
            if CJK_RE.search(t):
                continue
            tk = {k for k in key_forms(t) if len(k) >= min_key_len(k)}
            if not tk:
                continue
            for q, ks in ent_keys.items():
                inter = tk & ks
                if inter and any(len(x) >= min_key_len(x) for x in inter):
                    v3c[n['id']].setdefault(q, []).append(t)
    print('规范化匹配：%d 条节点有候选' % len(v3c), flush=True)

    # ---------- 取结构化字段 ----------
    allq = set(qids)
    for lst in v2c.values():
        for c in lst:
            allq.add(c['qid'])
    for d in v3c.values():
        allq |= set(d)
    meta = fetch_meta(allq)
    # 人名候选的机构中文名
    org_ids = set()
    for q in allq:
        m = meta.get(q, {})
        org_ids |= set(m.get('p108', [])) | set(m.get('p69', [])) | set(m.get('p1416', []))
    org_zh = fetch_org_zh(org_ids) if org_ids else {}
    print('机构中文名：%d 个实体' % len(org_zh), flush=True)

    # ---------- 合并候选 ----------
    merged = {}
    for n in PEND:
        nid = n['id']
        recs = {}
        for c in v2c.get(nid, []):
            recs[c['qid']] = {'qid': c['qid'], 'terms': list(c['terms']),
                              'src_v': 'v2'}
        for q, ts in v3c.get(nid, {}).items():
            r = recs.setdefault(q, {'qid': q, 'terms': [], 'src_v': 'v3'})
            r['terms'] = sorted(set(r['terms']) | set(ts))
        out = []
        for q, r in recs.items():
            m = dict(v2meta.get(q, {}))
            m.update({k: v for k, v in meta.get(q, {}).items() if v})
            lm = lit.get(q, {})
            out.append({
                'qid': q, 'terms': r['terms'], 'src_v': r['src_v'],
                'lbl': m.get('lbl') or (lm.get('labels') or [''])[0],
                'labels': lm.get('labels', []),
                'alts': lm.get('alts', []),
                'desc': (m.get('desc') or lm.get('desc') or '')[:130],
                'p31lbl': m.get('p31lbl', []), 'p17': m.get('p17', []),
                'p106': m.get('p106lbl', []), 'p101': m.get('p101lbl', []),
                'p108': m.get('p108lbl', []), 'p69': m.get('p69lbl', []),
                'p1416': m.get('p1416lbl', []),
                'type_ok': type_ok(n['type'], m),
                'country_ok': bool(country_qids(n.get('country', '')) & set(m.get('p17', []))),
                'country_conflict': country_conflict(n, m),
                'occ_ok': occ_ok(n['type'], m),
                'affil_ok': affil_ok(n, m, org_zh),
                'desc_domain': any(k in (m.get('desc', '') or '').lower() for k in DESC_DOMAIN),
            })
        merged[nid] = out

    json.dump(merged, open('_v3_candidates.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('候选明细 → _v3_candidates.json', flush=True)
    if mode == 'probe':
        return

    # ---------- 决策 ----------
    TL = {'university': '高校', 'scholar': '学者', 'student': '学生', 'exec': '高管',
          'company': '公司', 'investor': '投资', 'gov': '政府'}
    accept, review = {}, {}
    for n in PEND:
        nid = n['id']
        lst = merged[nid]
        if not lst:
            review[nid] = ('无候选', [])
            continue
        kept = [c for c in lst if not c['country_conflict']]
        if not kept:
            review[nid] = ('候选全被国别否决', lst[:3])
            continue
        t_ok = [c for c in kept if c['type_ok']]
        if not t_ok:
            review[nid] = ('无类型自洽候选', kept[:3])
            continue
        if n['type'] in HUMAN_TYPES:
            cjk_name = bool(CJK_RE.search(n.get('name', '')))
            if cjk_name:
                pool = [c for c in t_ok if c['affil_ok']]
                why_gate = '人名(中文名)需机构一致'
            else:
                pool = [c for c in t_ok if c['affil_ok'] or c['occ_ok'] or c['desc_domain']]
                why_gate = '人名(西文名)需领域证据'
            if not pool:
                review[nid] = (why_gate, t_ok[:4])
                continue
        else:
            pool = t_ok
        if len(pool) == 1:
            accept[nid] = (pool[0]['qid'], 'unique')
            continue
        c_ok = [c for c in pool if c['country_ok']]
        if len(c_ok) == 1:
            accept[nid] = (c_ok[0]['qid'], 'country')
            continue
        a_ok = [c for c in pool if c['affil_ok']]
        if len(a_ok) == 1:
            accept[nid] = (a_ok[0]['qid'], 'affiliation')
            continue
        o_ok = [c for c in pool if c['occ_ok']]
        if len(o_ok) == 1:
            accept[nid] = (o_ok[0]['qid'], 'occupation')
            continue
        review[nid] = ('多候选未收敛(%d)' % len(pool), pool[:6])

    print()
    print('=== v3 决策结果 ===')
    print('可回填 %d / 待人工 %d' % (len(accept), len(review)))
    for k, v in collections.Counter(v[1] for v in accept.values()).most_common():
        print('   规则 %-14s %d' % (k, v))
    print('\n--- 可回填 ---')
    for nid, (q, why) in sorted(accept.items()):
        n = BY_ID[nid]
        c = next((x for x in merged[nid] if x['qid'] == q), {})
        print('  %-16s %-4s %-16s -> %-11s %-34s %s' % (
            nid, TL.get(n['type'], n['type']), n['name'][:15], q,
            (c.get('lbl') or '')[:32], why))
    print('\n--- 待人工（前 60）---')
    for nid, (why, lst) in sorted(review.items())[:60]:
        n = BY_ID[nid]
        print('  %-16s %-4s %-16s %s' % (nid, TL.get(n['type'], n['type']), n['name'][:15], why))
        for c in (lst or [])[:3]:
            print('        %-11s %-30s p31=%s' % (c['qid'], (c['lbl'] or '')[:28],
                                                  ','.join(c['p31lbl'])[:44]))

    json.dump({k: v[0] for k, v in accept.items()}, open('_v3_accept.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    json.dump({k: {'why': v[0],
                   'cands': [{kk: c[kk] for kk in ('qid', 'lbl', 'desc', 'p31lbl', 'terms')}
                             for c in (v[1] or [])[:3]]}
               for k, v in review.items()},
              open('_v3_review.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('\n接受清单 → _v3_accept.json；复核清单 → _v3_review.json')


if __name__ == '__main__':
    main()
