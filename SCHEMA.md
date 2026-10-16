# 全球量子技术知识图谱 · Schema 本体文档

版本：v1.2（2026-10-09，新增「判断层：技术路线分派」） ｜ 数据文件：`quantum_network.json`（v8：363 节点/486 边） ｜ 校验器：`validate.py`（0 错误 0 警告方可入库）

## 1. 实体类型（节点 type）

| type         | 中文         | ID 前缀 | 说明                              |
| ------------ | ---------- | ----- | ------------------------------- |
| `university` | 高校/研究机构    | `u_`  | 含大学、国家实验室、研究所（MPQ、ICFO、RIKEN 等） |
| `scholar`    | 教授/课题组负责人  | `s_`  | 含教授、研究员、学派奠基人                   |
| `student`    | 研究生/博后（校友） | `st_` | 主要在创业或产业化中有节点价值的学生辈人物           |
| `exec`       | 企业创始人/高管   | `x_`  | 非学者身份为主的公司创始人、CEO、CTO           |
| `company`    | 公司         | `c_`  | 量子技术企业（含被收购、已上市主体）              |
| `investor`   | 投资机构       | `i_`  | VC、主权基金、战投方（含腾讯、中电信等产业方）        |

## 2. 关系类型（边 rel）与定义域/值域约束

**方向语义：边一律从「主体」指向「客体」。** `师承` 的方向是 **导师 → 学生**（读作"指导"）。

| rel     | 定义域（source）          | 值域（target）           | 语义                     | 典型 w |
| ------- | -------------------- | -------------------- | ---------------------- | ---- |
| `师承`    | scholar              | scholar/student/exec | 博士/博后指导关系              | 3    |
| `联合研究`  | 任意                   | 任意                   | 合作研究、联合实验、联合发表         | 2    |
| `学校孵化`  | university           | company              | spin-off/技术作价入股/团队发起设立 | 2–3  |
| `任职`    | scholar/student/exec | university/company   | 教职、学位授予院校、博后经历         | 1–2  |
| `任职/创办` | scholar/student/exec | company              | 联合创立、任首席科学家/CTO 等      | 3    |
| `投资/持股` | investor/company     | company              | 投资、并购、控股               | 1–3  |

## 3. 字段字典

### 3.1 全类型公共字段

| 字段           | 必填 | 类型       | 说明                                       |
| ------------ | -- | -------- | ---------------------------------------- |
| `id`         | ✓  | string   | 唯一，符合类型前缀 + 小写字母/数字                      |
| `type`       | ✓  | enum     | 见 §1                                     |
| `name`       | ✓  | string   | 中文名（无中文译名时用原文）                           |
| `name_en`    | 建议 | string   | 英文/原文名                                   |
| `country`    | ✓  | string   | 所在国家/地区（中文）                              |
| `region`     | ✓  | enum     | `北美` / `欧洲` / `中国` / `亚太及其他`             |
| `fields`     | 建议 | enum[]   | `量子计算`/`量子通信`/`量子传感与测量`/`量子软件与算法`/`量子网络` |
| `weight`     | ✓  | int 1–10 | 影响力权重，口径见 §4                             |
| `intro`      | ✓  | string   | 一句话简介（悬停/详情卡片展示）                         |
| `source`     | 建议 | URL      | 主要信息来源链接                                 |
| `note`       | 可选 | string   | 补充说明                                     |
| `uncertain`  | 可选 | string[] | 该实体未核验事项清单（每条一句话）                        |
| `wikidata`   | 可选 | string   | Wikidata QID（形如 `Q78610`）。填值须同时给 `wikidata_src` |
| `wikidata_src` | 可选 | enum    | QID 来源分级：`manual` / `auto-label` / `auto-alias`（口径见 §6） |
| `aliases`    | 可选 | string[] | 别名/曾用名/常用缩写（如 `MIT;麻省理工`），检索与消歧用         |
| `verified`   | 可选 | enum     | `是`=外部核实（有官方/权威来源）/`否`=未核实，缺省视为未核实       |
| `verif_note` | 可选 | string   | 核实结论摘要（核实轮产出，如核实依据与日期）                   |

### 3.2 类型专属字段

- `company`：`founded`（成立年份）、`hq`（所在地）、`funding`（融资阶段/金额/估值）、`business`（主营业务/技术路线）
- `scholar`/`student`：`affiliation`（任职机构）、`dept`（院系）、`title`（职称/身份）、`lab`（实验室主页 URL）
- `exec`：`company`（任职企业）、`title`（职务）

### 3.3 边字段

