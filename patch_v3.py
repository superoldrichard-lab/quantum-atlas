# -*- coding: utf-8 -*-
"""v3 数据补丁：新增节点与边，追加到 quantum_network.json"""
import json, io, sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
P = r'D:/WorkBuddy/Workspace/2026-10-03-quantum-graph/quantum_network.json'
d = json.load(open(P, encoding='utf-8'))
ids = {n['id'] for n in d['nodes']}
edge_keys = {(l['s'], l['t'], l['rel']) for l in d['links']}

new_nodes = [
 # ---- 高校/研究机构 (+5) ----
 {"id":"u_nju","type":"university","name":"南京大学","name_en":"Nanjing University","country":"中国","region":"中国","fields":["量子计算","量子通信","量子传感与测量"],"source":"https://www.nju.edu.cn/","intro":"物理学科传统强校，祝世宁院士领衔介电体超晶格与量子光学研究，在光子芯片与量子模拟方向有重要布局。","weight":7},
 {"id":"u_sxu","type":"university","name":"山西大学","name_en":"Shanxi University","country":"中国","region":"中国","fields":["量子通信","量子传感与测量"],"source":"https://www.sxu.edu.cn/","intro":"拥有量子光学与光量子器件国家重点实验室，彭堃墀院士奠基的连续变量量子光学学派所在地。","weight":6},
 {"id":"u_chalmers","type":"university","name":"查尔姆斯理工大学","name_en":"Chalmers University of Technology","country":"瑞典","region":"欧洲","fields":["量子计算","量子通信","量子传感与测量"],"source":"https://www.chalmers.se/en/","intro":"瑞典量子旗舰 WACQT（瓦伦堡量子技术中心，逾 10 亿克朗）协调高校，主攻超导量子计算整机。","weight":7},
 {"id":"u_siegen","type":"university","name":"锡根大学","name_en":"University of Siegen","country":"德国","region":"欧洲","fields":["量子计算"],"source":"https://www.uni-siegen.de/","intro":"量子光学教席（Wunderlich 组）以微波操控离子阱（MAGIC）见长，孵化了德国首家量子硬件公司 eleQtron。","weight":4},
 {"id":"u_riken","type":"university","name":"理化学研究所","name_en":"RIKEN","country":"日本","region":"亚太及其他","fields":["量子计算","量子通信"],"source":"https://www.riken.jp/en/","intro":"日本国立研究开发法人，量子计算研究中心（RQC）承载超导、光量子等多路线研究。","weight":7},
 # ---- 学者 (+8) ----
 {"id":"s_ye","type":"scholar","name":"叶军","name_en":"Jun Ye","country":"美国","region":"北美","fields":["量子传感与测量","量子计算"],"affiliation":"科罗拉多大学博尔德分校 / JILA","dept":"物理系 / JILA（NIST 联合研究所）","title":"教授 / JILA Fellow","lab":"https://jila.colorado.edu/yelabs","source":"https://jila.colorado.edu/yelabs","intro":"美国国家科学院院士，锶光晶格钟精度纪录保持者，量子精密测量与冷分子物理领域领袖。","weight":9,"note":"本科毕业于上海交通大学"},
 {"id":"s_zhusn","type":"scholar","name":"祝世宁","name_en":"Zhu Shining","country":"中国","region":"中国","fields":["量子通信","量子计算"],"affiliation":"南京大学","dept":"物理学院","title":"教授 / 中国科学院院士","source":"https://www.nju.edu.cn/","intro":"中科院院士，介电体超晶格与量子光学专家，长期从事准相位匹配与非线性光子学芯片研究。","weight":8},
 {"id":"s_pengkc","type":"scholar","name":"彭堃墀","name_en":"Peng Kunchi","country":"中国","region":"中国","fields":["量子通信","量子传感与测量"],"affiliation":"山西大学","dept":"光电研究所","title":"教授 / 中国科学院院士","source":"https://www.sxu.edu.cn/","intro":"中科院院士，山西大学量子光学学派奠基人，连续变量量子态制备与量子保密通信开拓者。","weight":8},
 {"id":"s_han","type":"scholar","name":"韩正甫","name_en":"Han Zhengfu","country":"中国","region":"中国","fields":["量子通信"],"affiliation":"中国科学技术大学","dept":"光学与光学工程系","title":"教授","source":"https://baike.baidu.com/item/韩正甫/7764452","intro":"郭光灿院士学生，833 公里光纤 QKD 纪录共同创造者，问天量子创始人、董事长兼首席科学家。","weight":6},
 {"id":"s_delsing","type":"scholar","name":"佩尔·德尔辛","name_en":"Per Delsing","country":"瑞典","region":"欧洲","fields":["量子计算"],"affiliation":"查尔姆斯理工大学","dept":"微技术与纳米科学系","title":"教授 / WACQT 创始主任（2018-2024）","source":"https://www.wacqt.se/en/","intro":"瑞典皇家科学院院士、前诺贝尔物理学奖委员会委员，WACQT 创始主任，超导量子比特先驱。","weight":7},
 {"id":"s_wehner","type":"scholar","name":"斯蒂芬妮·韦纳","name_en":"Stephanie Wehner","country":"荷兰","region":"欧洲","fields":["量子网络","量子通信"],"affiliation":"代尔夫特理工大学（QuTech）","dept":"QuTech","title":"教授 / 量子互联网联盟（QIA）协调人","source":"https://qutech.nl/","intro":"量子互联网理论与网络架构领军人物，欧洲量子互联网联盟（QIA）协调人。","weight":7},
 {"id":"s_wunderlich","type":"scholar","name":"克里斯托夫·文德利希","name_en":"Christof Wunderlich","country":"德国","region":"欧洲","fields":["量子计算"],"affiliation":"锡根大学","dept":"物理系量子光学教席","title":"教授","source":"https://eleqtron.com/en/company/","intro":"MAGIC 微波梯度耦合离子阱技术发明人，eleQtron 联合创始人。","weight":5},
 {"id":"s_vazirani","type":"scholar","name":"乌梅什·瓦兹拉尼","name_en":"Umesh Vazirani","country":"美国","region":"北美","fields":["量子计算","量子软件与算法"],"affiliation":"加州大学伯克利分校","dept":"计算机科学系","title":"教授","source":"https://www.cs.berkeley.edu/~vazirani/","intro":"量子计算理论奠基人之一，量子算法与量子复杂性学派领袖，培养了大批量子理论学者。","weight":7},
 # ---- 学生/校友 (+2) ----
 {"id":"st_xiang","type":"student","name":"项金根","name_en":"Xiang Jingen","country":"中国","region":"中国","fields":["量子计算"],"affiliation":"深圳量旋科技","title":"创始人 / CEO（清华大学博士、哈佛大学博士后）","source":"https://www.spinq.cn/","intro":"清华博士、哈佛博士后，2018 年回国创立量旋科技，做出全球首台桌面型核磁量子计算机。","weight":5},
 {"id":"st_peronnin","type":"student","name":"泰奥·佩罗南","name_en":"Théau Peronnin","country":"法国","region":"欧洲","fields":["量子计算"],"affiliation":"Alice & Bob","title":"联合创始人 / CEO","source":"https://alice-bob.com/","intro":"Alice & Bob 联合创始人兼 CEO，猫态量子比特（cat qubit）容错路线代表创业者。","weight":4,"uncertain":["博士培养单位（巴黎高师/巴黎-萨克雷体系）待公开资料核验"]},
 # ---- 公司 (+7) ----
 {"id":"c_quantinuum","type":"company","name":"Quantinuum","name_en":"Quantinuum","country":"美国/英国","region":"欧洲","fields":["量子计算","量子软件与算法"],"founded":"2021（前身 Cambridge Quantum 2014）","hq":"英国剑桥 / 美国科罗拉多布鲁姆菲尔德","funding":"已上市（Nasdaq: QNT，2026 年 6 月 IPO，估值约 176 亿美元）","business":"离子阱量子计算整机（H 系列）与量子软件（TKET、Quantum Origin）","source":"https://www.quantinuum.com/press-releases/introducing-quantinuum","intro":"由霍尼韦尔量子部门与剑桥量子计算（CQC）2021 年合并而成，全球最大全栈量子公司之一，H 系列离子阱机保持量子体积纪录。","weight":9},
 {"id":"c_ctquantum","type":"company","name":"中电信量子集团","name_en":"China Telecom Quantum Group","country":"中国","region":"中国","fields":["量子通信","量子计算","量子传感与测量"],"founded":"2023（前身中电信量子科技 2020）","hq":"合肥","funding":"央企子公司（中国电信全资，注册资本 30 亿元）","business":"量子通信网络运营、天衍量子计算云平台、量子安全产品","source":"https://gxq.hefei.gov.cn/xwdt/mtjj/18799739.html","intro":"中国电信量子板块主体，2025 年 1 月成为国盾量子控股股东，运营全球最大规模的量子城域网体系。","weight":6},
 {"id":"c_wentian","type":"company","name":"问天量子","name_en":"Qasky (Anhui Qasky Quantum Technology)","country":"中国","region":"中国","fields":["量子通信"],"founded":"2009","hq":"芜湖","funding":"B 轮（2026 年 7 月，6 亿元）","business":"量子保密通信设备、量子随机数芯片、量子密码标准制定","source":"http://www.qasky.com/","intro":"郭光灿、韩正甫 2009 年创立的中国第一家量子信息产业化企业，由芜湖投控与中科大共同发起。","weight":6},
 {"id":"c_eleqtron","type":"company","name":"eleQtron","name_en":"eleQtron GmbH","country":"德国","region":"欧洲","fields":["量子计算"],"founded":"2020","hq":"锡根（兼汉堡）","funding":"A 轮（2026 年 5 月，5700 万欧元）","business":"MAGIC 微波操控离子阱量子计算机整机","source":"https://eleqtron.com/en/company/","intro":"锡根大学孵化的德国首家量子硬件公司，MAGIC 技术以微波替代激光操控离子阱，大幅降低扩展复杂度。","weight":5},
 {"id":"c_spinq","type":"company","name":"量旋科技","name_en":"SpinQ Technology","country":"中国","region":"中国","fields":["量子计算"],"founded":"2018","hq":"深圳（河套）","funding":"C+ 轮（2026 年，C 系列累计近 10 亿元）","business":"核磁共振教育量子计算机、超导量子芯片与整机","source":"https://www.spinq.cn/","intro":"项金根 2018 年创立，全球首台桌面型核磁量子计算机出品方，中国首家出口超导量子芯片的企业。","weight":5},
 {"id":"c_guoyao","type":"company","name":"国耀量子","name_en":"Guoyao Quantum","country":"中国","region":"中国","fields":["量子传感与测量"],"founded":"","hq":"合肥","funding":"","business":"量子雷达（单光子探测）","source":"https://big5.cri.cn/gate/big5/gr.cri.cn/20190531/cf6fe024-6f86-f409-7b19-4e5f8468cc4a.htm","intro":"中科大潘建伟团队与窦贤康团队技术作价入股转化的量子雷达企业。","weight":4,"uncertain":["成立年份与融资信息未核验","股权结构与技术来源细节待核验"]},
 {"id":"c_gkqn","type":"company","name":"国科量网（国科量子通信网络）","name_en":"Guoke Quantum Network","country":"中国","region":"中国","fields":["量子通信"],"founded":"","hq":"北京","funding":"","business":"量子保密通信骨干网络建设与运营","source":"https://big5.cri.cn/gate/big5/gr.cri.cn/20190531/cf6fe024-6f86-f409-7b19-4e5f8468cc4a.htm","intro":"中科院国科控股背景、中科大技术入股的量子通信网络建设运营企业。","weight":4,"uncertain":["成立年份与融资信息未核验","与中科大技术入股的细节待核验"]},
]

