# patch_v6: 系统性查缺补漏 —— 韩国资本、以色列软件/安全、法硅基、西班牙ICFO、北京量子院、武汉/上海国内系、滑铁卢卫星QKD等
import json

P = r"D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json"
d = json.load(open(P, encoding="utf-8"))
by_id = {n["id"]: n for n in d["nodes"]}

def N(id, type, name, name_en, country, region, fields, weight, intro, source, **kw):
    n = {"id": id, "type": type, "name": name, "name_en": name_en, "country": country,
         "region": region, "fields": fields, "weight": weight, "intro": intro, "source": source,
         "note": kw.get("note",""), "uncertain": kw.get("unc",[]),
         "affiliation": kw.get("affiliation",""), "dept": kw.get("dept",""), "title": kw.get("title",""),
         "lab": kw.get("lab",""), "founded": kw.get("founded",""), "hq": kw.get("hq",""),
         "funding": kw.get("funding",""), "business": kw.get("business","")}
    if id in by_id:
        print("SKIP dup node", id); return
    d["nodes"].append(n); by_id[id] = n

# ---------- 高校/机构 ----------
N("u_baqis","university","北京量子信息科学研究院","Beijing Academy of Quantum Information Sciences","中国","中国",
  ["量子计算","量子通信"],7,
  "2017 年北京市与中科院、北大、清华共建的新型研发机构，薛其坤任院长，覆盖超导、拓扑、量子器件与量子通信，是中国量子科研「国家队」的重要一极。",
  "https://www.baqis.ac.cn/")
N("u_icfo","university","光子科学研究所（ICFO）","The Institute of Photonic Sciences","西班牙","欧洲",
  ["量子通信","量子传感与测量"],6,
  "巴塞罗那光子学旗舰研究所，量子光学、量子网络与量子传感研究欧洲前列，孵化 Quside（量子随机数）、LuxQuanta（CV-QKD）等企业。",
  "https://www.icfo.eu/")
N("u_cealeti","university","CEA-Leti（格勒诺布尔）","CEA-Leti","法国","欧洲",
  ["量子计算"],6,
  "法国原子能委员会微电子与纳米技术研究所，硅基量子点比特研究逾 15 年，与 CNRS 共同孵化硅基量子计算公司 Quobly。",
  "https://www.leti-cea.com/")
N("u_bham","university","伯明翰大学","University of Birmingham","英国","欧洲",
  ["量子传感与测量"],5,
  "英国国家量子传感与授时中心（UK QT Hub Sensors and Timing）牵头校，Kai Bongs 组冷原子重力仪工程化领先，衍生 Delta g 等传感企业。",
  "https://www.birmingham.ac.uk/")
N("u_wisc","university","威斯康星大学麦迪逊分校","University of Wisconsin–Madison","美国","北美",
  ["量子计算"],6,
  "Mark Saffman 中性原子量子门研究所在地（Wisconsin Quantum Institute），里德堡门协议的重要源头之一。",
  "https://wqi.wisc.edu/")
N("u_huji","university","耶路撒冷希伯来大学","Hebrew University of Jerusalem","以色列","亚太及其他",
  ["量子计算","量子软件与算法"],6,
  "以色列理论量子信息重镇，Dorit Aharonov 容错定理（Aharonov–Ben-Or）诞生地，错误缓解公司 Qedma 的学术源头之一。",
  "https://www.huji.ac.il/")
N("u_sysu","university","中山大学","Sun Yat-sen University","中国","中国",
  ["量子计算"],5,
  "罗乐教授量子信息与测控团队所在地（原子分子光物理、囚禁离子），启科量子首席科学家团队的学术依托单位。",
  "https://www.sysu.edu.cn/")
N("u_iapcm","university","中科院精密测量科学与技术创新研究院","Innovation Academy for Precision Measurement Science and Technology, CAS","中国","中国",
  ["量子计算","量子传感与测量"],6,
  "（原武汉物理与数学研究所）国内最早开展中性原子量子技术研究的团队之一，冷原子干涉重力测量与中性原子量子计算双线，孵化中科酷原。",
  "http://www.apm.ac.cn/")
N("u_sherbrooke","university","舍布鲁克大学","Université de Sherbrooke","加拿大","北美",
  ["量子计算"],5,
  "魁北克量子研究所（Institut Quantique）所在地，超导与玻色编码量子比特特色，孵化 Nord Quantique。",
  "https://www.usherbrooke.ca/")