| 字段              | 必填 | 说明                                                                            |
| --------------- | -- | ----------------------------------------------------------------------------- |
| `s` / `t`       | ✓  | 端点节点 id，必须存在                                                                  |
| `rel`           | ✓  | 见 §2                                                                          |
| `w`             | ✓  | 1=弱 / 2=中 / 3=强（师承、孵化、创办、控股类一般为 3）                                            |
| `note`          | 建议 | 关系说明（时间、事件依据）                                                                 |
| `unc`           | 可选 | true = 关系未完全核验，图上渲染为虚线                                                        |
| `verif`         | 建议 | enum：`是`=外部核实（权威来源直接支撑，约 44%）/`一致`=一致核验（多来源交叉一致，约 44%）/`否`=未核验（约 12%），缺省视为未核验 |
| `start` / `end` | 可选 | 4 位年份字符串：关系起止（任职起止、投资年份、博后起讫等）                                                |

## 4. 权重评级口径（weight）

| 分值  | 学者        | 公司/机构         | 高校       |
| --- | --------- | ------------- | -------- |
| 10  | 诺奖/图灵奖级   | —             | 全球量子生态旗舰 |
| 9   | 院士/学派奠基人  | 上市且行业龙头       | 顶级量子中心   |
| 7–8 | 知名 PI/院士级 | 上市/巨额融资/收购案主体 | 区域旗舰     |
| 5–6 | 中坚 PI     | 成长期（A–C 轮）    | 有量子方向积累  |
| 3–4 | 新锐/校友创业者  | 早期（种子–天使）     | 一般       |

## 5. 数据纪律（铁律）

1. **缺失留空，绝不编造**——融资、履历、实验室主页等查不到就留空或写"未公开"
2. **不确定项必须标注**——节点 `uncertain`、边 `unc`/`verif=否`（三者图上均渲染为虚线或灰显），并在 note 写明待核验点
3. **来源可溯**——每个实体尽量带 `source`；金额类信息区分「官方披露」与「第三方数据库口径」，后者标 unc
4. **入库前过校验**——`validate.py` 必须 0 错误 0 警告
5. **新增实体先查重**——确认 id 未被占用且不是既有实体的别名

## 6. 实体对齐（Wikidata）

### 6.1 现状

- 对齐方式：节点 `wikidata` 字段存 QID；`wikidata_src` 记录该 QID 的取得方式
- **当前覆盖 280 / 363（77.1%）**：`manual` 21 条、`auto-label` 218 条、`auto-alias` 41 条
- 前端详情卡统一渲染 Wikidata 外链（不区分来源）；来源仅供检索与数据治理使用

### 6.2 来源分级（`wikidata_src`）

| 取值 | 含义 | 置信依据 |
| --- | --- | --- |
| `manual` | 人工逐条核实 | 人工判断 |
| `auto-label` | 命中词条是节点主名（`name` / `name_en`） | 另经 P31 反向校验 |
| `auto-alias` | 命中词条是节点别名（`skos:altLabel` / 节点自带 `aliases`），或经身份通道（ORCID）命中 | 描述命中类型词 |

**只允许这三种取值**；`wikidata` 有值而 `wikidata_src` 为空视为不合规（`validate.py` 报错）。

### 6.3 批量对齐方法与验证

1. **通道可用性**：`www.wikidata.org/w/api.php`（`wbsearchentities`）与 `query.wikidata.org/sparql`（官方 WDQS）
   在部分网络下被整体阻断（实测 `http=000`、SSL `UNEXPECTED_EOF_WHILE_READING`）。可用替代三件套：
   `wikidata.demo.openlinksw.com/sparql`（全文召回）、`qlever.dev/api/wikidata`（结构化字段）、
   `pub.orcid.org/v3.0/expanded-search/`（人物消歧）。**端点超时不得判为「无该实体」**。
2. **回填纪律（三道硬门，缺一不可）**：
   ① `P31` 类型自洽——`scholar`/`student`/`exec` 必须 `Q5`，组织按类型关键词表比对；
   ② `P17` 国别——节点 `country` 与候选 `P17` 同时存在且不相交时**硬否决**；
   ③ 人名身份证据——西文名需「机构一致 或 职业/领域 或 描述命中领域词」，中文名需机构一致。
   门内若仍多候选，按 国别唯一 → 机构唯一 → 职业唯一 收敛；不收敛则留空进复核清单。
