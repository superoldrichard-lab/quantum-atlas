# patch_v5: 补齐中国以外节点详细信息 —— 公司融资/估值/技术路线、学者实验室主页与院系、新增投资方
import json, io

P = r"D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json"
d = json.load(open(P, encoding="utf-8"))
by_id = {n["id"]: n for n in d["nodes"]}

# ---------- 1. 公司：融资字段精确化 + 简介重写（技术路线+融资/估值） ----------
UPD = {
 "c_quera": {
   "funding": "B 轮 2.3 亿美元（2025-02，Google 量子 AI 与软银愿景基金 2 联合领投；NVentures 2025-09 扩轮），累计约 2.5 亿美元",
   "intro": "哈佛/MIT 中性原子团队创立（Lukin/Greiner/Vuletic/Bernien），256 比特 Aquila 为首台公有云中性原子机，2025 年交付首台门模型系统 Gemini（日本 AIST，约 4000 万美元合同）；2025-02 完成 2.3 亿美元 B 轮，入选 DARPA 量子基准计划（QBI）B 阶段。"},
 "c_atom": {
   "funding": "C 轮 1 亿美元（2026-06），累计约 2 亿美元（公开报道）",
   "intro": "中性原子（锶-87 核自旋）量子计算公司，1180 物理比特系统与 40 秒相干时间纪录；与微软合作演示 24 个纠缠逻辑比特（2024-11），经 Azure Quantum 提供商用访问；2026-06 获 1 亿美元 C 轮。"},
 "c_infleqtion": {
   "funding": "已上市（NYSE: INFQ，2026-02 经 Churchill X SPAC 交割，投前估值 18 亿美元，募资超 5.5 亿美元）",
   "intro": "JILA 冷原子技术产业化旗舰（原 ColdQuanta），单一中性原子平台横跨量子计算（Sqale）、原子钟（Tiqker）与射频/惯性量子传感，客户含 NASA、英美政府；2026-02 上市，为全球首家上市中性原子公司。"},
 "c_psiquantum": {
   "funding": "E 轮 10 亿美元（2025-09，估值 70 亿美元，BlackRock/淡马锡/Baillie Gifford 领投，NVentures 等跟投），累计超 18 亿美元",
   "intro": "布里斯托光量子团队创立，跳过 NISQ 直攻百万比特容错光量子计算机，芯片由 GlobalFoundries 代工；2025-09 完成 10 亿美元 E 轮、估值 70 亿美元，布里斯班（2027）与芝加哥（2028）两地整机在建。"},
 "c_qm": {
   "funding": "C 轮 1.7 亿美元（2025-02，PSG 领投，Intel Capital 等跟投），累计 2.8 亿美元，估值约 6.7 亿美元",
   "intro": "魏茨曼孵化的量子测控系统龙头，OPX 控制器 + QUA 语言被全球过半量子公司与实验室采用；与英伟达合作 DGX Quantum 量子-经典混合架构；2025-02 获 1.7 亿美元 C 轮。"},
 "c_quantinuum": {
   "funding": "已上市（Nasdaq: QNT，2026-06 IPO 募资 16.8 亿美元）；上市前 2025-09 获 6 亿美元融资，投前估值 100 亿美元",
   "intro": "由霍尼韦尔量子部门与剑桥量子计算（CQC）2021 年合并而成，H 系列离子阱机保持量子体积纪录，TKET 编译栈与量子化学/密码软件全栈布局；2025-09 融资 6 亿美元（投前估值 100 亿美元），2026-06 IPO，为全球估值最高的量子公司之一。"},
 "c_xanadu": {
   "funding": "已上市（2026-03 完成与 Crane Harbor 的 SPAC 合并，交易估值 36 亿美元，募资约 3 亿美元）",
   "intro": "光量子计算公司，Borealis 演示高斯玻色采样优势，PennyLane 为量子机器学习事实标准框架；2025-11 宣布 SPAC 合并（估值 36 亿美元），2026-03 完成上市，推进容错光量子路线图。"},
 "c_iqm": {
   "funding": "已上市（Nasdaq: IQMX，2026-07 SPAC）；上市前 2025-09 完成 3.2 亿美元 B 轮（估值约 10 亿美元）",
   "intro": "2018 年 Aalto/VTT 孵化的欧洲超导整机龙头（Goetz、Möttönen 等四人联创），Spark/Resonance 系列已向 13 家客户交付 15 套系统（含欧洲多国超算中心）；2026-07 经 SPAC 上市，为欧洲首家上市量子硬件公司。"},
 "c_quandela": {
   "funding": "B 轮 5000 万欧元（2023-11，Omnes/Quantonation/Bpifrance 等，公开报道）",
   "intro": "CNRS C2N 孵化（Senellart 联合创立），确定性量子点单光子源全球领先，已交付 6 比特光量子机 MosaiQ 并接入欧洲量子云；2023-11 获 5000 万欧元 B 轮。"},
 "c_pasqal": {
   "funding": "B 轮约 1 亿欧元（2023，淡马锡领投）；2026-03 宣布与 Bleichroeder II 的 SPAC 合并（投前估值约 20 亿美元，预计 2026 下半年交割）",
   "intro": "Institut d'Optique 孵化的中性原子公司（Browaeys 联合创立，Aspect 任科学顾问），200+ 比特系统交付法德 HPC 中心，欧洲量子计算旗舰；2026-03 宣布以约 20 亿美元投前估值经 SPAC 上市。"},
 "c_alicebob": {
   "funding": "B 轮 1 亿欧元（2025-01，公开报道）",
   "intro": "ENS 孵化（Peronnin 联合创立）的猫量子比特公司，以硬件层偏置噪声比特将容错开销压缩数个量级，与 Bull/Atos 合作交付系统；2025-01 获 1 亿欧元 B 轮（Bpifrance、AXA Venture Partners 等）。"},
 "c_oqc": {
   "funding": "B 轮 1 亿美元（2023-11，SBI 领投，Chevron 2024 跟投），累计超 1.5 亿美元",
   "intro": "牛津超导量子计算孵化企业（Leek 创立、Wisby 任 CEO），coaxmon 三维架构；Toshiko 32 比特系统部署商用数据中心，英国首家 QCaaS 公司；2023 年 B 轮为英国量子公司最大轮次之一。"},
 "c_phasecraft": {
   "funding": "B 轮 3400 万美元（2025，Plural/Playground Global/Novo 量子基金联合领投），累计超 5000 万美元",
   "intro": "UCL 与布里斯托量子算法团队共同创立（Montanaro/Cubitt/Morton），聚焦量子化学与材料模拟算法的实用化压缩；2025 年获 3400 万美元 B 轮。"},
 "c_quantum_motion": {
   "funding": "B 轮 4200 万英镑（2023-02，Bosch Ventures/Porsche SE/British Patient Capital 等，公开报道）",
   "intro": "UCL 孵化（Morton 联合创立），用标准 CMOS 工艺制造硅量子点芯片，2022 年交付首台硅基整机 Bloomsbury；2023-02 获 4200 万英镑 B 轮。"},
 "c_universal_quantum": {
   "funding": "风险投资 + 德国宇航中心（DLR）6700 万欧元研制合同（2023，公开报道）",
   "intro": "萨塞克斯大学孵化（Hensinger 创立，Weidt 任 CEO），微波操控 + 电场互连模块的百万比特离子阱架构；2023 年获 DLR 6700 万欧元合同建造两台离子阱量子计算机。"},
 "c_orca": {
   "funding": "A 轮 1500 万美元（2022，公开报道）",
   "intro": "牛津孵化（Walmsley/Nunn 联合创立），以量子存储复用架构降低光量子硬件复杂度，PT 系列光量子系统已交付多国超算与国防用户。"},
 "c_qctrl": {
   "funding": "B 轮及多轮扩展（累计约 1 亿美元级，公开报道口径不一）",
   "intro": "悉尼大学孵化（Biercuk 创立），量子控制基础设施软件开创者，Boulder Opal/Fire Opal 被主流硬件商与实验室集成，并拓展量子导航传感；空客、Salesforce 等为产业投资方。",
   "unc": "累计融资金额各家报道口径不一（约 1 亿美元级）"},
 "c_sqc": {
   "funding": "A 轮 5000 万澳元（2023，估值 1.95 亿澳元）；2026-03 获澳国家重建基金（NRF）2000 万澳元",
   "intro": "UNSW/CQC2T 孵化（Simmons 创立），原子级精度制造硅量子比特，创立时获政府/Telstra/CBA/UNSW 共 8300 万澳元；产品 Watermelon（量子机器学习）与 Quantum Twins（材料模拟）已商用；入选 DARPA QBI B 阶段。"},
 "c_diraq": {
   "funding": "A 轮累计约 7500 万澳元（含 2026-02 澳 NRF 2000 万澳元，公开报道）",
   "intro": "UNSW 孵化（Dzurak 创立），硅 MOS 量子点量子比特，主打与 CMOS 产线完全兼容的制造路线，计划 2029 年推出首款产品；入选 DARPA QBI。"},
 "c_qb": {
   "funding": "A 轮约 3000 万美元（2024，公开报道）",
   "intro": "ANU 孵化，金刚石 NV 色心室温量子计算路线，机架式量子加速卡进入 Pawsey 等超算中心试点，兼顾量子传感；获澳政府与 Main Sequence 等投资。",
   "unc": "A 轮具体金额来自第三方数据库报道，未经公司公告核验"},
 "c_speqtral": {
   "funding": "A 轮 830 万美元（2022，Xora/淡马锡系领投，公开报道）",
   "intro": "NUS 量子科技中心（CQT）孵化的卫星 QKD 公司（Bedington 联合创立），继承 SpooQy-1 立方星技术，2025 年发射 SpeQtral-1 卫星，与 SES 等合作构建星地量子网络。"},
 "c_kets": {
   "funding": "早期（累计约 550 万英镑 + Innovate UK SBRI 项目，公开报道）",
   "intro": "布里斯托大学孵化的芯片级 QKD 公司，将量子密钥分发集成到光子芯片以降低成本；QKD 原型正与英国电信（BT）联合测试。"},
 "c_qnami": {
   "funding": "A 轮约 440 万美元（2021，公开报道）",
   "intro": "巴塞尔大学孵化的量子传感公司，ProteusQ 扫描 NV 显微镜用于纳米磁成像与材料表征，是高校量子传感技术转化的欧洲样本。",
   "unc": "A 轮金额来自公开报道，未经公司公告核验"},
 "c_photonicinc": {
   "funding": "B 轮 1 亿美元（2024-09，微软/BDC 等，投后估值约 5 亿美元，公开报道）",
   "intro": "SFU 孵化（Stephanie Simmons 联合创立），硅自旋-光子接口（T 中心）路线，与微软合作分布式容错量子计算；2024-09 获 1 亿美元 B 轮。"},
 "c_oxford_ionics": {
   "funding": "成长期风险投资；2025-06 IonQ 宣布以约 11 亿美元收购",
   "intro": "牛津孵化的电子控制离子阱公司（Ballance/Harty 创立），保持量子门保真度多项世界纪录；2025-06 IonQ 宣布以约 11 亿美元收购，并入其离子阱路线图。"},
 "c_horizon": {
   "funding": "已上市（2026-03 完成与 dMY Squared 的 SPAC 合并，交易规模 5.03 亿美元，代码 HQ）",
   "intro": "Fitzsimons（CQT/SUTD）创立，开发从经典代码自动合成量子程序的编译工具链；2026-03 经 SPAC 上市（代码 HQ），为新加坡首家上市量子公司。"},
 "c_qci": {
   "funding": "风险投资（多轮，金额未完整公开）",
   "intro": "耶鲁正式技术转移企业（Schoelkopf/Devoret 创立），主打双轨腔（dual-rail cavity）量子比特的内建纠错路线，是 cQED 学派最直接的产业化载体。"},
}

