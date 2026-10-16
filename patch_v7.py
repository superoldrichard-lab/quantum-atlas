# patch_v7: Qolab/Aegiq/ParityQC/Qilimanjaro/Entropica/OrangeQS + 龙桂鲁/王向斌/Grangier/Lewenstein/Lechner/Martinis + Bpifrance
import json, io

P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
d = json.load(open(P, encoding='utf-8'))
ids = {n['id'] for n in d['nodes']}

new_nodes = [
 # ---- 高校 ----
 {"id":"u_sheffield","type":"university","name":"谢菲尔德大学","name_en":"University of Sheffield","country":"英国","region":"欧洲",
  "fields":["量子计算","量子通信"],"weight":5,
  "intro":"英国量子光子学研究重镇，半导体量子点单光子源方向有二十余年积累（Skolnick/Heffernan 团队），2019 年孵化 Aegiq。",
  "source":"https://www.aegiq.com"},
 {"id":"u_ucsb","type":"university","name":"加州大学圣塔芭芭拉分校","name_en":"UC Santa Barbara","country":"美国","region":"北美",
  "fields":["量子计算"],"weight":6,
  "intro":"John Martinis 组所在地，Google 2019 年量子优越性实验的超导处理器核心研发地，美国超导量子比特重镇。",
  "source":"https://forbes.com/sites/moorinsights/2026/07/21/qolab-wants-to-rewrite-the-rules-for-superconducting-quantum-hardware"},
 {"id":"u_ub","type":"university","name":"巴塞罗那大学","name_en":"Universitat de Barcelona","country":"西班牙","region":"欧洲",
  "fields":["量子计算"],"weight":4,
  "intro":"与巴塞罗那超算中心（BSC）、IFAE 联合孵化绝热量子公司 Qilimanjaro，西班牙量子计算学术一极。",
  "source":"https://www.qilimanjaro.tech"},
 # ---- 学者 ----
 {"id":"s_martinis","type":"scholar","name":"约翰·马蒂尼斯","name_en":"John Martinis","country":"美国","region":"北美",
  "fields":["量子计算"],"weight":9,"affiliation":"加州大学圣塔芭芭拉分校","dept":"物理系","title":"教授（现主职 Qolab CTO）",
  "intro":"超导量子比特先驱，领导 Google 团队实现 2019 年量子优越性，2025 年诺贝尔物理学奖得主，2022 年联合创立 Qolab 任 CTO。",
  "source":"https://forbes.com/sites/moorinsights/2026/07/21/qolab-wants-to-rewrite-the-rules-for-superconducting-quantum-hardware",
  "note":"UCSB 现职状态以学校官网为准"},
 {"id":"s_lechner","type":"scholar","name":"沃尔夫冈·莱希纳","name_en":"Wolfgang Lechner","country":"奥地利","region":"欧洲",
  "fields":["量子计算","量子软件与算法"],"weight":6,"affiliation":"因斯布鲁克大学","dept":"理论物理研究所","title":"教授",
  "intro":"Parity 量子优化架构提出者，将组合优化问题映射到平行局域相互作用，2020 年联合创立 ParityQC。",
  "source":"https://parityqc.com"},
 {"id":"s_lewenstein","type":"scholar","name":"马切伊·莱文斯坦","name_en":"Maciej Lewenstein","country":"西班牙","region":"欧洲",
  "fields":["量子计算"],"weight":7,"affiliation":"光子科学研究所（ICFO）","dept":"量子光学理论组","title":"ICREA 研究教授",
  "intro":"量子模拟与强场物理理论大家，ICFO 量子光学理论组组长，欧洲最高产的量子理论家之一。",
  "source":"https://www.icfo.eu"},
 {"id":"s_grangier","type":"scholar","name":"菲利普·格朗吉耶","name_en":"Philippe Grangier","country":"法国","region":"欧洲",
  "fields":["量子通信"],"weight":7,"affiliation":"巴黎-萨克雷高等光学学院（IOGS）/CNRS","dept":"Charles Fabry 实验室","title":"CNRS 研究主任/教授",
  "intro":"连续变量 QKD（CV-QKD）与量子光学实验先驱，欧洲量子通信实验早期主导者之一。",
  "source":"https://www.institutoptique.fr"},
 {"id":"s_longguilu","type":"scholar","name":"龙桂鲁","name_en":"Long Guilu","country":"中国","region":"中国",
  "fields":["量子通信"],"weight":7,"affiliation":"清华大学","dept":"物理系","title":"教授",
  "intro":"量子直接通信（QSDC）主要提出者，推动 QSDC 样机研制与城域组网试验，量子安全直接通信方向代表人物。",
  "source":"https://www.tsinghua.edu.cn"},
 {"id":"s_wangxiangbin","type":"scholar","name":"王向斌","name_en":"Wang Xiangbin","country":"中国","region":"中国",
  "fields":["量子通信"],"weight":7,"affiliation":"清华大学","dept":"物理系","title":"教授、济南量子技术研究院院长",
  "intro":"诱骗态方法与双场 QKD（TF-QKD）理论重要贡献者，「发送-不发送」协议提出者，QKD 实用化理论奠基人之一。",
  "source":"https://www.tsinghua.edu.cn"},
 # ---- 高管 ----
 {"id":"e_sich","type":"exec","name":"马克西姆·西奇","name_en":"Maksym Sich","country":"英国","region":"欧洲",
  "fields":["量子计算","量子通信"],"weight":3,"company":"Aegiq","title":"联合创始人兼 CEO",
  "intro":"谢菲尔德大学物理学博士（LSE 经济学本科），2019 年与 Dufferwiel 等共同创立 Aegiq。",
  "source":"https://www.aegiq.com"},
 # ---- 公司 ----
 {"id":"c_qolab","type":"company","name":"Qolab","name_en":"Qolab","country":"美国","region":"北美",
  "fields":["量子计算"],"weight":6,"founded":"2022","hq":"麦迪逊/圣塔芭芭拉（美国）",
  "funding":"累计约 7000 万美元（A 轮 1600 万 Octave 领投；2026-06 B 轮 5420 万 UC Investments 领投，应用材料等跟投）",
  "business":"以半导体制造工艺生产高相干超导量子比特与 QPU 整机",
  "intro":"Google 量子硬件负责人 Martinis 与产品负责人 Alan Ho 2022 年创立，用 300mm 半导体产线工艺解决量子比特良率与集成瓶颈，牵头 DARPA 量子基准计划（QBI）硬件开发。",
  "source":"https://forbes.com/sites/moorinsights/2026/07/21/qolab-wants-to-rewrite-the-rules-for-superconducting-quantum-hardware"},
 {"id":"c_aegiq","type":"company","name":"Aegiq","name_en":"Aegiq","country":"英国","region":"欧洲",
  "fields":["量子计算","量子通信"],"weight":4,"founded":"2019","hq":"谢菲尔德（英国）",
  "funding":"累计约 500 万英镑（High-Tech Gründerfonds 领投，Black Quant/Quantum Exponential 等跟投）",
  "business":"半导体量子点确定性单光子源、光量子计算与量子通信系统",
  "intro":"谢菲尔德大学 2019 年 12 月孵化，基于该校二十余年量子光子学积累，2025 年向英国国家量子计算中心（NQCC）交付光量子计算机。",
  "source":"https://www.aegiq.com"},
 {"id":"c_parityqc","type":"company","name":"ParityQC","name_en":"ParityQC","country":"奥地利","region":"欧洲",
  "fields":["量子软件与算法"],"weight":4,"founded":"2020","hq":"因斯布鲁克（奥地利）",
  "funding":"早中期风险投资","business":"Parity 架构量子优化软件、编译器与硬件蓝图授权",
  "intro":"因斯布鲁克大学 Lechner 组孵化，以 Parity 架构连接优化问题与多类量子硬件，与多家整机厂商合作。",
  "source":"https://parityqc.com"},
 {"id":"c_qili","type":"company","name":"Qilimanjaro Quantum Tech","name_en":"Qilimanjaro","country":"西班牙","region":"欧洲",
  "fields":["量子计算"],"weight":4,"founded":"2020","hq":"巴塞罗那（西班牙）",
  "funding":"早中期风险投资","business":"绝热/模拟量子计算（超导 flux 量子比特）与量子云服务",
  "intro":"巴塞罗那大学、巴塞罗那超算中心（BSC）与 IFAE 联合孵化，欧洲模拟/绝热量子计算代表企业，已交付相干量子退火系统。",
  "source":"https://www.qilimanjaro.tech"},
 {"id":"c_entropica","type":"company","name":"Entropica Labs","name_en":"Entropica Labs","country":"新加坡","region":"亚太及其他",
  "fields":["量子软件与算法"],"weight":3,"founded":"2018","hq":"新加坡",
  "funding":"早期风险投资","business":"量子算法、错误缓解与量子工作流软件",
  "intro":"新加坡量子软件公司，团队源自 CQT/新加坡科技设计大学生态，服务量子硬件与制药等应用客户。",
  "source":"https://www.entropicalabs.com"},
 {"id":"c_orangeqs","type":"company","name":"Orange Quantum Systems","name_en":"OrangeQS","country":"荷兰","region":"欧洲",
  "fields":["量子计算"],"weight":3,"founded":"2020","hq":"代尔夫特（荷兰）",
  "funding":"早期风险投资","business":"量子芯片自动化测试与表征设备",
  "intro":"代尔夫特 QuTech 生态孵化的量子芯片测试设备商，为超导/自旋量子比特产线提供自动化表征系统。",
  "source":"https://orangeqs.com"},
 # ---- 投资机构 ----
 {"id":"i_bpifrance","type":"investor","name":"法国公共投资银行","name_en":"Bpifrance","country":"法国","region":"欧洲",
  "fields":[],"weight":6,
  "intro":"法国主权背景公共投资银行，通过深科技基金重仓法国量子企业，Quobly 1.15 亿欧元 A 轮领投方。",
  "source":"https://www.bpifrance.com"},
]

