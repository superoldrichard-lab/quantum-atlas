# -*- coding: utf-8 -*-
"""v4 数据补丁：新增企业创始人/高管(exec)与投资机构(investor)节点；
   更新国内公司技术路线/融资估值简介"""
import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
d = json.load(open(P, encoding='utf-8'))
ids = {n['id'] for n in d['nodes']}
edge_keys = {(l['s'], l['t'], l['rel']) for l in d['links']}

# ---------- 1. 更新既有公司节点（技术路线 + 融资/估值） ----------
updates = {
 "c_origin": {
   "funding": "Pre-IPO 轮近 30 亿元（2026 年，投前估值 210 亿元）",
   "intro": "郭光灿、郭国平 2017 年创立，中国第一家量子计算企业。技术路线：超导+半导体双路线全栈，第四代整机“本源悟空-180”（180 计算比特）2026 年 5 月上线。融资：2021 中网投领投 A 轮、2022 深创投领投近 10 亿 B 轮、2026 中兵集团领投 Pre-IPO 近 30 亿元（投前估值 210 亿元），2025-09 已科创板 IPO 辅导备案。",
   "source": "https://stock.10jqka.com.cn/20260608/c677274983.shtml"},
 "c_turingq": {
   "funding": "战略轮（2025 年，估值超 70 亿元，累计 8 轮超 10 亿元）",
   "intro": "金贤敏 2021 年创立，上海交大知识产权作价入股。技术路线：光量子计算——飞秒激光直写三维光子芯片+铌酸锂薄膜（LNOI）光子芯片，建有国内首条光子芯片中试线。融资：联想之星领投天使轮，君联资本、中网投、盛世投资等累计 8 轮超 10 亿元，2025 年估值超 70 亿元。",
   "source": "https://so.html5.qq.com/page/real/search_news?docid=70000021_10669eebe1472952"},
 "c_boseq": {
   "funding": "A++ 轮（2025-10，数亿元，华德科创/南山战新投联合领投）",
   "intro": "文凯、马寅 2020 年创立。技术路线：相干光量子计算——1000 专用量子比特相干伊辛机（专用）+ 通用光量子（长期）双轨布局，在深圳南山建设规模化专用光量子计算机制造工厂。融资：2025-10 完成数亿元 A++ 轮，华德科创、南山战新投联合领投，啟赋资本等老股东加码。",
   "source": "https://www.news.cn/digital/20251015/b6023ec32a0e4ce7b858836fd53695d9/c.html"},
 "c_huayi": {
   "funding": "A+ 轮（2026-05，建投投资领投；累计融资超 5 亿元）",
   "source": "https://hyqubit.com/newsinfo/11254213.html",
   "intro": "段路明、姚麟 2022 年创立，清华大学量子信息中心孵化。技术路线：离子阱量子计算，全球首创二维离子阵列架构（理论可承载上万比特）；HYQ-A37（37 比特，2023）、HYQ-B100（100+ 比特，2024，已交付中国移动研究院）。融资：高榕资本领投天使轮，央视融媒体基金领投 Pre-A，2025-07 数亿元 A 轮（社保基金、北京国资加码），2026-05 建投投资领投 A+ 轮，累计超 5 亿元。",
   "uncertain": []},
 "c_quantumctek": {
   "funding": "已上市（科创板 688027，2020-07；2025-01 起中电信量子集团控股）",
   "intro": "潘建伟、彭承志团队 2009 年创立，“量子科技第一股”。技术路线：量子保密通信（QKD）为主业，拓展超导量子计算（“祖冲之”系列协作与稀释制冷机等核心设备）与量子精密测量（单光子雷达、冷原子重力仪）。2025-01 中电信量子集团成为控股股东（直接持股 21.86%，合计表决权 40.43%），实控人变更为国务院国资委。"},
 "c_ciqtek": {
   "funding": "已上市（科创板 688828，2026-08-11，上市总市值约 441 亿元）",
   "intro": "杜江峰团队贺羽 2016 年创立，源于中科院微观磁共振重点实验室。技术路线：量子精密测量与高端科学仪器——电子顺磁共振（EPR）波谱仪、扫描 NV 探针显微镜、场发射电镜等，多项指标达到或超越国际竞品。融资：高瓴创投领投 B 轮并两度加注，基石资本、同创伟业、国风投、中科院资本等入股；2026-08 登陆科创板，市值约 441 亿元，2026 上半年营收增长 51%。",
   "source": "https://www.stcn.com/article/detail/4070211.html"},
 "c_iqm": {
   "funding": "已上市（Nasdaq: IQMX，2026-07 SPAC 上市；上市前私募融资超 6 亿美元）",
   "intro": "2018 年由 Aalto 大学与芬兰 VTT 孵化（Goetz、Möttönen、Tan、Vartiainen 四人联合创立），欧洲超导量子计算整机龙头，自建芯片产线。融资：2022 年 World Fund 领投 1.28 亿欧元 A2 轮（腾讯、Tesi 等跟投），2025-09 Ten Eleven 领投超 3 亿美元 B 轮，2026-07 经 SPAC 登陆纳斯达克（估值约 18 亿美元）。",
   "source": "https://datadeep.tech/iqm-quantum-computers-iqmx"},
 "c_wentian": {
   "intro": "郭光灿、韩正甫 2009 年创立的中国第一家量子信息产业化企业，由芜湖投控与中科大共同发起。技术路线：量子保密通信（城域 QKD 网络、QKD 设备）+ 量子随机数芯片，牵头量子密码行业标准制定。融资：2026-07 完成 6 亿元 B 轮（中天汇富、合凡资产、延福基金等），地方后备上市企业。"},
}
n_by_id = {n['id']: n for n in d['nodes']}
for nid, u in updates.items():
    n_by_id[nid].update(u)