for cid, u in UPD.items():
    n = by_id[cid]
    n["funding"] = u["funding"]
    n["intro"] = u["intro"]
    if u.get("unc"):
        n.setdefault("uncertain", [])
        if u["unc"] not in n["uncertain"]:
            n["uncertain"].append(u["unc"])

# ---------- 2. 学者：实验室主页（仅填确信的官网） ----------
LAB = {
 "s_lukin": "https://lukin.physics.harvard.edu",
 "s_greiner": "https://greiner.physics.harvard.edu",
 "s_vuletic": "https://cua.mit.edu",
 "s_monroe": "https://jqi.umd.edu",
 "s_kim": "https://ionq.com",
 "s_schoelkopf": "https://quantuminstitute.yale.edu",
 "s_devoret": "https://quantuminstitute.yale.edu",
 "s_martinis": "https://qolab.ai",
 "s_kimble": "https://iqim.caltech.edu",
 "s_houck": "https://quantum.princeton.edu",
 "s_siddiqi": "https://qnl.berkeley.edu",
 "s_awschalom": "https://chicagoquantum.org",
 "s_bernien": "https://pme.uchicago.edu",
 "s_zeilinger": "https://quantum.at",
 "s_hanson": "https://qutech.nl",
 "s_vandersypen": "https://qutech.nl",
 "s_groblacher": "https://qutech.nl",
 "s_blatt": "https://quantumoptics.at",
 "s_zoller": "https://www.iqoqi.at",
 "s_cirac": "https://www.mpq.mpg.de",
 "s_bloch": "https://www.quantum-munich.de",
 "s_ekert": "https://www.quantumlah.org",
 "s_gisin": "https://www.unige.ch/gap",
 "s_loss": "https://quantumtheory.physik.unibas.ch",
 "s_lodahl": "https://www.quantum-photonics.dk",
 "s_leek": "https://oqc.tech",
 "s_biercuk": "https://q-ctrl.com",
 "s_simmons": "https://www.cqc2t.org",
 "s_morello": "https://www.cqc2t.org",
 "s_dzurak": "https://diraq.com.au",
 "s_doherty": "https://quantumbrilliance.com",
 "s_nakamura": "https://rqc.riken.jp/en/",
 "s_vazirani": "https://www.cs.berkeley.edu/~vazirani",
 "s_obrien": "https://www.psiquantum.com",
 "s_rudolph": "https://www.psiquantum.com",
 "s_montanaro": "https://phasecraft.io",
 "s_cubitt": "https://phasecraft.io",
 "s_hensinger": "https://universalquantum.com",
 "s_mosca": "https://evolutionq.com",
 "s_browaeys": "https://www.pasqal.com",
 "s_fitzsimons": "https://horizonquantum.com",
 "s_delsing": "https://wacqt.se",
 "s_wehner": "https://qutech.nl",
 "s_wunderlich": "https://eleqtron.com",
 "s_mottonen": "https://qcd.aalto.fi",
 "s_senellart": "https://www.c2n.universite-paris-saclay.fr",
 "st_rigetti": "https://rigetti.com",
 "st_weedbrook": "https://www.xanadu.ai",
 "st_ballance": "https://www.oxionics.com",
 "st_zeiher": "https://planqc.eu",
 "st_bedington": "https://speqtral.com",
 "st_peronnin": "https://alice-bob.com",
}
filled_lab = 0
for sid, url in LAB.items():
    n = by_id[sid]
    if not n.get("lab"):
        n["lab"] = url
        filled_lab += 1