new_links = [
 {"s":"u_sheffield","t":"c_aegiq","rel":"学校孵化","w":2,"note":"2019 年 12 月 spin-out"},
 {"s":"e_sich","t":"c_aegiq","rel":"任职/创办","w":3,"note":"联合创始人兼 CEO"},
 {"s":"e_sich","t":"u_sheffield","rel":"任职","w":1,"note":"物理学博士"},
 {"s":"s_martinis","t":"u_ucsb","rel":"任职","w":1,"unc":True,"note":"现主职 Qolab，UCSB 职务状态待核验"},
 {"s":"s_martinis","t":"c_qolab","rel":"任职/创办","w":3,"note":"联合创始人兼 CTO"},
 {"s":"u_wisc","t":"c_qolab","rel":"学校孵化","w":1,"unc":True,"note":"在 UW-Madison 孵化（WARF 参投）；硬件负责人 McDermott 为该校教授"},
 {"s":"s_lechner","t":"u_innsbruck","rel":"任职","w":2,"note":"理论物理研究所教授"},
 {"s":"s_lechner","t":"c_parityqc","rel":"任职/创办","w":3,"note":"联合创始人"},
 {"s":"u_innsbruck","t":"c_parityqc","rel":"学校孵化","w":2,"note":"2020 年 spin-off"},
 {"s":"u_ub","t":"c_qili","rel":"学校孵化","w":1,"note":"与 BSC、IFAE 联合孵化"},
 {"s":"s_lewenstein","t":"u_icfo","rel":"任职","w":2,"note":"ICREA 研究教授"},
 {"s":"s_grangier","t":"u_iqo","rel":"任职","w":2,"note":"Charles Fabry 实验室"},
 {"s":"s_longguilu","t":"u_tsinghua","rel":"任职","w":2,"note":"物理系教授"},
 {"s":"s_wangxiangbin","t":"u_tsinghua","rel":"任职","w":2,"note":"物理系教授；兼任济南量子技术研究院院长"},
 {"s":"u_nus","t":"c_entropica","rel":"学校孵化","w":1,"unc":True,"note":"团队源自 CQT/SUTD 生态，确切孵化关系待核验"},
 {"s":"u_delft","t":"c_orangeqs","rel":"学校孵化","w":1,"unc":True,"note":"QuTech/Delft 生态孵化"},
 {"s":"i_bpifrance","t":"c_quobly","rel":"投资/持股","w":1,"note":"2026-06 领投 1.15 亿欧元 A 轮"},
]

added_n = added_l = 0
for n in new_nodes:
    if n['id'] in ids:
        print('SKIP node (exists):', n['id']); continue
    d['nodes'].append(n); ids.add(n['id']); added_n += 1

existing_pairs = {(l['s'],l['t'],l['rel']) for l in d['links']}
for l in new_links:
    if l['s'] not in ids or l['t'] not in ids:
        print('SKIP link (missing endpoint):', l); continue
    if (l['s'],l['t'],l['rel']) in existing_pairs:
        print('SKIP link (dup):', l['s'], '->', l['t']); continue
    d['links'].append(l); added_l += 1

# sanity
bad = [l for l in d['links'] if l['s'] not in ids or l['t'] not in ids]
iso = [i for i in ids if not any(l['s']==i or l['t']==i for l in d['links'])]
json.dump(d, open(P,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'added nodes={added_n}, links={added_l} | total nodes={len(d["nodes"])}, links={len(d["links"])}')
print('bad endpoints:', len(bad), '| isolated:', iso)