# ---------- 2. 新增节点 ----------
new_nodes = [
 # ---- 学者补充 (+2) ----
 {"id":"s_mottonen","type":"scholar","name":"米科·默特宁","name_en":"Mikko Möttönen","country":"芬兰","region":"欧洲","fields":["量子计算"],"affiliation":"阿尔托大学","dept":"应用物理系","title":"教授 / IQM 首席科学家","source":"https://datadeep.tech/iqm-quantum-computers-iqmx","intro":"阿尔托大学教授，量子器件组负责人，IQM 四位联合创始人之一、首席科学家，超导量子比特复位与读出技术先驱。","weight":6},
 {"id":"s_senellart","type":"scholar","name":"帕斯卡尔·塞内拉尔","name_en":"Pascale Senellart","country":"法国","region":"欧洲","fields":["量子计算","量子通信"],"affiliation":"CNRS / 巴黎-萨克雷（C2N）","dept":"纳米科学与技术中心（C2N）","title":"CNRS 研究主任 / Quandela 联合创始人","source":"https://www.quandela.com/","intro":"半导体量子点单光子源领域权威，Quandela 联合创始人，法国 CNRS 银质奖章得主。","weight":6,"uncertain":["任职机构表述（C2N 隶属 CNRS/巴黎-萨克雷）待核验"]},
 # ---- 企业创始人/高管 exec (+15) ----
 {"id":"x_khan","type":"exec","name":"伊利亚斯·汗","name_en":"Ilyas Khan","country":"英国","region":"欧洲","fields":["量子计算"],"affiliation":"Quantinuum","title":"创始人（CQC）/ 首席产品官、副董事长","source":"https://www.quantinuum.com/press-releases/introducing-quantinuum","intro":"2014 年经剑桥 Accelerate 项目创立 Cambridge Quantum，2021 年主导与霍尼韦尔量子部门合并为 Quantinuum。","weight":6},
 {"id":"x_goetz","type":"exec","name":"扬·格茨","name_en":"Jan Goetz","country":"芬兰","region":"欧洲","fields":["量子计算"],"affiliation":"IQM Quantum Computers","title":"联合创始人 / CEO","source":"https://www.meetiqm.com","intro":"IQM 联合创始人兼 CEO（2026 年起单独出任），Aalto 博士，主导公司经 SPAC 登陆纳斯达克。","weight":5},
 {"id":"x_reymond","type":"exec","name":"乔治-奥利维耶·雷蒙","name_en":"Georges-Olivier Reymond","country":"法国","region":"欧洲","fields":["量子计算"],"affiliation":"Pasqal","title":"联合创始人 / CEO","source":"https://www.pasqal.com","intro":"Pasqal 联合创始人兼 CEO，将 Browaeys 组中性原子光镊技术产业化。","weight":5},
 {"id":"x_ribordy","type":"exec","name":"格雷瓜尔·里博迪","name_en":"Grégoire Ribordy","country":"瑞士","region":"欧洲","fields":["量子通信"],"affiliation":"ID Quantique","title":"联合创始人 / CEO","source":"https://www.idquantique.com","intro":"IDQ 联合创始人兼 CEO，日内瓦大学博士，全球量子保密通信产业化先驱。","weight":5},
 {"id":"x_bloom","type":"exec","name":"本·布鲁姆","name_en":"Ben Bloom","country":"美国","region":"北美","fields":["量子计算"],"affiliation":"Atom Computing","title":"创始人 / CEO","source":"https://atom-computing.com","intro":"Atom Computing 创始人兼 CEO，中性原子（核自旋量子比特）路线，曾宣布千比特级系统。","weight":5},
 {"id":"x_rose","type":"exec","name":"乔迪·罗斯","name_en":"Geordie Rose","country":"加拿大","region":"北美","fields":["量子计算"],"affiliation":"D-Wave Systems","title":"创始人","source":"https://www.dwavesys.com","intro":"D-Wave 创始人（1999），量子退火商业化第一人，曾任 CEO/CTO，现专注机器人智能等新创业。","weight":5,"uncertain":["现任 D-Wave 职务状态待核验"]},
 {"id":"x_sivan","type":"exec","name":"伊塔马尔·西万","name_en":"Itamar Sivan","country":"以色列","region":"亚太及其他","fields":["量子计算"],"affiliation":"Quantum Machines","title":"联合创始人 / CEO","source":"https://www.quantum-machines.co","intro":"Quantum Machines 联合创始人兼 CEO，魏茨曼研究所博士，量子测控系统（OPX）赛道开创者。","weight":5},
 {"id":"x_wisby","type":"exec","name":"伊拉娜·维斯比","name_en":"Ilana Wisby","country":"英国","region":"欧洲","fields":["量子计算"],"affiliation":"Oxford Quantum Circuits","title":"创始人（首任 CEO）","source":"https://oqc.tech","intro":"OQC 创始人，牛津大学量子物理博士，将 Leek 组 coaxmon 三维超导架构产业化。","weight":4,"uncertain":["现任 OQC 职务状态待核验"]},
 {"id":"x_shadbolt","type":"exec","name":"皮特·沙德博尔特","name_en":"Pete Shadbolt","country":"美国","region":"北美","fields":["量子计算"],"affiliation":"PsiQuantum","title":"联合创始人 / 首席科学官","source":"https://www.psiquantum.com","intro":"PsiQuantum 四位联合创始人之一，布里斯托尔大学博士（O'Brien 组），光量子容错计算路线核心设计者。","weight":5},
 {"id":"x_brierley","type":"exec","name":"史蒂夫·布赖尔利","name_en":"Steve Brierley","country":"英国","region":"欧洲","fields":["量子软件与算法"],"affiliation":"Riverlane","title":"创始人 / CEO","source":"https://www.riverlane.com","intro":"Riverlane 创始人兼 CEO，量子纠错（QEC）工程化领军人物，曾长期在剑桥从事量子信息研究。","weight":4},
 {"id":"x_weidt","type":"exec","name":"塞巴斯蒂安·韦特","name_en":"Sebastian Weidt","country":"英国","region":"欧洲","fields":["量子计算"],"affiliation":"Universal Quantum","title":"联合创始人 / CEO","source":"https://universalquantum.com","intro":"Universal Quantum 联合创始人兼 CEO，萨塞克斯大学离子阱模块互联技术产业化负责人。","weight":4},
 {"id":"x_yaolin","type":"exec","name":"姚麟","name_en":"Yao Lin","country":"中国","region":"中国","fields":["量子计算"],"affiliation":"华翊量子","title":"联合创始人 / 董事长兼 CEO","source":"https://hyqubit.com/newsinfo/11254213.html","intro":"华翊量子联合创始人、董事长兼 CEO，曾在美国布鲁克海文国家实验室及商业公司多年，负责公司工程化与商业化。","weight":5},
 {"id":"x_mayin","type":"exec","name":"马寅","name_en":"Ma Yin","country":"中国","region":"中国","fields":["量子计算"],"affiliation":"玻色量子","title":"联合创始人","source":"https://www.news.cn/digital/20251015/b6023ec32a0e4ce7b858836fd53695d9/c.html","intro":"玻色量子联合创始人，与文凯共同主导相干光量子计算专用机产业化。","weight":4,"uncertain":["教育背景与具体职务分工待核验"]},
 {"id":"x_palacios","type":"exec","name":"卡门·帕拉西奥斯","name_en":"Carmen Palacios-Berraquero","country":"英国","region":"欧洲","fields":["量子通信"],"affiliation":"Nu Quantum","title":"创始人 / CEO","source":"https://www.nu-quantum.com","intro":"Nu Quantum 创始人兼 CEO，剑桥大学博士，量子网络互连（QNU）方向创业者。","weight":4,"uncertain":["博士学位授予院校待核验"]},
 {"id":"x_nunn","type":"exec","name":"乔什·纳恩","name_en":"Josh Nunn","country":"英国","region":"欧洲","fields":["量子计算"],"affiliation":"ORCA Computing","title":"联合创始人 / CSO","source":"https://orcacomputing.com","intro":"ORCA 联合创始人，牛津大学量子存储（量子内存）技术产业化负责人。","weight":4},
 # ---- 投资机构 investor (+21) ----
 {"id":"i_chinatelecom","type":"investor","name":"中国电信集团","name_en":"China Telecom","country":"中国","region":"中国","intro":"央企三大运营商之一，经中电信量子集团（全资）布局量子通信/计算/测量全栈，2025 年起成为国盾量子实际控制人链条顶端。","weight":8,"source":"https://ah.people.com.cn/n2/2025/1123/c227767-41420270.html"},
 {"id":"i_honeywell","type":"investor","name":"霍尼韦尔","name_en":"Honeywell","country":"美国","region":"北美","intro":"Quantinuum 最大股东（合并时约 54%，IPO 后保留约 48% 表决权），H 系列离子阱硬件技术来源方。","weight":7,"source":"https://www.honeywell.com/us/en/press/2021/11/honeywell-quantum-solutions-and-cambridge-quantum-complete-business-combination-to-form-world-s-largest-most-advanced-standalone-quantum-company"},
 {"id":"i_jpmorgan","type":"investor","name":"摩根大通","name_en":"JPMorgan Chase","country":"美国","region":"北美","intro":"2024 年 1 月领投 Quantinuum 3 亿美元股权轮融资，同时是量子金融应用的重要用户方。","weight":6,"source":"https://www.quantinuum.com"},
 {"id":"i_nvidia","type":"investor","name":"英伟达（NVentures）","name_en":"NVIDIA / NVentures","country":"美国","region":"北美","intro":"系统性投资量子计算多条路线：2025-09 首次投资 Quantinuum（离子阱），另投资 PsiQuantum（光量子）与 QuEra（中性原子）。","weight":8,"source":"https://www.news.cn/digital/20251015/b6023ec32a0e4ce7b858836fd53695d9/c.html"},
 {"id":"i_blackrock","type":"investor","name":"贝莱德","name_en":"BlackRock","country":"美国","region":"北美","intro":"PsiQuantum 多轮融资主要机构投资方，亦出现在 IQM 投资方名单。","weight":7,"source":"https://www.turingq.com"},
 {"id":"i_tencent","type":"investor","name":"腾讯","name_en":"Tencent","country":"中国","region":"中国","intro":"2022 年参与 IQM 1.28 亿欧元 A2 轮，是中国互联网巨头中少有的欧洲量子硬件投资方。","weight":6,"source":"https://techfundingnews.com/finnish-startup-iqm-to-raise-over-e200m-will-it-be-one-of-the-biggest-rounds-in-european-quantum-computing-history/"},
 {"id":"i_temasek","type":"investor","name":"淡马锡","name_en":"Temasek","country":"新加坡","region":"亚太及其他","intro":"新加坡主权基金，据报道领投 Pasqal 2023 年约 1 亿欧元 B 轮。","weight":6,"source":"https://www.pasqal.com","uncertain":["领投 Pasqal B 轮的细节待核验"]},
 {"id":"i_hillhouse","type":"investor","name":"高瓴创投","name_en":"GL Ventures","country":"中国","region":"中国","intro":"2020-2021 年领投国仪量子 B 轮并两度加注（发行前直接持股约 6.3%），其量子赛道首个布局项目。","weight":6,"source":"https://www.stcn.com/article/detail/4070211.html"},
 {"id":"i_jushi","type":"investor","name":"基石资本","name_en":"Co-Stone Capital","country":"中国","region":"中国","intro":"2020 年经深圳领瑞基石基金入股国仪量子，看重量子精密测量“可落地的颠覆”。","weight":4,"source":"https://www.stcn.com/article/detail/4070211.html"},
 {"id":"i_cicf","type":"investor","name":"中网投（中国互联网投资基金）","name_en":"China Internet Investment Fund","country":"中国","region":"中国","intro":"国家级基金，2021 年领投本源量子 A 轮，亦为图灵量子战略投资方。","weight":5,"source":"https://stock.10jqka.com.cn/20260608/c677274983.shtml"},
 {"id":"i_szvc","type":"investor","name":"深创投","name_en":"Shenzhen Capital Group","country":"中国","region":"中国","intro":"2022 年经红土基金领投本源量子近 10 亿元 B 轮，并参与 Pre-IPO 轮。","weight":5,"source":"https://stock.10jqka.com.cn/20260608/c677274983.shtml"},
 {"id":"i_zkx","type":"investor","name":"中科创星","name_en":"CASSTAR","country":"中国","region":"中国","intro":"中科院背景硬科技早期基金，2026 年联合领投本源量子 Pre-IPO 轮 4.5 亿元。","weight":5,"source":"https://unicorn500.com/index.php?a=index&aid=416&c=View&m=home"},
 {"id":"i_junlian","type":"investor","name":"君联资本","name_en":"Legend Capital","country":"中国","region":"中国","intro":"2021 年参与图灵量子 Pre-A 轮；亦为华翊量子早期投资方并持续追加至 A+ 轮。","weight":5,"source":"https://so.html5.qq.com/page/real/search_news?docid=70000021_10669eebe1472952"},
 {"id":"i_legendstar","type":"investor","name":"联想之星","name_en":"Legend Star","country":"中国","region":"中国","intro":"2021 年领投图灵量子天使轮（2500 万元），当时国内量子计算最大天使轮。","weight":4,"source":"https://so.html5.qq.com/page/real/search_news?docid=70000021_10669eebe1472952"},
 {"id":"i_shengshi","type":"investor","name":"盛世投资","name_en":"CGP Investment","country":"中国","region":"中国","intro":"母基金管理机构，2025 年领投图灵量子亿元战略轮（估值推至 30-35 亿元区间）。","weight":4,"source":"https://finance.sina.cn/2025-07-21/detail-infhfezw4880167.d.html"},
 {"id":"i_gaorong","type":"investor","name":"高榕资本","name_en":"Gaorong Capital","country":"中国","region":"中国","intro":"2022 年领投华翊量子超亿元天使轮，红杉中国、奇绩创坛等跟投。","weight":4,"source":"https://m.thepaper.cn/rss_newsDetail_17743111"},
 {"id":"i_baiduv","type":"investor","name":"百度风投","name_en":"Baidu Ventures","country":"中国","region":"中国","intro":"华翊量子 Pre-A 轮入场并多轮追加至 A+ 轮，布局离子阱量子计算。","weight":4,"source":"https://hyqubit.com/newsinfo/11254213.html"},
 {"id":"i_jiantou","type":"investor","name":"建投投资","name_en":"JIC Investment","country":"中国","region":"中国","intro":"中国建投旗下投资平台，2026-05 领投华翊量子 A+ 轮，中信建投投资、中车资本跟投。","weight":4,"source":"https://hyqubit.com/newsinfo/11254213.html"},
 {"id":"i_wuhu","type":"investor","name":"芜湖投控","name_en":"Wuhu Investment Holding Group","country":"中国","region":"中国","intro":"芜湖市投资控股集团，2009 年与中科大共同发起设立问天量子。","weight":4,"source":"https://m.toutiao.com/article/7663828382190207515"},
 {"id":"i_worldfund","type":"investor","name":"World Fund","name_en":"World Fund","country":"德国","region":"欧洲","intro":"德国气候与深科技基金，2022 年领投 IQM 1.28 亿欧元 A2 轮（当时欧洲量子公司最大轮次）。","weight":4,"source":"https://techfundingnews.com/finnish-startup-iqm-to-raise-over-e200m-will-it-be-one-of-the-biggest-rounds-in-european-quantum-computing-history/"},
 {"id":"i_earlybird","type":"investor","name":"Earlybird（UNI-X）","name_en":"Earlybird Venture Capital","country":"德国","region":"欧洲","intro":"德国深科技 VC，2022 年初投资 eleQtron（UNI-X 高校转化基金）。","weight":4,"source":"https://eleqtron.com/en?p=2263"},
]