3. **反向校验（必做）**：对回填结果逐条取回 Wikidata 的 `P31 (instance of)` 与节点 `type` 比对，类型冲突即剔除。
4. **工具链**（均在项目根）：
   - `align_wikidata_sparql.py` — 阶段1 标签通道（输出 `quantum_network_wikidata_hits.json`）
   - `probe_alias.py` — 阶段2 别名通道（输出 `_alias_probe.json`）
   - `backfill_wikidata.py` — 阶段1/2 写盘（备份 `quantum_network.pre-wikidata.json`）
   - `align_wikidata_v2.py` — 阶段3-A 中文标签精确 + P31 消歧（输出 `_v2_*.json`）
   - `align_wikidata_v3.py` — 阶段3-B 镜像全文召回 + 机构一致性（输出 `_v3_*.json`）
   - `align_wikidata_v4.py` — **修正 v3 的两处召回缺陷**（中文词条被剔除、`OR` 拼接吃满 `LIMIT`），逐词条单查（输出 `_v4_*.json`）
   - `align_wikidata_v5.py` + `v5_resolve.py` — ORCID 人物双通道；`v5_resolve.py` 用图谱自带的
     362 条 `name`+`name_en` 组双语机构字典重算（输出 `_v5_*.json`）
   - `align_wikidata_v6.py` — 收尾扫描（高 `LIMIT` + 包含式发现，处理「条目名比节点名长」的情形，如 Temasek ⊂ Temasek Holdings）
   - `backfill_wikidata_v3.py` — **当前写盘入口**：读 `_final_accept.json`（权威清单）+
     `_final_manual.json`（标 `manual` 的节点）+ `_final_drop.json`（显式排除），
     备份 `quantum_network.pre-wikidata3.json`，含重复/冲突 QID 检测
5. **未对齐部分（83 条）**：逐条经全词条全文召回 + ORCID 通道核查，**该名下 Wikidata 确实无对应项**
   （返回项均为论文/专利/船只/顶级域名/消歧页/历史人物，P31 无一自洽）。
   构成：公司 25、高管 31、学者 11、投资机构 8、学生 7、高校 1。
   逐条清单见 `docs/wikidata-alignment-status.md` §六。
   注：v6 已按「条目名 ⊃ 节点名」再捞回 3 条（Temasek Holdings / Dr. Alan Baratz / Shanghai XunTai），
   写盘入口 `backfill_wikidata_v3.py` 另支持 `_final_accept_v6.json` 与 `_final_src_override.json`。

### 6.4 变更要求

- 回填/修改 QID 后须重跑：`validate.py` → `build.py` → `kg/gen_import_cypher.py` → `export_jsonld.py`，
  确保 `nodes.csv` / `kg/import.cypher` / `quantum_network.jsonld` 三处口径与基础层一致。

## 7. 判断层（技术路线分派，与基础层严格分离）

86 个 `company` 节点的技术路线归类存于独立文件 `tech_routes.json`（**判断层，不回写基础事实层**），
分类框架、判定规则与逐企业依据见 `docs/tech-route-report.md`（资料库一级数据源）。

- 分类口径：**6 个一级领域 × 20 条二级技术路线**（报告 §1.2），每企业唯一主路线（规则 R1）
- 字段：`route`（二级路线）、`route_group`（一级领域）、`confidence`（高/中/低）、`basis`（判定依据）、`route_note`（多路线布局/并购归属变更备注）
- 构建期由 `build.py` 合并进前端数据（与照片合并同机制），前端工具栏「技术路线」下拉框即按此筛选
- 重新生成/校验：`python build_routes.py`（覆盖 86 家企业，缺漏或多余 id 直接报错）；`--table` 同步回填报告第十三章分派表
- 维护触发条件与诚实声明见报告 §14.3 / §14.4

## 8. 推断层（机器推导，与基础层严格分离）

基础图谱（`quantum_network.json`）只存人工录入、可溯源的事实；推断产物一律写入独立文件  
`quantum_network.inferred.json`，**不回写主数据文件**。

### 推断关系类型（2 类，仅存在于推断层）

| 关系   | 规则                    | 方向            | w | 说明           |
| ---- | --------------------- | ------------- | - | ------------ |
| 同门   | R1：共享同一导师（基础层「师承」边）   | 无向（按 id 序存单条） | 1 | note 记共同导师   |
| 共同投资 | R2：共同出现在一家公司「投资/持股」边中 | 无向（按 id 序存单条） | 1 | note 记共同被投企业 |

### 推断节点注释

| 属性                                  | 规则               | 类型         | 说明                                                     |
| ----------------------------------- | ---------------- | ---------- | ------------------------------------------------------ |
| `school`                            | R3：学派传播的主学派      | string     | 学派根（weight≥9 且 ≥2 名在录学生）以自身命名；其余取字典序第一个，便于 Cypher 精确匹配 |
| `schools_all`                       | R3：完整多重归属        | string     | 「｜」分隔                                                  |
| `centrality_deg` / `centrality_btw` | R4：度/中介中心性       | float      | 基于无向化全图                                                |
| `bridge` / `bridge_countries`       | R5：一阶邻居覆盖 ≥2 个外国 | int/string | 国家字段按「/」拆分复合写法后比较                                      |

### 工程约定

- 推断边带 `rule` 属性（R1/R2）与 `inferred: true`（Neo4j 导入时）
- 重算方式：`python kg/infer.py`（同时刷新 `inference_report.md`）
- Neo4j 中的等价 Cypher 规则见 `kg/import.cypher` 第 4 节注释
- 查询入口：`kg/query.py`（grandcypher 引擎），示例库 `kg/queries.md`；推断层属性默认值由 `kg/graph_engine.py` 补齐，保证空属性不报错