# ---------- 学者 ----------
N("s_saffman","scholar","Mark Saffman","Mark Saffman","美国","北美",
  ["量子计算"],7,"里德堡中性原子量子门协议提出者之一（Saffman–Walker 2005），中性原子量子计算理论体系奠基人，威斯康星量子研究所主任。",
  "https://wqi.wisc.edu/",affiliation="威斯康星大学麦迪逊分校",dept="物理系",title="教授 / Wisconsin Quantum Institute 主任")
N("s_jennewein","scholar","Thomas Jennewein","Thomas Jennewein","加拿大","北美",
  ["量子通信"],7,"卫星量子通信加拿大旗手，QEYSSat 量子加密科学卫星负责人；蔡林格在因斯布鲁克时期的博后，与潘建伟同门。",
  "https://uwaterloo.ca/institute-for-quantum-computing/",affiliation="滑铁卢大学",dept="物理与天文学系 / IQC",title="教授")
N("s_knight","scholar","Peter Knight","Peter Knight","英国","欧洲",
  ["量子通信","量子计算"],8,"英国量子光学教父级人物，帝国理工学院教授、英国国家量子技术计划主要设计者之一，爵士。",
  "https://www.imperial.ac.uk/",affiliation="帝国理工学院",dept="物理系",title="教授（英国皇家学会院士）")
N("s_aharonov","scholar","Dorit Aharonov","Dorit Aharonov","以色列","亚太及其他",
  ["量子计算","量子软件与算法"],8,"容错量子计算定理（Aharonov–Ben-Or 1997）证明者，量子计算复杂性理论奠基人之一；Qedma 联合创始人。",
  "https://www.huji.ac.il/",affiliation="耶路撒冷希伯来大学",dept="计算机科学与工程学院",title="教授")
N("s_ozeri","scholar","Roee Ozeri","Roee Ozeri","以色列","亚太及其他",
  ["量子计算"],6,"离子阱量子计算与量子传感专家，魏茨曼研究所教授；Quantum Art 联合创始人兼首席科学家。",
  "https://www.weizmann.ac.il/",affiliation="魏茨曼科学研究所",dept="复杂系统物理系",title="教授")
N("s_luole","scholar","罗乐","Le Luo","中国","中国",
  ["量子计算"],5,"中山大学量子信息与测控团队带头人，原子分子光物理与囚禁离子专家；Monroe 在 JQI 时期的博后，启科量子联合创始人兼首席科学家。",
  "https://www.sysu.edu.cn/",affiliation="中山大学",dept="物理与天文学院",title="教授")
N("s_zengguihua","scholar","曾贵华","Guihua Zeng","中国","中国",
  ["量子通信"],5,"连续变量量子密钥分发（CV-QKD）国内先行者之一，上海交通大学教授；循态量子的学术源头（公开报道，细节待核验）。",
  "https://www.sjtu.edu.cn/",affiliation="上海交通大学",dept="电子信息与电气工程学院",title="教授",
  unc=["与循态量子的具体关联细节以公开报道为准，待核验"])
N("s_bongs","scholar","Kai Bongs","Kai Bongs","英国","欧洲",
  ["量子传感与测量"],6,"冷原子量子传感工程化领军人物，伯明翰大学量子传感与授时中心主任，原子重力仪/重力梯度仪产业化推动者。",
  "https://www.birmingham.ac.uk/",affiliation="伯明翰大学",dept="物理与天文学院",title="教授")

# ---------- 学生/博后（校友创业者） ----------
N("st_goban","student","Akihisa Goban","Akihisa Goban","日本","亚太及其他",
  ["量子计算","量子网络"],4,"纳米光纤腔 QED 囚禁中性原子技术专家（Caltech Kimble 组博后经历），NanoQT 联合创始人。",
  "https://www.nanoqt.tech/",affiliation="NanoQT",title="联合创始人",
  unc=["博后师承关系依据其 Caltech 时期纳米光纤囚禁研究经历整理"])
N("st_lemyre","student","Julien Camirand Lemyre","Julien Camirand Lemyre","加拿大","北美",
  ["量子计算"],4,"舍布鲁克大学博士，2020 年联合创立 Nord Quantique 并任 CEO，主攻玻色编码（GKP）容错量子比特。",
  "https://nordquantique.ca/",affiliation="Nord Quantique",title="联合创始人/CEO")

# ---------- 公司 ----------
N("c_classiq","company","Classiq","Classiq Technologies","以色列","亚太及其他",
  ["量子软件与算法"],6,"2020 年创立（Minerbi/Naveh 兄弟），量子算法高级建模与电路自动合成平台，客户含 BMW、劳斯莱斯、花旗、东芝；与英伟达/微软/AWS 深度合作。",
  "https://www.classiq.io/",founded="2020",hq="特拉维夫",
  funding="C 轮 1.1 亿美元（2025-05）+ 2025 年底 3000 万美元增资，累计超 2 亿美元；正洽谈 SPAC 上市（估值区间 20–50 亿美元，公开报道）",
  business="量子软件平台（电路自动合成）",
  unc=["SPAC 上市谈判仍在进行中，估值以最终交割为准"])