# ---------- 3. 学者：院系补缺 ----------
DEPT = {
 "s_hanson": "QuTech / Kavli 纳米科学研究所",
 "s_vandersypen": "QuTech / Kavli 纳米科学研究所",
 "s_ekert": "数学研究所（牛津）/ CQT（NUS）",
 "s_simmons": "CQC2T / 物理学院",
 "s_nakamura": "量子计算研究中心（RQC）",
 "s_yamamoto": "NTT 基础科学实验室（NTT Research PHI Lab）",
 "s_browaeys": "Institut d'Optique / CNRS",
 "s_aspect": "Institut d'Optique（名誉教授）",
 "st_zeiher": "MPQ / LMU（组长、教授）",
}
for sid, dept in DEPT.items():
    n = by_id[sid]
    if not n.get("dept"):
        n["dept"] = dept

# ---------- 4. 新增投资方节点 ----------
NEW_NODES = [
 {"id":"i_google","type":"investor","name":"Google（量子 AI）","name_en":"Google Quantum AI","country":"美国","region":"北美",
  "fields":["量子计算"],"weight":7,"intro":"Google 量子 AI 部门以战略投资方身份于 2025-02 联合领投 QuEra 2.3 亿美元 B 轮，在自身超导路线之外对冲布局中性原子路线；亦为 SandboxAQ 等量子公司的投资方。",
  "source":"https://quera.com/press-releases/quera-completes-230m-financing","note":"","uncertain":[],"founded":"","hq":"Mountain View","funding":"","business":""},
 {"id":"i_softbank","type":"investor","name":"软银愿景基金","name_en":"SoftBank Vision Fund","country":"日本","region":"亚太及其他",
  "fields":["量子计算"],"weight":6,"intro":"软银愿景基金 2 期于 2025-02 联合领投 QuEra 2.3 亿美元 B 轮，为日本资本切入全球量子计算核心资产的标志性案例。",
  "source":"https://quera.com/press-releases/quera-completes-230m-financing","note":"","uncertain":[],"founded":"","hq":"东京","funding":"","business":""},
 {"id":"i_nrf","type":"investor","name":"澳大利亚国家重建基金","name_en":"National Reconstruction Fund (NRF)","country":"澳大利亚","region":"亚太及其他",
  "fields":["量子计算"],"weight":5,"intro":"澳联邦政府 150 亿澳元产业基金，2026 年先后向 Diraq 与 SQC 各注资 2000 万澳元，为澳大利亚量子双子星的重要国资股东。",
  "source":"https://www.smartcompany.com.au/startupsmart/silicon-quantum-computing-nrf-20-million/","note":"","uncertain":[],"founded":"","hq":"堪培拉","funding":"","business":""},
]
for nn in NEW_NODES:
    nn.setdefault("affiliation",""); nn.setdefault("dept",""); nn.setdefault("title",""); nn.setdefault("lab","")
    if nn["id"] in by_id:
        print("SKIP dup node", nn["id"]); continue
    d["nodes"].append(nn); by_id[nn["id"]] = nn