new_links = [
 {"s":"s_ye","t":"u_colorado","rel":"任职","w":2,"note":"JILA/NIST 联合研究所教授"},
 {"s":"s_ye","t":"u_sjtu","rel":"任职","w":1,"note":"本科学位授予院校（1989 年，应用物理）"},
 {"s":"s_zhusn","t":"u_nju","rel":"任职","w":2},
 {"s":"s_pengkc","t":"u_sxu","rel":"任职","w":2},
 {"s":"s_han","t":"u_ustc","rel":"任职","w":2},
 {"s":"s_guo","t":"s_han","rel":"师承","w":2,"note":"韩正甫为郭光灿院士学生"},
 {"s":"s_delsing","t":"u_chalmers","rel":"任职","w":2},
 {"s":"s_wehner","t":"u_delft","rel":"任职","w":2},
 {"s":"s_wehner","t":"s_hanson","rel":"联合研究","w":1,"note":"QuTech 同机构，量子互联网计划合作"},
 {"s":"s_wunderlich","t":"u_siegen","rel":"任职","w":2},
 {"s":"s_vazirani","t":"u_berkeley","rel":"任职","w":2},
 {"s":"s_nakamura","t":"u_riken","rel":"任职","w":1,"unc":True,"note":"曾任理研团队负责人，现职以东京大学为主，兼任关系待核验"},
 {"s":"u_riken","t":"u_tokyo","rel":"联合研究","w":1,"unc":True,"note":"超导量子计算联合研究（RQC-东大合作，细节待核验）"},
 {"s":"st_xiang","t":"u_tsinghua","rel":"任职","w":1,"note":"博士学位授予院校"},
 {"s":"st_xiang","t":"u_harvard","rel":"任职","w":1,"note":"博士后研究单位"},
 {"s":"st_xiang","t":"c_spinq","rel":"任职/创办","w":2,"note":"创始人、CEO"},
 {"s":"st_peronnin","t":"c_alicebob","rel":"任职/创办","w":2,"note":"联合创始人、CEO"},
 {"s":"st_peronnin","t":"u_ens","rel":"任职","w":1,"unc":True,"note":"博士培养单位待核验（巴黎高师/巴黎-萨克雷体系）"},
 {"s":"u_cambridge","t":"c_quantinuum","rel":"学校孵化","w":2,"note":"前身 CQC 2014 年经剑桥大学 Accelerate Cambridge 项目创立"},
 {"s":"c_ctquantum","t":"c_quantumctek","rel":"投资/持股","w":3,"note":"2025 年 1 月起为控股股东（直接持股 21.86%，合计表决权 40.43%，实控人国务院国资委）"},
 {"s":"c_ctquantum","t":"u_ustc","rel":"联合研究","w":1,"unc":True,"note":"“天衍-287”采用中科大“祖冲之三号”同款芯片，合作形式待核验"},
 {"s":"u_ustc","t":"c_wentian","rel":"学校孵化","w":2,"note":"2009 年由芜湖投控与中科大共同发起设立"},
 {"s":"s_guo","t":"c_wentian","rel":"任职/创办","w":2,"note":"联合创始人"},
 {"s":"s_han","t":"c_wentian","rel":"任职/创办","w":2,"note":"创始人、董事长兼首席科学家"},
 {"s":"u_siegen","t":"c_eleqtron","rel":"学校孵化","w":2,"note":"量子光学教席 spin-off（2020）"},
 {"s":"s_wunderlich","t":"c_eleqtron","rel":"任职/创办","w":2,"note":"联合创始人"},
 {"s":"u_ustc","t":"c_guoyao","rel":"学校孵化","w":1,"unc":True,"note":"潘建伟团队与窦贤康团队技术作价入股，细节待核验"},
 {"s":"u_ustc","t":"c_gkqn","rel":"学校孵化","w":1,"unc":True,"note":"中科大科技成果作价入股，细节待核验"},
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