N("c_qart","company","Quantum Art","Quantum Art","以色列","亚太及其他",
  ["量子计算"],6,"2022 年魏茨曼研究所 Ozeri 组孵化，离子阱量子计算，主打多比特门与模块化架构；路线图 2027 年千比特、2033 年百万比特。",
  "https://www.quantum-art.tech/",founded="2022",hq="雷霍沃特",
  funding="A 轮 1 亿美元（2025-12，Bedford Ridge 领投）+ 2026-04 扩轮 1.4 亿美元，累计约 2 亿美元；正洽谈 SPAC 上市（公开报道）",
  business="离子阱量子计算整机",
  unc=["SPAC 上市谈判仍在进行中，估值以最终交割为准"])
N("c_qedma","company","Qedma","Qedma Quantum","以色列","亚太及其他",
  ["量子软件与算法"],5,"2020 年前后由 Lindner（Technion）、Sinay 与 Aharonov（希伯来大学）联合创立，量子错误缓解软件（QESEM），与 IBM 深度合作。",
  "https://www.qedma.com/",founded="2020",hq="特拉维夫",
  funding="A 轮 2600 万美元（2025-07，Glilot+ 领投，IBM、韩国投资伙伴等跟投）",
  business="量子错误缓解软件")
N("c_quobly","company","Quobly","Quobly","法国","欧洲",
  ["量子计算"],7,"2022 年 CEA-Leti/CNRS 孵化（原名 Siquance，Vinet/Meunier/Perruchot 联创），FD-SOI 硅自旋量子比特走 300mm 标准产线路线，与意法半导体共建制造链。",
  "https://www.quobly.io/",founded="2022",hq="格勒诺布尔",
  funding="A 轮 1.15 亿欧元（2026-06，Bpifrance/SEALSQ/意法半导体领投），累计超 1.6 亿欧元",
  business="硅基量子计算整机与处理器")
N("c_nordq","company","Nord Quantique","Nord Quantique","加拿大","北美",
  ["量子计算"],5,"2020 年舍布鲁克大学 Institut Quantique 孵化（Camirand Lemyre 联创），玻色编码（GKP）容错量子比特路线，以硬件层纠错压缩扩展成本。",
  "https://nordquantique.ca/",founded="2020",hq="舍布鲁克",
  funding="早中期风险投资（A 轮 2024，Quantonation 领投，公开报道）",
  business="玻色码超导量子计算")
N("c_quside","company","Quside","Quside Technologies","西班牙","欧洲",
  ["量子通信","量子传感与测量"],4,"2017 年 ICFO 孵化，量子随机数发生器（QRNG）专业厂商，相空间随机性测量芯片用于密码与蒙特卡洛加速。",
  "https://quside.com/",founded="2017",hq="巴塞罗那",
  funding="早中期风险投资（公开报道）",
  business="量子随机数发生器")
N("c_luxquanta","company","LuxQuanta","LuxQuanta Technologies","西班牙","欧洲",
  ["量子通信"],4,"2021 年 ICFO 孵化，连续变量 QKD（CV-QKD）系统 NOVA LQ，主打与现有电信光网络共纤部署。",
  "https://luxquanta.com/",founded="2021",hq="巴塞罗那",
  funding="早期风险投资（A 轮，公开报道）",
  business="CV-QKD 系统")
N("c_nanoqt","company","NanoQT","Nanofiber Quantum Technologies","日本","亚太及其他",
  ["量子计算","量子网络"],4,"2022 年创立（Goban 等联创），纳米光纤腔 QED 囚禁中性原子的独特路线，日美双基地，与 QuEra 合作可扩展网络化量子处理器。",
  "https://www.nanoqt.tech/",founded="2022",hq="东京 / 美国（双基地）",
  funding="早期风险投资（公开报道）",
  business="纳米光纤腔 QED 量子计算",
  unc=["创始团队与融资细节公开信息有限"])
N("c_qike","company","启科量子","Qudoors","中国","中国",
  ["量子计算","量子通信"],5,"2019 年罗乐（中山大学，Monroe 博后）与留美团队联合创立，离子阱+量子通信双线：发布国内首台模块化离子阱工程机「天算 1 号」，量子保密通信设备达电信级标准。",
  "https://www.qudoor.com/",founded="2019",hq="北京",
  funding="风险投资（多轮，金额未完整公开）",
  business="离子阱量子计算 + 量子保密通信设备")
