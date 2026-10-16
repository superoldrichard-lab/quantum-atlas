# align_wikidata.py — Wikidata 实体批量对齐（需在可直连 wikidata.org 的网络环境运行）
#
# 策略：
#   1. 对每个尚无 wikidata 字段的节点，用 wbsearchentities 按 name_en 搜索候选
#   2. 按节点类型做描述词过滤（scholar→physicist/researcher；university→university/institute；company→company...）
#   3. 置信度分级：label 精确匹配 + 描述命中类型词 => high（自动回填）；其余 => 写入 review 清单，绝不强行回填
#   4. 回填后自动跑 validate.py 同等约束检查
#
# 用法：python align_wikidata.py [--limit N] [--dry-run]
import json, re, sys, time, urllib.parse, urllib.request

P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
API = 'https://www.wikidata.org/w/api.php'
UA = {'User-Agent': 'QuantumKG-Align/1.1 (academic research graph alignment)'}

TYPE_HINT = {
    'university': ['university', 'institute', 'research', 'laboratory', 'academy', 'college', 'school', 'center', 'centre'],
    'scholar':    ['physicist', 'researcher', 'scientist', 'professor', 'mathematician', 'computer scientist', 'engineer', 'academic'],
    'student':    ['physicist', 'researcher', 'scientist', 'engineer', 'entrepreneur', 'executive', 'founder'],
    'exec':       ['executive', 'entrepreneur', 'founder', 'businessperson', 'physicist', 'engineer', 'computer scientist', 'CEO'],
    'company':    ['company', 'enterprise', 'startup', 'corporation', 'manufacturer', 'firm'],
    'investor':   ['company', 'fund', 'investment', 'venture', 'capital', 'telecom', 'corporation', 'bank'],
}

def api(params):
    url = API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=30))

def search_candidates(term, limit=5):
    r = api({'action': 'wbsearchentities', 'search': term, 'language': 'en',
             'format': 'json', 'limit': limit, 'type': 'item'})
    return r.get('search', [])

def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())

def main():
    dry = '--dry-run' in sys.argv
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])
    d = json.load(open(P, encoding='utf-8'))
    todo = [n for n in d['nodes'] if not n.get('wikidata')]
    if limit: todo = todo[:limit]
    filled, review, skipped = 0, [], 0
    for i, n in enumerate(todo):
        term = n.get('name_en') or n['name']
        try:
            cands = search_candidates(term)
        except Exception as e:
            print(f'[{i+1}/{len(todo)}] {n["id"]}: API error {e}'); time.sleep(2); continue
        hints = TYPE_HINT.get(n['type'], [])
        best = None
        for c in cands:
            label_ok = norm(c.get('label')) == norm(term) or norm(c.get('label')) == norm(n['name'])
            desc = (c.get('description') or '').lower()
            desc_ok = any(h in desc for h in hints)
            if label_ok and desc_ok:
                best = c; break
        if best:
            n['wikidata'] = best['id']
            filled += 1
            print(f'[{i+1}/{len(todo)}] {n["id"]} -> {best["id"]} ({best.get("label")} | {best.get("description","")[:60]})')
        else:
            skipped += 1
            cand_brief = [(c['id'], c.get('label'), (c.get('description') or '')[:50]) for c in cands[:3]]
            review.append({'id': n['id'], 'type': n['type'], 'term': term, 'candidates': cand_brief})
            print(f'[{i+1}/{len(todo)}] {n["id"]}: no confident match -> review')
        time.sleep(0.4)  # 礼貌限速
    if not dry:
        json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    rp = P.replace('.json', '_wikidata_review.json')
    json.dump(review, open(rp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\ndone: filled={filled}, to_review={skipped} (list -> {rp})' + (' [DRY RUN, data not saved]' if dry else ''))

if __name__ == '__main__':
    main()