# ---------- 3. 更新既有边 ----------
for l in d['links']:
    if l['s']=='u_tsinghua' and l['t']=='c_huayi':
        l['note'] = '清华大学量子信息中心孵化（2022）'
    if l['s']=='s_duan' and l['t']=='c_huayi':
        l['note'] = '创始人、首席科学家'

# ---------- 4. 新增边 ----------
new_links = [
 # 投资机构 → 公司
 {"s":"i_chinatelecom","t":"c_ctquantum","rel":"投资/持股","w":3,"note":"全资设立（注册资本 30 亿元）"},
 {"s":"i_chinatelecom","t":"c_quantumctek","rel":"投资/持股","w":1,"note":"经中电信量子集团间接控股，实控人国务院国资委"},
 {"s":"i_honeywell","t":"c_quantinuum","rel":"投资/持股","w":3,"note":"最大股东（IPO 后保留约 48% 表决权），离子阱硬件技术来源"},
 {"s":"i_jpmorgan","t":"c_quantinuum","rel":"投资/持股","w":2,"note":"2024-01 领投 3 亿美元股权轮"},
 {"s":"i_nvidia","t":"c_quantinuum","rel":"投资/持股","w":1,"note":"NVentures 2025-09 首次投资"},
 {"s":"i_nvidia","t":"c_psiquantum","rel":"投资/持股","w":1,"unc":True,"note":"公开报道提及的战略投资（轮次细节待核验）"},
 {"s":"i_nvidia","t":"c_quera","rel":"投资/持股","w":1,"unc":True,"note":"公开报道提及的战略投资（轮次细节待核验）"},
 {"s":"i_blackrock","t":"c_psiquantum","rel":"投资/持股","w":2,"note":"多轮融资主要机构投资方"},
 {"s":"i_blackrock","t":"c_iqm","rel":"投资/持股","w":1,"unc":True,"note":"出现在公开投资方名单（轮次待核验）"},
 {"s":"i_tencent","t":"c_iqm","rel":"投资/持股","w":2,"note":"2022 年 A2 轮投资方之一"},
 {"s":"i_worldfund","t":"c_iqm","rel":"投资/持股","w":2,"note":"2022 年 1.28 亿欧元 A2 轮领投"},
 {"s":"i_temasek","t":"c_pasqal","rel":"投资/持股","w":2,"unc":True,"note":"据报道领投 2023 年约 1 亿欧元 B 轮（待核验）"},
 {"s":"i_hillhouse","t":"c_ciqtek","rel":"投资/持股","w":2,"note":"B 轮领投并两度加注（发行前直接持股约 6.3%）"},
 {"s":"i_jushi","t":"c_ciqtek","rel":"投资/持股","w":1,"note":"2020 年入场（深圳领瑞基石）"},
 {"s":"i_cicf","t":"c_origin","rel":"投资/持股","w":2,"note":"2021 年 A 轮领投"},
 {"s":"i_cicf","t":"c_turingq","rel":"投资/持股","w":1,"note":"战略投资方之一"},
 {"s":"i_szvc","t":"c_origin","rel":"投资/持股","w":2,"note":"2022 年近 10 亿元 B 轮领投（红土基金）"},
 {"s":"i_zkx","t":"c_origin","rel":"投资/持股","w":2,"note":"2026 年 Pre-IPO 轮联合领投 4.5 亿元"},
 {"s":"i_junlian","t":"c_turingq","rel":"投资/持股","w":1,"note":"2021 年 Pre-A 轮投资方"},
 {"s":"i_junlian","t":"c_huayi","rel":"投资/持股","w":1,"note":"早期投资方，持续追加至 A+ 轮"},
 {"s":"i_legendstar","t":"c_turingq","rel":"投资/持股","w":1,"note":"2021 年天使轮领投 2500 万元"},
 {"s":"i_shengshi","t":"c_turingq","rel":"投资/持股","w":2,"note":"2025 年亿元战略轮领投"},
 {"s":"i_gaorong","t":"c_huayi","rel":"投资/持股","w":1,"note":"2022 年超亿元天使轮领投"},
 {"s":"i_baiduv","t":"c_huayi","rel":"投资/持股","w":1,"note":"Pre-A 轮入场，多轮追加"},
 {"s":"i_jiantou","t":"c_huayi","rel":"投资/持股","w":2,"note":"2026-05 A+ 轮领投"},
 {"s":"i_wuhu","t":"c_wentian","rel":"投资/持股","w":2,"note":"2009 年与中科大共同发起设立"},
 {"s":"i_earlybird","t":"c_eleqtron","rel":"投资/持股","w":1,"note":"2022 年初 VC 投资方（UNI-X 高校转化基金）"},
 # 创始人/高管 → 公司
 {"s":"x_khan","t":"c_quantinuum","rel":"任职/创办","w":2,"note":"CQC 创始人，现任首席产品官、副董事长"},
 {"s":"x_goetz","t":"c_iqm","rel":"任职/创办","w":2,"note":"联合创始人、CEO"},
 {"s":"s_mottonen","t":"c_iqm","rel":"任职/创办","w":2,"note":"联合创始人、首席科学家"},
 {"s":"x_reymond","t":"c_pasqal","rel":"任职/创办","w":2,"note":"联合创始人、CEO"},
 {"s":"x_ribordy","t":"c_idq","rel":"任职/创办","w":2,"note":"联合创始人、CEO"},
 {"s":"s_senellart","t":"c_quandela","rel":"任职/创办","w":2,"note":"联合创始人"},
 {"s":"x_bloom","t":"c_atom","rel":"任职/创办","w":2,"note":"创始人、CEO"},
 {"s":"x_rose","t":"c_dwave","rel":"任职/创办","w":2,"note":"创始人（曾任 CEO/CTO）"},
 {"s":"x_sivan","t":"c_qm","rel":"任职/创办","w":2,"note":"联合创始人、CEO"},
 {"s":"x_wisby","t":"c_oqc","rel":"任职/创办","w":2,"note":"创始人（首任 CEO）"},
 {"s":"x_shadbolt","t":"c_psiquantum","rel":"任职/创办","w":2,"note":"联合创始人、首席科学官"},
 {"s":"x_brierley","t":"c_riverlane","rel":"任职/创办","w":2,"note":"创始人、CEO"},
 {"s":"x_weidt","t":"c_universal_quantum","rel":"任职/创办","w":2,"note":"联合创始人、CEO"},
 {"s":"x_yaolin","t":"c_huayi","rel":"任职/创办","w":2,"note":"联合创始人、董事长兼 CEO"},
 {"s":"x_mayin","t":"c_boseq","rel":"任职/创办","w":2,"note":"联合创始人"},
 {"s":"x_palacios","t":"c_nuquantum","rel":"任职/创办","w":2,"note":"创始人、CEO"},
 {"s":"x_nunn","t":"c_orca","rel":"任职/创办","w":2,"note":"联合创始人"},
 # 创始人/高管 → 高校（教育/研究经历）
 {"s":"x_khan","t":"u_cambridge","rel":"任职","w":1,"unc":True,"note":"Judge Business School 荣誉研究员（待核验）"},
 {"s":"x_goetz","t":"u_aalto","rel":"任职","w":1,"note":"博士学位授予院校（Aalto/VTT 研究经历）"},
 {"s":"s_mottonen","t":"u_aalto","rel":"任职","w":2,"note":"应用物理系教授"},
 {"s":"s_senellart","t":"u_iqo","rel":"任职","w":1,"unc":True,"note":"CNRS/C2N（巴黎-萨克雷体系，机构表述待核验）"},
 {"s":"x_rose","t":"u_ubc","rel":"任职","w":1,"unc":True,"note":"博士学位授予院校（待核验）"},
 {"s":"x_sivan","t":"u_weizmann","rel":"任职","w":1,"note":"博士学位授予院校"},
 {"s":"x_wisby","t":"u_oxford","rel":"任职","w":1,"unc":True,"note":"博士学位授予院校（待核验）"},
 {"s":"x_brierley","t":"u_cambridge","rel":"任职","w":1,"unc":True,"note":"剑桥研究经历（待核验）"},
 {"s":"x_weidt","t":"u_sussex","rel":"任职","w":1,"note":"萨塞克斯大学研究员经历"},
 {"s":"x_palacios","t":"u_cambridge","rel":"任职","w":1,"unc":True,"note":"博士学位授予院校（待核验）"},
 {"s":"x_nunn","t":"u_oxford","rel":"任职","w":1,"unc":True,"note":"牛津研究经历（待核验）"},
 # 师承
 {"s":"s_gisin","t":"x_ribordy","rel":"师承","w":1,"unc":True,"note":"日内瓦大学博士（Gisin 组，待核验）"},
 {"s":"s_obrien","t":"x_shadbolt","rel":"师承","w":2,"note":"布里斯托尔大学博士（O'Brien 组）"},
]

added_n = added_l = 0
for n in new_nodes:
    if n['id'] in ids:
        print('SKIP existing node:', n['id']); continue
    d['nodes'].append(n); ids.add(n['id']); added_n += 1
for l in new_links:
    key = (l['s'], l['t'], l['rel'])
    if key in edge_keys:
        print('SKIP existing link:', key); continue
    if l['s'] not in ids or l['t'] not in ids:
        print('MISSING endpoint:', key); continue
    d['links'].append(l); edge_keys.add(key); added_l += 1

json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'added {added_n} nodes, {added_l} links -> total {len(d["nodes"])} nodes, {len(d["links"])} links')