N("c_coolatom","company","中科酷原","Cold Atom Quantum (Wuhan)","中国","中国",
  ["量子计算","量子传感与测量"],5,"2020 年中科院精密测量院团队创立（武汉），国内首家兼具中性原子量子计算与原子量子精密测量产业化能力的公司；2024 年发布国内首台 100 比特原子量子计算机「汉原 1 号」并已交付 3 套。",
  "https://www.coldatom.com.cn/",founded="2020",hq="武汉",
  funding="D 轮近亿元（2026-01，中国移动链长基金）；中科创星 A 轮（2022）等，累计披露约 1.6 亿元",
  business="中性原子量子计算整机 + 量子精密测量仪器",
  unc=["公司官网地址以工商/公开报道为准，待核验"])
N("c_xuntai","company","循态量子","Xuntai Quantum","中国","中国",
  ["量子通信"],4,"公开报道称为上海交通大学曾贵华团队成果转化的 CV-QKD 企业（2017 年成立，细节待核验），连续变量量子保密通信设备与组网方案。",
  "",founded="2017",hq="上海",
  funding="风险投资（公开信息有限）",
  business="CV-QKD 设备与组网",
  unc=["与上海交大的成果转化关系及融资信息依据公开报道整理，待核验"])

# ---------- 创始人/高管 ----------
N("x_vinet","exec","Maud Vinet","Maud Vinet","法国","欧洲",
  ["量子计算"],5,"Quobly 联合创始人兼 CEO，原 CEA-Leti 量子计算项目负责人，法国硅基量子计算产业化的核心推手。",
  "https://www.quobly.io/",affiliation="Quobly",title="联合创始人/CEO")
N("x_tangbiao","exec","汤彪","Tang Biao","中国","中国",
  ["量子计算","量子传感与测量"],4,"中科酷原创始人/董事长，中科院精密测量院背景，中性原子量子计算与量子精密测量产业化负责人。",
  "https://news.hubeidaily.net/mobile/c_5031163.html",affiliation="中科酷原",title="创始人/董事长",
  unc=["个人履历公开信息有限"])

# ---------- 投资机构 ----------
N("i_skt","investor","SK 电讯","SK Telecom","韩国","亚太及其他",
  ["量子通信"],5,"韩国最大电信运营商，2018 年控股 ID Quantique（约 6500 万美元）成为全球量子通信产业化的战略推手，并以 IDQ 技术建设韩国量子安全网络。",
  "https://www.idquantique.com/",note="2025 年 IonQ 控股 IDQ 后的股权结构以交易披露为准",
  unc=["IonQ 收购后 SKT 保留的持股比例以公开披露为准"])

