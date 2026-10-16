# validate.py — 按 SCHEMA.md 约束校验 quantum_network.json
import json, re, sys
from collections import Counter

P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
d = json.load(open(P, encoding='utf-8'))
errors, warnings = [], []

NODE_TYPES = {'university','scholar','student','exec','company','investor'}
PERSON = {'scholar','student','exec'}
ORG = {'university','company'}
REGIONS = {'北美','欧洲','中国','亚太及其他'}
FIELDS = {'量子计算','量子通信','量子传感与测量','量子软件与算法','量子网络'}
ID_PREFIX = {'university':'u_','scholar':'s_','student':'st_','exec':'x_','company':'c_','investor':'i_'}
# 关系约束：rel -> (允许的 source 类型集合, 允许的 target 类型集合, w 范围)
# 注意「师承」边方向语义为「导师 → 学生」（读作"指导"）
REL_RULES = {
 '师承':     ({'scholar'}, PERSON, {1,2,3}),
 '联合研究': (NODE_TYPES, NODE_TYPES, {1,2,3}),
 '学校孵化': ({'university'}, {'company'}, {1,2,3}),
 '任职':     (PERSON, ORG, {1,2,3}),
 '任职/创办': (PERSON, {'company'}, {1,2,3}),
 '投资/持股': ({'investor','company'}, {'company'}, {1,2,3}),
}

ids = set()
for n in d['nodes']:
    nid = n.get('id','?')
    if nid in ids: errors.append(f'duplicate node id: {nid}')
    ids.add(nid)
    t = n.get('type')
    if t not in NODE_TYPES: errors.append(f'{nid}: bad type {t}')
    elif not nid.startswith(ID_PREFIX[t]): warnings.append(f'{nid}: id prefix mismatch for type {t}')
    for f in ('name','intro','country','region'):
        if not n.get(f): errors.append(f'{nid}: missing {f}')
    if n.get('region') not in REGIONS: errors.append(f'{nid}: bad region {n.get("region")}')
    w = n.get('weight')
    if not isinstance(w,int) or not (1<=w<=10): errors.append(f'{nid}: bad weight {w}')
    for f in n.get('fields',[]):
        if f not in FIELDS: warnings.append(f'{nid}: unknown field {f}')
    src = n.get('source','')
    if src and not src.startswith('http'): warnings.append(f'{nid}: source not a URL: {src[:40]}')
    wd = n.get('wikidata','')
    if wd and not re.fullmatch(r'Q\d+', wd): errors.append(f'{nid}: bad wikidata id {wd}')
    ws = n.get('wikidata_src','')
    if ws not in ('', 'manual', 'auto-label', 'auto-alias'):
        errors.append(f'{nid}: bad wikidata_src {ws}')
    if wd and not ws:
        errors.append(f'{nid}: wikidata={wd} 但缺 wikidata_src（SCHEMA §6.2 要求成对出现）')
    if ws and not wd:
        errors.append(f'{nid}: wikidata_src={ws} 但无 wikidata')
    if n.get('verified') not in (None,'是','否'):
        errors.append(f'{nid}: bad verified {n.get("verified")}')
    for f in ('fields','aliases','uncertain'):
        if not isinstance(n.get(f,[]), list): errors.append(f'{nid}: {f} must be a list')

seen = set()
for l in d['links']:
    s, t, rel = l.get('s'), l.get('t'), l.get('rel')
    key = (s,t,rel)
    if key in seen: errors.append(f'duplicate edge: {s} -{rel}-> {t}')
    seen.add(key)
    if s not in ids or t not in ids:
        errors.append(f'dangling endpoint: {s} -> {t}'); continue
    if rel not in REL_RULES:
        errors.append(f'{s}->{t}: unknown rel {rel}'); continue
    ds, dt, wr = REL_RULES[rel]
    ts = next(n['type'] for n in d['nodes'] if n['id']==s)
    tt = next(n['type'] for n in d['nodes'] if n['id']==t)
    if ts not in ds: errors.append(f'{s}({ts}) -{rel}-> {t}: source type violation (allow {sorted(ds)})')
    if tt not in dt: errors.append(f'{s} -{rel}-> {t}({tt}): target type violation (allow {sorted(dt)})')
    if l.get('w') not in wr: errors.append(f'{s}->{t}: bad w {l.get("w")}')
    if l.get('verif') not in (None,'是','一致','否'):
        errors.append(f'{s}->{t}: bad verif {l.get("verif")}')
    for k in ('start','end'):
        v = l.get(k)
        if v and not re.fullmatch(r'\d{4}', str(v)): warnings.append(f'{s}->{t}: {k} not a year: {v}')

linked = set()
for l in d['links']: linked.add(l['s']); linked.add(l['t'])
iso = ids - linked
if iso: errors.append(f'isolated nodes: {sorted(iso)}')

print(f'nodes={len(d["nodes"])} links={len(d["links"])}')
print(f'ERRORS: {len(errors)}')
for e in errors: print('  E:', e)
print(f'WARNINGS: {len(warnings)}')
for w_ in warnings: print('  W:', w_)
sys.exit(1 if errors else 0)
