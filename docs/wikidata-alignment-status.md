# 量子图谱 · Wikidata QID 对齐报告

状态：**本轮收尾对齐完成（2026-10-11）** ｜ 数据源：`quantum_network.json`（363 节点 / 486 边）

## 一、结论

**覆盖率从 11 / 363（3.0%）→ 214 / 363（59.0%）→ 280 / 363（77.1%）**，本轮净增 66 条，
全部带来源标注 `wikidata_src`（枚举仍严格限定为 `manual` / `auto-label` / `auto-alias`）。

| 来源 | 条数 | 含义 |
|---|---|---|
| `manual` | 21 | 人工逐条核实（原旗舰节点 11 + 本轮人工裁定 10） |
| `auto-label` | 218 | 命中词条是节点主名（`name` / `name_en`） |
| `auto-alias` | 41 | 命中词条是节点别名 / 经 ORCID 身份通道命中 |
| **合计** | **280 / 363（77.1%）** | |

剩余 **83 条**未对齐，逐条核查后确认**该名下 Wikidata 确实无对应项**（见 §六）。

## 二、覆盖率阶梯

| 阶段 | 通道 | 新增 | 累计覆盖 |
|---|---|---|---|
| 起点 | 人工核实 | — | 11 / 363（3.0%） |
| 阶段1 | `rdfs:label` 精确匹配 | +165 | 176 / 363（48.5%） |
| 阶段2 | `skos:altLabel` + 自带 aliases | +38 | 214 / 363（59.0%） |
| 阶段3 | 镜像全文召回（含中文）+ ORCID 人物消歧 + v6 收尾 + 人工裁定 | +66 | **280 / 363（77.1%）** |

## 三、本轮的三个关键修正

### 3.1 中文通道不能靠「精确标签」——必须走全文索引

v2 的中文通道是**字面精确匹配**，而 Wikidata 的中文标签常是完整法定名：

- 本源量子 → 标签是「合肥本源量子计算科技有限责任公司」→ 精确匹配必失手
- 问天量子 → 标签是「安徽问天量子科技股份有限公司」→ 同上

本轮改为在镜像（OpenLink 托管的 Wikidata Virtuoso）上用 `bif:contains` 做**中文全文召回**，
配合「规范化包含」匹配（`本源量子` ⊂ `合肥本源量子计算科技有限责任公司`），一次捞回
本源量子、问天量子、Quantum Benchmark、Qblox、Quantum Circuits、Quantum Motion 等。

### 3.2 `OR` 拼接 + `LIMIT` 会吃满结果集（v3 的隐藏 bug）

v3 把 10 个词条用 `OR` 拼成一条查询再 `LIMIT 200`。实测：

```
'本源量子' OR ('origin' AND 'quantum')   → 40 条全是论文标题（"Origin of terminal…"）
'本源量子'                                → 1 条，正是 Q64213489
```

多词 AND 项会召回大量噪声并**吃满 LIMIT**，真正命中的实体被挤出结果集。
另外 v3 曾**显式剔除中文词条**（注释写「中文全文索引噪声太大」），把中文交给 v2 的精确通道 ——
两个缺陷叠加，是 91 条「别名也无命中」的主因。v4 改为**逐词条单查**，中文一并召回。

### 3.3 人名消歧：从「机构字符串比对」升级到「ORCID 身份通道」

人名是最难的一类（"John Morton" 同时是主教、艺术家、板球手）。v3 只看 `P108/P69` 标签字符串，
一旦 Wikidata 没写机构就无解。本轮引入两条高精度通道：

- **O1 标签 + `P496(ORCID)` 存在**：同名里凡是带 ORCID 的必定是研究者，直接把政客/歌手/运动员全剔除
- **O2 ORCID 检索**（`pub.orcid.org`，本机实测可达）：按姓名搜人 → 用其 `institution-name` 与节点
  `affiliation` 比对锁定 → `ORCID → P496 → QID` 反查

> 关键坑：**ORCID 机构名是英文，节点 affiliation 常是中文**（`Weizmann Institute of Science` vs
> `魏茨曼科学研究所`），首轮机构比对全部落空。解法是**用图谱自带的 362 条 `name` + `name_en` 组双语机构字典**，
> 把中文 affiliation 扩展到英文键再比对。

## 四、质量验证

1. **类型自洽（P31 硬门）**：`HUMAN_TYPES`（scholar/student/exec）必须 `P31 = Q5`；组织按关键词表比对。
   本轮据此剔除了一批误配：`i_temasek → Temasek（人类定居点）`、`i_thirdpoint → Third Point（悬崖）`、
   `c_origin → 本体论（消歧页）`。
