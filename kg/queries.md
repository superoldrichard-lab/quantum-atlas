# 量子图谱 · Cypher 查询示例库

所有查询均已在 `kg/query.py`（grandcypher 引擎）上实测通过，结果为真实运行输出。

**运行方式**（在项目根目录）：

```bash
"C:/Users/Boss/.workbuddy/binaries/python/envs/default/Scripts/python.exe" kg/query.py "<查询>"
# 叠加推断层（同门/共同投资/学派/桥梁）时加 --inferred
```

**语法约束（grandcypher 子集）**：
- 字符串字面量必须用**双引号**：`WHERE r.rel = "师承"`
- 关系类型不写 `[r:类型]`，用 `WHERE r.rel = "..."` 过滤
- 不支持 `OPTIONAL MATCH`、聚合函数（count/sum）；聚合统计见 `inference_report.md`
- 布尔属性直接比较：`WHERE r.unc = true`；取反用 `NOT a = b`

---

## 一、学术谱系

### Q1 某导师的直接学生
```cypher
MATCH (m)-[r]->(s) WHERE r.rel = "师承" AND m.id = "s_pan" RETURN m.name, s.name
```
```
潘建伟 → 陆朝阳 / 陈宇翱 / 金贤敏   （3 行）
```

### Q2 某学派全体成员（推断层）
```cypher
MATCH (n) WHERE n.school = "安东·蔡林格学派" RETURN n.name, n.schools_all
```
```
Thomas Jennewein | 安东·蔡林格学派
陆朝阳 / 陈宇翱 / 金贤敏      | 安东·蔡林格学派｜潘建伟学派
安东·蔡林格       | 安东·蔡林格学派            （5 行）
```
> `school` 为主学派（学派根本人以自己命名），`schools_all` 为完整多重归属。

### Q3 某国学者的师承输出
```cypher
MATCH (m)-[r]->(s) WHERE r.rel = "师承" AND m.country = "英国" RETURN m.name, s.name
```
```
大卫·卢卡斯 → 克里斯·巴兰斯   （1 行）
```

### Q4 旗舰学者清单（权重 ≥ 9）
```cypher
MATCH (n) WHERE n.type = "scholar" AND n.weight >= 9 RETURN n.name, n.country, n.weight
```
```
蔡林格/姚期智/肖尔/普雷斯基尔/阿斯佩/潘建伟(10)；
卢金/吉桑/佐勒/德沃雷/布洛赫/叶军/埃克特/洛斯/马蒂尼斯/西拉克/门罗/舍尔科普夫/薛其坤(9)   （19 行）
```

---

## 二、产业与资本

### Q5 某公司的投资方
```cypher
MATCH (i)-[r]->(c) WHERE r.rel = "投资/持股" AND c.id = "c_quantumctek" RETURN i.name, i.type
```
```
中电信量子集团(company) / 中国电信集团(investor)   （2 行）
```

### Q6 某高校孵化的全部公司（含融资阶段）
```cypher
MATCH (u)-[r]->(c) WHERE r.rel = "学校孵化" AND u.id = "u_ustc" RETURN c.name, c.funding
```
```
国盾量子(科创板 688027) / 本源量子(Pre-IPO 210 亿) / 国仪量子(科创板 688828)
问天量子(B 轮 6 亿) / 国耀量子 / 国科量网   （6 行）
```

### Q7 跨国投资流向（资本出海/入华）
```cypher
MATCH (i)-[r]->(c) WHERE r.rel = "投资/持股" AND NOT i.country = c.country
RETURN i.name, i.country, c.name, c.country
```
```
腾讯(中国)→IQM(芬兰)；软银(日本)→QuEra(美国)/Classiq(以色列)；
淡马锡(新加坡)→Pasqal(法国)/PsiQuantum(美国)；IonQ→IDQ(瑞士)/Oxford Ionics(英国)/Classiq(以色列) 等   （14 行）
```

### Q8 跨境桥梁节点（推断层，投资视角关键通道）
```cypher
MATCH (n) WHERE n.bridge = 1 RETURN n.name, n.country, n.bridge_countries
```
```
IonQ(美国)→以色列｜瑞士｜英国；IQM(芬兰)→中国｜德国｜美国；
文凯(中国)→日本｜美国；软银→以色列｜美国；淡马锡→法国｜美国 等   （9 行）
```

### Q9 共同投资网络（推断层）
```cypher
MATCH (a)-[r]->(b) WHERE r.rel = "共同投资" RETURN a.name, b.name, r.note
```
```
中网投｜君联｜联想之星｜盛世投资（共同被投：图灵量子）；
高榕｜百度风投｜建投投资｜君联（华翊量子）；霍尼韦尔｜JPMorgan｜NVentures（Quantinuum）等   （31 行）
```

---

## 三、数据质量审计

### Q10 全部不确定边（待人工核验清单）
```cypher
MATCH (a)-[r]->(b) WHERE r.unc = true RETURN a.name, r.rel, b.name
```
```
44 行：如 舍尔科普夫-师承→里盖蒂、伯克利-孵化→Atom、潘建伟-任职/创办→国盾量子 等
```
> 这是图谱的"自检口"：任何一轮数据修订后重跑此查询，核验清单应只减不增。

### Q11 同门关系（推断层）
```cypher
MATCH (a)-[r]->(b) WHERE r.rel = "同门" RETURN a.name, b.name, r.note
```
```
金贤敏｜陆朝阳｜陈宇翱（共同导师：潘建伟）；郭国平｜韩正甫（郭光灿）；
Jennewein｜潘建伟（蔡林格）   （5 行）
```

---

## 迁移到 Neo4j 时

以上查询在 Neo4j 中同样成立，只需两处调整：关系类型可写为 `[:`师承`]` 原生化；
聚合类问题（如"投资组合规模最大的机构"）可用 `WITH count(*) AS c ORDER BY c DESC` 直接表达。
导入：Neo4j Browser 执行 `kg/import.cypher` 全量脚本即可。