# ---------- 边 ----------
L = [
 {"s":"s_xue","t":"u_baqis","rel":"任职","w":2,"note":"北京量子院院长（2017 年创院起）"},
 {"s":"s_saffman","t":"u_wisc","rel":"任职","w":1,"note":"物理系教授 / WQI 主任"},
 {"s":"s_jennewein","t":"u_waterloo","rel":"任职","w":1,"note":"IQC 教授"},
 {"s":"s_zeilinger","t":"s_jennewein","rel":"师承","w":2,"note":"Jennewein 曾在因斯布鲁克 Zeilinger 组从事博士后研究"},
 {"s":"s_knight","t":"u_imperial","rel":"任职","w":1,"note":"物理系教授"},
 {"s":"s_aharonov","t":"u_huji","rel":"任职","w":1,"note":"计算机科学教授"},
 {"s":"s_aharonov","t":"c_qedma","rel":"任职/创办","w":2,"note":"联合创始人（与 Technion 的 Lindner、Sinay 共创）"},
 {"s":"u_huji","t":"c_qedma","rel":"学校孵化","w":1,"unc":True,"note":"希伯来大学/Technion 学者共创"},
 {"s":"s_ozeri","t":"u_weizmann","rel":"任职","w":1,"note":"复杂系统物理系教授"},
 {"s":"s_ozeri","t":"c_qart","rel":"任职/创办","w":2,"note":"联合创始人兼首席科学家"},
 {"s":"u_weizmann","t":"c_qart","rel":"学校孵化","w":2,"note":"Ozeri 组 spin-off（2022）"},
 {"s":"s_luole","t":"u_sysu","rel":"任职","w":1,"note":"物理与天文学院教授"},
 {"s":"s_monroe","t":"s_luole","rel":"师承","w":2,"note":"罗乐曾在 JQI 从事博士后研究（Monroe 组）"},
 {"s":"s_luole","t":"c_qike","rel":"任职/创办","w":2,"note":"联合创始人兼首席科学家"},
 {"s":"u_sysu","t":"c_qike","rel":"学校孵化","w":1,"unc":True,"note":"罗乐团队与中山大学联培合作，成果转化关系以公开报道为准"},
 {"s":"s_zengguihua","t":"u_sjtu","rel":"任职","w":1,"note":"电子信息与电气工程学院教授"},
 {"s":"s_zengguihua","t":"c_xuntai","rel":"任职/创办","w":1,"unc":True,"note":"公开报道称循态量子为其团队成果转化企业"},
 {"s":"u_sjtu","t":"c_xuntai","rel":"学校孵化","w":1,"unc":True,"note":"成果转化细节待核验"},
 {"s":"st_goban","t":"c_nanoqt","rel":"任职/创办","w":2,"note":"联合创始人"},
 {"s":"s_kimble","t":"st_goban","rel":"师承","w":1,"unc":True,"note":"Goban 曾在 Caltech Kimble 组从事纳米光纤囚禁研究"},
 {"s":"st_lemyre","t":"u_sherbrooke","rel":"任职","w":1,"note":"博士学位授予院校（Institut Quantique）"},
 {"s":"st_lemyre","t":"c_nordq","rel":"任职/创办","w":2,"note":"联合创始人/CEO"},
 {"s":"u_sherbrooke","t":"c_nordq","rel":"学校孵化","w":2,"note":"Institut Quantique spin-off（2020）"},
 {"s":"s_bongs","t":"u_bham","rel":"任职","w":1,"note":"量子传感与授时中心主任"},
 {"s":"u_cealeti","t":"c_quobly","rel":"学校孵化","w":2,"note":"CEA-Leti/CNRS spin-off（2022，原名 Siquance）"},
 {"s":"x_vinet","t":"c_quobly","rel":"任职/创办","w":2,"note":"联合创始人/CEO"},
 {"s":"x_vinet","t":"u_cealeti","rel":"任职","w":1,"note":"原 CEA-Leti 量子计算项目负责人"},
 {"s":"u_icfo","t":"c_quside","rel":"学校孵化","w":2,"note":"ICFO spin-off（2017）"},
 {"s":"u_icfo","t":"c_luxquanta","rel":"学校孵化","w":2,"note":"ICFO spin-off（2021）"},
 {"s":"u_iapcm","t":"c_coolatom","rel":"学校孵化","w":2,"note":"中科院精密测量院团队创立（2020）"},
 {"s":"x_tangbiao","t":"c_coolatom","rel":"任职/创办","w":2,"note":"创始人/董事长"},
 {"s":"x_tangbiao","t":"u_iapcm","rel":"任职","w":1,"unc":True,"note":"核心团队源自精密测量院，个人任职细节公开信息有限"},
 {"s":"i_zkx","t":"c_coolatom","rel":"投资/持股","w":2,"note":"2022-03 A 轮投资方"},
 {"s":"c_ionq","t":"c_classiq","rel":"投资/持股","w":2,"note":"IonQ 为 Classiq 战略投资方之一（2025，公开报道）"},
 {"s":"i_softbank","t":"c_classiq","rel":"投资/持股","w":1,"note":"SoftBank 参与投资（2025，公开报道）"},
 {"s":"i_skt","t":"c_idq","rel":"投资/持股","w":2,"note":"2018 年控股 IDQ（约 6500 万美元）"},
]
existing = {(l["s"],l["t"],l["rel"]) for l in d["links"]}
added = 0
for l in L:
    assert l["s"] in by_id and l["t"] in by_id, l
    l.setdefault("unc", False)
    if (l["s"],l["t"],l["rel"]) in existing:
        print("SKIP dup link", l["s"], l["t"]); continue
    d["links"].append(l); added += 1

json.dump(d, open(P,"w",encoding="utf-8"), ensure_ascii=False, indent=1)

ids = {n["id"] for n in d["nodes"]}
bad = [l for l in d["links"] if l["s"] not in ids or l["t"] not in ids]
iso = [i for i in ids if not any(l["s"]==i or l["t"]==i for l in d["links"])]
no_intro = [n["id"] for n in d["nodes"] if not n.get("intro")]
no_weight = [n["id"] for n in d["nodes"] if not n.get("weight")]
from collections import Counter
print("nodes:", len(d["nodes"]), dict(Counter(n["type"] for n in d["nodes"])))
print("links:", len(d["links"]), "| links added:", added)
print("bad:", len(bad), "| isolated:", iso, "| no_intro:", no_intro, "| no_weight:", no_weight)