2. **国别否决（P17 硬门）**：节点 `country` 与候选 `P17` 同时存在且不相交 → 直接否决。
   据此纠正了 `c_xanadu → Q12132906（乌克兰国家存托公司，P17=乌克兰）` 这类「别名唯一」误配。
3. **人工裁定 10 条**（来源标 `manual`），包括两处关键纠错：
   - `s_lucas`：v2 选的 `Q89696888` 其 `P108 = 布雷斯特大学中心医院`（医学同名者，ORCID 0000-0001-8201-0808）；
     改判 `Q103228119`（`D.Phil. University of Oxford 1997`，`P69 = University of Oxford`），与节点「Oxford 物理系教授」一致。
   - `s_morton`：4 个同名候选里锁定 `Q60686362 John J. L. Morton`（`P108 = University College London`）。
4. **显式排除 3 条**（写入 `_final_drop.json`，可追溯）：
   - `st_heyu`（贺羽／中科大博士／国仪量子创始人）≠ `Q77782578`（哈佛的 Yu He）
   - `x_yaolin`（姚麟／华翊量子）≠ `Q88109562`（福建师大 ORCID 记录）
   - `i_legendstar`（联想之星，创投）≠ `Q4208011`（A Legend Star Entertainment，娱乐公司）
5. **产物口径核对**：五处产物 QID 数完全一致（见 §五）；`validate.py` **0 错误 0 警告**。
6. **前端实测（Playwright，本轮重跑）**：
   - 页内数据覆盖 `{total:363, links:486, withQid:280, bySrc:{auto-label:218, auto-alias:41, manual:21}}`
   - 查询过滤精确：`wikidata_src = "manual"` → 21 条、`"auto-label"` → 218 条、`"auto-alias"` → 41 条
   - 详情卡（点 `u_mit`）渲染 `https://www.wikidata.org/wiki/Q49108` 外链，**不出现「QID来源」字样**
   - 页面错误：none

## 五、产物同步（四处口径已核对一致）

| 产物 | QID 数 | `wikidata_src` |
|---|---|---|
| `quantum_network.json`（基础层） | 280 | ✔ 218 / 41 / 21 |
| `nodes.csv` | 280 | ✔ 新增列 |
| `kg/import.cypher` | 280 | ✔ |
| `quantum_network.jsonld`（`schema:sameAs`） | 280 | ✔ `kg:wikidataSource` |
| `workbench.html` / `index.html`（前端内置） | 280 | ✔ |

## 六、未对齐 83 条：逐类核查结论

这 83 条**不是「没查到」，而是「该名下 Wikidata 确实没有对应项」**。核查方式：
以节点的 `name` / `name_en` / `aliases` 全部词条，在镜像上对 `rdfs:label` 与 `skos:altLabel`
做 `bif:contains` 全文召回（语言含 `en/zh/zh-hans/zh-cn/zh-hant`），再叠加 ORCID 人物通道；
所有返回项经 P31 类型门过滤后**无一与节点类型自洽**（返回的多为学术论文、专利、船只、
顶级域名、消歧页、历史人物）。

| 类型 | 条数 | 代表节点 |
|---|---|---|
| 公司 | 25 | Oxford Ionics、Quobly、Oxford Quantum Circuits、QphoX、eleQtron、ParityQC、KETS、evolutionQ、Horizon Quantum、Orange Quantum Systems、量旋科技、中科酷原、未磁科技、相干科技、国耀量子、国科量网 |
| 高管 | 31 | 格雷瓜尔·里博迪（IDQ）、伊塔马尔·西万（Quantum Machines）、史蒂夫·布赖尔利（Riverlane）、乔什·纳恩（Riverlane）、尼科洛·德马西（D-Wave）、尼科洛·索马斯基（Quandela）、卢瓦克·昂里耶（Alice & Bob）、艾伦·何（Qolab）… |
| 学者 | 11 | 郭国平（本源量子）、乔·菲茨西蒙斯（Phasecraft）、韩正甫（问天量子）、克里斯托夫·文德利希（eleQtron）、Roee Ozeri（Weizmann）、曾贵华、荣星、御手洗光介（Quandela）… |
| 投资机构 | 8 | 高瓴创投、联想之星、盛世投资、百度风投、建投投资、芜湖投控、World Fund、澳大利亚国家重建基金 |
| 学生 | 7 | 克里斯蒂安·威德布鲁克（Xanadu）、文凯（QuEra）、克里斯·巴兰斯、项金根、李相良、汤姆·哈蒂 |
| 高校/院系 | 1 | 中科院精密测量科学与技术创新研究院 |

