# -*- coding: utf-8 -*-
"""
量子图谱 · Wikidata 对齐 v2 —— 消化剩余 149 条

与 v1（align_wikidata_sparql.py / probe_alias.py）的差别：
  v1 只查英文 rdfs:label，且用「描述文本是否含类型词」过滤 → 中文实体（标签是中文）整批漏，
     且描述措辞一变就误杀（如 "Michele Mosca" 描述里没写 mathematician）。
  v2 改为：
    通道A 中文标签/别名   rdfs:label@zh / skos:altLabel@zh
    通道B 英文标签/别名   rdfs:label@en / skos:altLabel@en
    通道C 结构化消歧      取回 P31(instance of) + P17(国家) + P106(职业) + P101(领域) + P108(雇主)，
                          用结构化字段判定，不再依赖描述文本

用法：
  python align_wikidata_v2.py --probe    仅探测候选 → _v2_candidates.json
  python align_wikidata_v2.py            决策试算（dry-run，不写盘）
  python align_wikidata_v2.py --write    决策并写盘（自动备份 quantum_network.json）
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

EP = 'https://query.wikidata.org/sparql'
UA = {'User-Agent': 'QuantumKG-Align/3.0 (academic knowledge-graph enrichment)',
      'Accept': 'application/sparql-results+json'}

# 端点优先级：WDQS（query.wikidata.org）在部分时段被网络阻断（实测 http=000 / SSL EOF），
# QLever（弗莱堡大学托管的 Wikidata 全量镜像）可达且更快，故设为主通道，WDQS 作回落。
ENDPOINTS = [
    'https://qlever.dev/api/wikidata',                 # QLever 新域名，直连 POST 免 308 跳转
    'https://qlever.cs.uni-freiburg.de/api/wikidata',  # 老域名（会 308 跳转，下面用 GET 兜底）
    'https://query.wikidata.org/sparql',               # 官方 WDQS
]
_ep = {'idx': 0}

PREFIXES = '''PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <http://schema.org/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
'''


def sparql(q, retries=4, tag=''):
    """带端点回落与重试的 SPARQL 查询。QLever 需显式声明 wd: 前缀。
    urllib 不跟随 308（QLever 老域名会 308），故遇 3xx 时改用 GET 重试。"""
    q = PREFIXES + q
    start = _ep['idx']
    order = ENDPOINTS[start:] + ENDPOINTS[:start]
    last = None
    for ep in order:
        for a in range(retries):
            try:
                data = urllib.parse.urlencode({'query': q}).encode()
                req = urllib.request.Request(ep, data=data, headers=UA)
                with urllib.request.urlopen(req, timeout=150) as r:
                    txt = r.read().decode('utf-8')
                j = json.loads(txt)
                if 'results' not in j:
                    raise RuntimeError('bad payload: %s' % txt[:160])
                _ep['idx'] = ENDPOINTS.index(ep)
                return j
            except urllib.error.HTTPError as e:
                last = e
                if e.code in (301, 302, 303, 307, 308):
                    try:                                  # 用 GET 跟随跳转
                        url = ep + '?' + urllib.parse.urlencode({'query': q})
                        req = urllib.request.Request(url, headers=UA)
                        with urllib.request.urlopen(req, timeout=150) as r:
                            j = json.loads(r.read().decode('utf-8'))
                        if 'results' in j:
                            _ep['idx'] = ENDPOINTS.index(ep)
                            return j
                        raise RuntimeError('bad payload')
                    except Exception as e2:
                        last = e2
                time.sleep(1.0 * (a + 1))
            except Exception as e:
                last = e
                time.sleep(1.0 * (a + 1))
    raise RuntimeError('SPARQL failed %s: %s' % (tag, last))


CJK = re.compile(r'[\u4e00-\u9fff]')


def clean(s):
    s = (s or '').strip()
    s = re.sub(r'[（(][^）)]*[）)]', ' ', s)
    s = re.sub(r'[（(].*$', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip(' ·-—/、，,')


def node_terms(n):
    """返回 [(term, lang), ...]，lang ∈ {zh, zh-hans, zh-cn, en}"""
    raw = []
    for s in [n.get('name', ''), n.get('name_en', '')] + list(n.get('aliases') or []):
        for part in re.split(r'[/；;]', s or ''):
            p = clean(part)
            if p:
                raw.append(p)
    out, seen = [], set()
    for p in raw:
        if CJK.search(p):
            langs = ZH_LANGS
        else:
            langs = ['en']
        for L in langs:
            k = (p, L)
            if k in seen:
                continue
            seen.add(k)
            out.append(k)
    return out


ZH_LANGS = ['zh']          # 主通道：Wikidata 中文标签绝大多数打 zh
ZH_LANGS_2 = ['zh-hans', 'zh-cn', 'zh-hant', 'zh-tw']   # 补漏通道


# ---------------- 国家 → QID ----------------
COUNTRY_QID = {
    '中国': 'Q148', '中国大陆': 'Q148', '中国香港': 'Q8646', '中国台湾': 'Q865', '中国澳门': 'Q14773',
    '美国': 'Q30', '英国': 'Q145', '德国': 'Q183', '法国': 'Q142', '荷兰': 'Q55',
    '加拿大': 'Q16', '瑞士': 'Q39', '西班牙': 'Q29', '以色列': 'Q801', '新加坡': 'Q334',
    '日本': 'Q17', '澳大利亚': 'Q408', '奥地利': 'Q40', '芬兰': 'Q33', '瑞典': 'Q34',
    '意大利': 'Q38', '丹麦': 'Q35', '挪威': 'Q20', '比利时': 'Q31', '爱尔兰': 'Q27',
    '韩国': 'Q884', '印度': 'Q668', '俄罗斯': 'Q159', '波兰': 'Q36', '捷克': 'Q213',
}


def country_qids(c):
    out = set()
    for part in re.split(r'[/、,，]', c or ''):
        part = part.strip()
        if part in COUNTRY_QID:
            out.add(COUNTRY_QID[part])
    return out


# ---------------- 类型 → P31 关键词 ----------------
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
              'businesswoman', 'chief executive', 'banker', 'investor', 'founder']
FIELD_KW = ['physics', 'quantum', 'optics', 'mathematics', 'computer science',
            'electrical engineering', 'engineering', 'chemistry', 'materials science',
            'quantum information', 'photonics']


# ---------------- 载入 ----------------
data = json.load(open('quantum_network.json', encoding='utf-8'))
NODES = data['nodes']
BY_ID = {n['id']: n for n in NODES}
PEND = [n for n in NODES if not n.get('wikidata')]
# 图谱内已知机构名（用于雇主消歧）
KNOWN_ORG_NAMES = set()
for n in NODES:
    if n['type'] in ('company', 'university', 'investor', 'gov'):
        for s in [n.get('name', ''), n.get('name_en', '')] + list(n.get('aliases') or []):
            c = clean(s)
            if len(c) > 3:
                KNOWN_ORG_NAMES.add(c.lower())


def build_term_index(nodes):
    t2n = collections.defaultdict(set)
    n2t = {}
    for n in nodes:
        ts = node_terms(n)
        n2t[n['id']] = ts
        for t, L in ts:
            t2n[(t, L)].add(n['id'])
    return t2n, n2t


def lookup_labels(t2n, cache_tag='label'):
    """分批查 rdfs:label / skos:altLabel。B=40（实测 200 会拖垮端点）。
    每批结束即落盘，进程被打断可断点续跑。"""
    cache_path = '_v2_%s.json' % cache_tag
    keys = [k for k in t2n if '"' not in k[0] and '\\' not in k[0]]
    hits = collections.defaultdict(set)      # node_id -> {qid}
    matched = collections.defaultdict(dict)  # node_id -> {qid: [terms]}
    if os.path.exists(cache_path):
        c = json.load(open(cache_path, encoding='utf-8'))
        for nid, qs in c.get('hits', {}).items():
            hits[nid] = set(qs)
        for nid, d in c.get('matched', {}).items():
            for q, ts in d.items():
                matched[nid][q] = ts
        done = set(c.get('done', []))
        print('  [resume] 已缓存 %d 条候选，已完成批次 %s' % (len(hits), sorted(done)), flush=True)
    else:
        done = set()

    B = 40
    nbatch = (len(keys) + B - 1) // B

    def save():
        json.dump({'hits': {k: sorted(v) for k, v in hits.items()},
                   'matched': {k: v for k, v in matched.items()},
                   'done': sorted(done)},
                  open(cache_path, 'w', encoding='utf-8'), ensure_ascii=False)

    for bi in range(0, len(keys), B):
        bno = bi // B + 1
        if bno in done:
            continue
        chunk = keys[bi:bi + B]
        vals = ' '.join('%s@%s' % (json.dumps(t, ensure_ascii=False), L) for t, L in chunk)
        ok = True
        for pred in ('rdfs:label', 'skos:altLabel'):
            q = '''SELECT ?item ?t WHERE {
  VALUES ?t { %s }
  ?item %s ?t .
}''' % (vals, pred)
            try:
                res = sparql(q, tag='%s#%d' % (pred, bi))
            except Exception as e:
                print('  [warn] %s 批 %d 失败: %s' % (pred, bno, e), flush=True)
                ok = False
                continue
            for b in res['results']['bindings']:
                qid = b['item']['value'].rsplit('/', 1)[-1]
                if not re.fullmatch(r'Q\d+', qid):
                    continue          # 过滤 Lexeme/Property 等非实体（QLever 会返回 L* 词位）
                t = b['t']['value']
                L = b['t'].get('xml:lang', '')
                for nid in t2n.get((t, L), ()):
                    hits[nid].add(qid)
                    matched[nid].setdefault(qid, []).append(t)
        if ok:
            done.add(bno)
        save()
        print('  批次 %d/%d 完成（累计候选节点 %d）' % (bno, nbatch, len(hits)), flush=True)
        time.sleep(0.2)
    return hits, matched


def fetch_meta(qids, cache_path='_v2_meta.json'):
    cache = {}
    if os.path.exists(cache_path):
        cache = json.load(open(cache_path, encoding='utf-8'))
    todo = [q for q in qids if q not in cache]
    B = 40
    for i in range(0, len(todo), B):
        chunk = todo[i:i + B]
        vals = ' '.join('wd:' + q for q in chunk)
        q = '''SELECT ?item ?lbl ?desc ?p31 ?p31lbl ?p17 ?p17lbl ?p106lbl ?p101lbl ?p108lbl WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item rdfs:label ?lbl . FILTER(lang(?lbl)="en") }
  OPTIONAL { ?item schema:description ?desc . FILTER(lang(?desc)="en") }
  OPTIONAL { ?item wdt:P31 ?p31 . OPTIONAL { ?p31 rdfs:label ?p31lbl . FILTER(lang(?p31lbl)="en") } }
  OPTIONAL { ?item wdt:P17 ?p17 . OPTIONAL { ?p17 rdfs:label ?p17lbl . FILTER(lang(?p17lbl)="en") } }
  OPTIONAL { ?item wdt:P106 ?p106 . OPTIONAL { ?p106 rdfs:label ?p106lbl . FILTER(lang(?p106lbl)="en") } }
  OPTIONAL { ?item wdt:P101 ?p101 . OPTIONAL { ?p101 rdfs:label ?p101lbl . FILTER(lang(?p101lbl)="en") } }
  OPTIONAL { ?item wdt:P108 ?p108 . OPTIONAL { ?p108 rdfs:label ?p108lbl . FILTER(lang(?p108lbl)="en") } }
  OPTIONAL { ?item wdt:P69 ?p69 . OPTIONAL { ?p69 rdfs:label ?p69lbl . FILTER(lang(?p69lbl)="en") } }
  OPTIONAL { ?item wdt:P1416 ?p1416 . OPTIONAL { ?p1416 rdfs:label ?p1416lbl . FILTER(lang(?p1416lbl)="en") } }
}''' % vals
        res = sparql(q, tag='meta#%d' % i)
        for b in res['results']['bindings']:
            qid = b['item']['value'].rsplit('/', 1)[-1]
            m = cache.setdefault(qid, {'lbl': '', 'desc': '', 'p31': [], 'p31lbl': [],
                                       'p17': [], 'p106lbl': [], 'p101lbl': [],
                                       'p108lbl': [], 'p69lbl': [], 'p1416lbl': []})
            for _k in ('p69lbl', 'p1416lbl'):
                m.setdefault(_k, [])
            if b.get('lbl'):
                m['lbl'] = b['lbl']['value']
            if b.get('desc'):
                m['desc'] = b['desc']['value']
            if b.get('p31'):
                p = b['p31']['value'].rsplit('/', 1)[-1]
                if p not in m['p31']:
                    m['p31'].append(p)
            if b.get('p31lbl') and b['p31lbl']['value'] not in m['p31lbl']:
                m['p31lbl'].append(b['p31lbl']['value'])
            if b.get('p17') and b['p17']['value'].rsplit('/', 1)[-1] not in m['p17']:
                m['p17'].append(b['p17']['value'].rsplit('/', 1)[-1])
            for k in ('p106lbl', 'p101lbl', 'p108lbl', 'p69lbl', 'p1416lbl'):
                if b.get(k) and b[k]['value'] not in m[k]:
                    m[k].append(b[k]['value'])
        print('  元数据 %d/%d' % (min(i + B, len(todo)), len(todo)), flush=True)
        time.sleep(0.2)
    json.dump(cache, open(cache_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return cache


def type_ok(ntype, meta):
    if ntype in HUMAN_TYPES:
        return 'Q5' in meta.get('p31', [])
    kws = TYPE_P31_KW.get(ntype, [])
    blob = ' | '.join(meta.get('p31lbl', [])).lower()
    return any(k in blob for k in kws)


def occ_ok(ntype, meta):
    occ = ' | '.join(meta.get('p106lbl', [])).lower()
    fld = ' | '.join(meta.get('p101lbl', [])).lower()
    if ntype == 'scholar':
        return any(k in occ for k in OCC_KW_SCI) or any(k in fld for k in FIELD_KW)
    if ntype in ('exec', 'student'):
        return (any(k in occ for k in OCC_KW_SCI) or any(k in occ for k in OCC_KW_BIZ)
                or any(k in fld for k in FIELD_KW))
    return False


def desc_domain(meta):
    """描述里的领域信号（仅作正向加分，不做过滤——v1 就是误用它当过滤条件才漏掉整批）"""
    d = (meta.get('desc', '') or '').lower()
    return any(k in d for k in ['physicist', 'quantum', 'physics', 'researcher',
                                'professor', 'scientist', 'engineer'])


def linked_ok(n, meta):
    """候选人是否通过 P108 雇主 / P69 母校 / P1416 隶属 关联到图谱内已知机构"""
    labels = (list(meta.get('p108lbl', [])) + list(meta.get('p69lbl', []))
              + list(meta.get('p1416lbl', [])))
    for e in labels:
        el = clean(e).lower()
        if len(el) < 4:
            continue
        if el in KNOWN_ORG_NAMES:
            return True
        for k in KNOWN_ORG_NAMES:
            if len(k) >= 6 and (k in el or el in k):
                return True
    return False


def country_conflict(n, meta):
    """节点有国别、候选有 P17，且两者不相交 → 判负（Xanadu 误配乌克兰存托机构就是这样抓到的）"""
    want = country_qids(n.get('country', ''))
    got = set(meta.get('p17', []))
    return bool(want) and bool(got) and not (want & got)


def country_ok(n, meta):
    want = country_qids(n.get('country', ''))
    if not want:
        return False
    return bool(want & set(meta.get('p17', [])))


def main():
    mode = 'dry'
    if '--probe' in sys.argv:
        mode = 'probe'
    if '--write' in sys.argv:
        mode = 'write'

    t2n, n2t = build_term_index(PEND)
    print('待对齐 %d 条，词条 %d 个' % (len(PEND), len(t2n)), flush=True)
    hits, matched = lookup_labels(t2n)
    allq = set()
    for s in hits.values():
        allq |= s
    print('标签/别名通道命中：%d 条节点有候选，候选实体 %d 个' % (len(hits), len(allq)), flush=True)

    # 补漏通道：中文变体语言标签（zh-hans / zh-cn / zh-hant / zh-tw）
    miss = [n for n in PEND if n['id'] not in hits]
    if miss:
        t2n2 = collections.defaultdict(set)
        for n in miss:
            for t, L in node_terms(n):
                if L in ZH_LANGS_2:
                    t2n2[(t, L)].add(n['id'])
        if t2n2:
            print('补漏通道：%d 条无候选，试 %d 个中文变体词条' % (len(miss), len(t2n2)), flush=True)
            h2, m2 = lookup_labels(t2n2, cache_tag='label2')
            for nid, s in h2.items():
                hits[nid] |= s
                for q, ts in m2[nid].items():
                    matched[nid].setdefault(q, []).extend(ts)
            allq = set()
            for s in hits.values():
                allq |= s
            print('补漏后：%d 条节点有候选，候选实体 %d 个' % (len(hits), len(allq)), flush=True)

    meta = fetch_meta(sorted(allq))

    # 汇总
    cands = {}
    for n in PEND:
        nid = n['id']
        qs = hits.get(nid, set())
        lst = []
        for q in sorted(qs):
            m = meta.get(q, {})
            lst.append({
                'qid': q,
                'lbl': m.get('lbl', ''),
                'desc': m.get('desc', '')[:110],
                'p31': m.get('p31', []),
                'p31lbl': m.get('p31lbl', []),
                'p17': m.get('p17', []),
                'p106': m.get('p106lbl', []),
                'p101': m.get('p101lbl', []),
                'p108': m.get('p108lbl', [])[:4],
                'p69': m.get('p69lbl', [])[:4],
                'p1416': m.get('p1416lbl', [])[:4],
                'terms': sorted(set(matched.get(nid, {}).get(q, []))),
                'type_ok': type_ok(n['type'], m),
                'country_ok': country_ok(n, m),
                'country_conflict': country_conflict(n, m),
                'occ_ok': occ_ok(n['type'], m),
                'linked_ok': linked_ok(n, m),
                'desc_domain': desc_domain(m),
            })
        cands[nid] = lst

    json.dump(cands, open('_v2_candidates.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('候选明细 → _v2_candidates.json')

    # 决策
    TL = {'university': '高校', 'scholar': '学者', 'student': '学生', 'exec': '高管',
          'company': '公司', 'investor': '投资', 'gov': '政府'}
    accept, review = {}, {}
    for n in PEND:
        nid = n['id']
        lst = cands[nid]
        if not lst:
            review[nid] = ('无候选', [])
            continue
        # ① 国别冲突一票否决
        kept = [c for c in lst if not c['country_conflict']]
        if not kept:
            review[nid] = ('候选全部国别冲突', lst[:4])
            continue
        # ② 类型必须自洽（P31 结构化判定，不再看描述文本）
        t_ok = [c for c in kept if c['type_ok']]
        if not t_ok:
            review[nid] = ('无类型自洽候选', kept[:4])
            continue
        # ③ 人名必须有领域关联证据（职业/领域/机构关联/描述领域词）
        if n['type'] in HUMAN_TYPES:
            pool = [c for c in t_ok if c['occ_ok'] or c['linked_ok'] or c['desc_domain']]
            if not pool:
                review[nid] = ('人名无领域证据', t_ok[:4])
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
        l_ok = [c for c in pool if c['linked_ok']]
        if len(l_ok) == 1:
            accept[nid] = (l_ok[0]['qid'], 'linked')
            continue
        o_ok = [c for c in pool if c['occ_ok']]
        if len(o_ok) == 1:
            accept[nid] = (o_ok[0]['qid'], 'occupation')
            continue
        review[nid] = ('多候选未收敛(%d)' % len(pool), pool[:6])

    print()
    print('=== 决策结果 ===')
    print('可回填 %d 条 / 待人工 %d 条' % (len(accept), len(review)))
    by_rule = collections.Counter(v[1] for v in accept.values())
    for k, v in by_rule.most_common():
        print('   规则 %-14s %d' % (k, v))
    print()
    print('--- 可回填明细 ---')
    for nid, (q, why) in sorted(accept.items()):
        n = BY_ID[nid]
        m = meta.get(q, {})
        print('  %-16s %-9s %-18s -> %-11s %-34s %s' % (
            nid, TL.get(n['type'], n['type']), n['name'][:16], q,
            (m.get('lbl', '') or '')[:32], why))
    print()
    print('--- 待人工明细 ---')
    for nid, (why, lst) in sorted(review.items()):
        n = BY_ID[nid]
        print('  %-16s %-9s %-18s %s' % (nid, TL.get(n['type'], n['type']), n['name'][:16], why))
        for c in (lst or [])[:3]:
            print('        %-11s %-30s p31=%s' % (c['qid'], (c['lbl'] or '')[:28],
                                                  ','.join(c['p31lbl'])[:44]))

    json.dump({k: v[0] for k, v in accept.items()}, open('_v2_accept.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print()
    print('接受清单 → _v2_accept.json')


if __name__ == '__main__':
    main()