# 更新英伟达简介（现 4 笔量子投资）
by_id["i_nvidia"]["intro"] = "系统性投资量子计算多条路线：2025-09 首次投资 Quantinuum（离子阱）、跟投 PsiQuantum 10 亿美元 E 轮（光量子）、跟投 QuEra 2.3 亿美元 B 轮扩轮（中性原子），并以 NVAQC 加速量子研究中心构建量子-GPU 混合生态。"

# ---------- 5. 新增投资/持股边 ----------
NEW_LINKS = [
 {"s":"i_google","t":"c_quera","rel":"投资/持股","w":2,"note":"2025-02 联合领投 2.3 亿美元 B 轮"},
 {"s":"i_softbank","t":"c_quera","rel":"投资/持股","w":2,"note":"2025-02 联合领投 2.3 亿美元 B 轮"},
 {"s":"i_nvidia","t":"c_quera","rel":"投资/持股","w":2,"note":"2025-09 跟投扩轮（NVentures）"},
 {"s":"i_blackrock","t":"c_psiquantum","rel":"投资/持股","w":2,"note":"2025-09 联合领投 10 亿美元 E 轮"},
 {"s":"i_temasek","t":"c_psiquantum","rel":"投资/持股","w":2,"note":"2025-09 联合领投 10 亿美元 E 轮"},
 {"s":"i_nrf","t":"c_sqc","rel":"投资/持股","w":2,"note":"2026-03 注资 2000 万澳元（SAFE）"},
 {"s":"i_nrf","t":"c_diraq","rel":"投资/持股","w":2,"note":"2026-02 注资 2000 万澳元"},
]
existing = {(l["s"],l["t"],l["rel"]) for l in d["links"]}
for l in NEW_LINKS:
    assert l["s"] in by_id and l["t"] in by_id, l
    if (l["s"],l["t"],l["rel"]) in existing:
        print("SKIP dup link", l); continue
    d["links"].append(l)

json.dump(d, open(P,"w",encoding="utf-8"), ensure_ascii=False, indent=1)

# 校验
ids = {n["id"] for n in d["nodes"]}
bad = [l for l in d["links"] if l["s"] not in ids or l["t"] not in ids]
iso = [i for i in ids if not any(l["s"]==i or l["t"]==i for l in d["links"])]
no_intro = [n["id"] for n in d["nodes"] if not n.get("intro")]
from collections import Counter
print("nodes:", len(d["nodes"]), dict(Counter(n["type"] for n in d["nodes"])))
print("links:", len(d["links"]))
print("bad:", len(bad), "| isolated:", iso, "| no_intro:", no_intro)
print("lab filled:", filled_lab)
vague = [n["id"] for n in d["nodes"] if n["type"]=="company" and n.get("country")!="中国" and n.get("funding") in ("风险投资","早期风险投资","早中期风险投资","成长期风险投资","政府与产业资本注资")]
print("still vague funding:", vague)
missing_lab = [n["id"] for n in d["nodes"] if n["type"] in ("scholar","student") and n.get("country")!="中国" and not n.get("lab")]
print("scholars still missing lab:", len(missing_lab), missing_lab)