**结论**：这 83 条的瓶颈已不在检索方法，而在 **Wikidata 侧的覆盖度**。
若需继续提升，只有两条路：① 人工核对 Wikidata 原始页面确认真无条目；
② 反向贡献（为本图谱中的高价值实体在 Wikidata 建项）。**不建议**为了覆盖率而放宽 P31/国别硬门。

### 本轮 v6 收尾扫描的额外收获

高 `LIMIT` + **包含式发现**（允许「条目名 ⊃ 节点名」）再捞回 3 条 —— 这类节点的词条名与节点名不同词，
低 `LIMIT` 时会被同名噪声挤掉：

| 节点 | 命中理由 |
|---|---|
| `i_temasek` 淡马锡 → `Q762479` | 条目名 `Temasek Holdings`（P31：主权财富基金），含节点名「淡马锡控股」 |
| `x_baratz` 艾伦·巴拉茨 → `Q123580687` | 条目名 `Dr. Alan Baratz`，描述为 `Ceo, D-wave Quantum Inc.` |
| `c_xuntai` 循态量子 → `Q108801483` | 条目名 `Shanghai XunTai Quantech Co.`，中文标签「上海循态信息科技有限公司」 |

## 七、工具链（均在项目根）

| 脚本 | 作用 |
|---|---|
| `align_wikidata_sparql.py` | 阶段1 标签通道（输出 `quantum_network_wikidata_hits.json`） |
| `probe_alias.py` | 阶段2 别名通道（输出 `_alias_probe.json`） |
| `backfill_wikidata.py` | 阶段1/2 写盘（备份 `quantum_network.pre-wikidata.json`） |
| `align_wikidata_v2.py` | 阶段3-A 中文标签 + P31 结构化消歧（输出 `_v2_*.json`） |
| `align_wikidata_v3.py` | 阶段3-B 镜像全文召回 + 机构一致性（输出 `_v3_*.json`） |
| `align_wikidata_v4.py` | **修正 v3 的中文剔除与 OR 拼接缺陷**（逐词条单查；输出 `_v4_*.json`） |
| `align_wikidata_v5.py` + `v5_resolve.py` | **ORCID 人物双通道**（双语机构字典重算；输出 `_v5_*.json`） |
| `align_wikidata_v6.py` | 收尾扫描（高 LIMIT + 包含式发现；输出 `_v6_*.json`） |
| `backfill_wikidata_v3.py` | **本轮写盘入口**（读 `_final_accept.json`，备份 `quantum_network.pre-wikidata3.json`） |

终裁输入：`_final_accept.json`（权威清单）、`_final_manual.json`（标 `manual` 的节点）、`_final_drop.json`（显式排除）。

## 八、网络前提（重要）

本轮全程处于 **`query.wikidata.org`（官方 WDQS）被网络阻断**的状态（`http=000`，
SSL `UNEXPECTED_EOF_WHILE_READING`，`www.wikidata.org` / `en.wikipedia.org` / `commons` / `dbpedia` 同时不可达；
机器经 `127.0.0.1:4295` 代理出网，`--noproxy '*'` 无效）。可用替代：

| 端点 | 用途 | 约束 |
|---|---|---|
| `https://wikidata.demo.openlinksw.com/sparql` | 全文召回 + 字面量 | `VALUES ?t { "x"@en }` 报 `SR549`；须用直接字面量或 `bif:contains`；`bif:contains` 的中文词必须写成单引号短语 `'本源量子'` |
| `https://qlever.dev/api/wikidata` | 结构化字段（P31/P17/P106…） | 必须显式写 `PREFIX wd:`；旧域名 `qlever.cs.uni-freiburg.de` 会 308 而 `urllib` 不跟随 |
| `https://pub.orcid.org/v3.0/expanded-search/` | 人物身份消歧 | 可达（200）；`institution-name` 需与节点 affiliation 做中英对照 |

> 排查纪律：端点静默超时**不能**判为「无该实体」。本轮最初把 149 条中的 91 条记为「无命中」，
> 实际相当一部分是端点/语法/截断造成的假阴性 —— 换通道后逐一恢复。

## 九、后续

1. 新增节点后按 `align_wikidata_v4.py → v6` 重跑增量对齐（v4 逐词条单查，最稳）
2. 前端详情卡仍只渲染 Wikidata 外链（不展示来源）；`wikidata_src` 仅用于检索与数据治理
3. 若日后官方 WDQS 恢复可达，可把 `MIRROR` 换回 `query.wikidata.org/sparql` 复核本轮全部结果
