# 全球量子技术图谱 · Quantum Academia Atlas

数据截至 **2026-10-05**（两轮检索：2026-10-04 首轮 + 2026-10-05 扩充轮）。覆盖量子计算、量子通信、量子传感与测量三个方向下：
**高校/研究机构 — 学者（教授/课题组负责人）— 研究生/博士后 — 量子技术公司** 及其关系网络。

## 交付物

| 文件 | 说明 |
|---|---|
| `quantum_atlas.html` | **自包含单文件交互页面**（约 3.7 MB，数据与图像全部内嵌，无任何外部依赖，可直接双击打开）。节点以真实人物照片/机构校徽/公司 Logo 呈现（圆形裁剪，无图者回退为首字母徽章）。支持缩放、拖拽、搜索定位、下拉折叠式筛选面板（类型/地区/国家/研究方向/关系类型，标题行实时显示选择摘要）、按类型或地区着色切换、点击节点弹出详情卡片（含头像、来源链接与不确定项）。**简化视图**默认开启：概览缩放下自动遮挡小节点与重叠标签（枢纽与悬停/搜索焦点始终可见，放大后逐步显现），可在左侧"显示选项"关闭。 |
| `quantum_atlas.json` | 结构化主数据（canonical）。`meta` 含词表与数据说明；`nodes` 223 个；`links` 226 条。 |
| `nodes.csv` / `links.csv` | 便于 Excel 分析的镜像导出（UTF-8 BOM）。 |
| `build_atlas.py` | 数据构建与校验脚本（引用完整性、自环、重复 ID 检查），可复现。 |
| `template.html` | 页面模板（数据占位符注入后生成最终 HTML）。 |

## 数据规模

- **364 个节点**：高校/研究机构 56 · 学者 94 · 研究生/博士后 13 · 公司 60
- **226 条关系**：任职任教 94 · 创办 62 · 孵化 43 · 师承指导 11 · 联合研究 8 · 培养输送 6 · 任职(企业) 2
- 覆盖 18 个国家/地区：美国、加拿大、英国、德国、法国、瑞士、荷兰、奥地利、丹麦、芬兰、西班牙、以色列、中国、中国香港、日本、韩国、新加坡、澳大利亚
- 地区分布：欧洲 96 · 北美 71 · 东亚 39 · 大洋洲 11 · 东南亚 4 · 中东 2

## 数据字典

节点字段：`id, type(university|scholar|student|company), name, name_en, country, region, city, dept(院系), role(学生身份), advisor(导师), now(现职), field(研究方向，受控词表), homepage(实验室主页), honors, founded(成立年份), stage(融资阶段，含时间), business, status, note, sources(来源URL), uncertain(不确定项)`

关系字段：`source, target, type, strength(1一般/2重要/3核心), note, sources, uncertain`。
关系类型：`affiliation 任职任教 · phd_advisor 师承指导 · alumni 培养输送 · collaboration 联合研究 · founded 创办 · incubated 孵化 · employment 任职 · investment 投资`（本批未发现可核实的高校/学者作为投资方的公开实例，故无 investment 边）。

## 方法与诚实性声明

1. **来源**：所有实体与关系均通过公开网络检索核实（两轮合计约 70 次，官网、新闻稿、权威媒体、维基百科等），每条数据附 `sources` 链接；少数来源仅为站点级链接。
2. **缺失即留空**：未核实的字段一律为空，不编造。无法完全确认的说法写入 `uncertain` 数组（页面上以 ⚠ 和虚线边呈现）。
3. **样本而非名录**：这是"强来源优先"的精选样本，不是穷尽式清单；学生/博后仅收录公开报道充分者（PhD 后创业、一作里程碑论文等）。
4. **时效**：公司融资阶段为检索时可查证的最新一轮并注明时间；职务变动如实记录（如 Devoret 2025 年获诺奖并任 Google 量子硬件首席科学家、杜江峰 2025 年起任教育部副部长、Zapata AI 2024 年停运、Oxford Ionics / ID Quantique 被 IonQ 收购、Infleqtion 与 Terra Quantum 推进 SPAC 上市、Laflamme 已于 2025 年逝世等）。
5. **重要更正**：Hyunseok Jeong 在首尔国立大学（而非高丽大学）；Rob Schoelkopf 仍在耶鲁（跳槽马里兰系误传），均已按核实结果收录。
6. 已知不确定项示例：de Leon 是否转任斯坦福、Hafezi 是否转任乔治梅森、QCI 的 Devoret 联合创始人身份、Kipu/Quantum Art/Atomionics 的学术渊源、部分代尔夫特分拆公司成立年份等——均已在数据中标注。

## 简化视图（节点遮挡）与节点图像说明

- 默认开启：概览缩放下，屏幕半径低于阈值的"学生/学者"小节点自动遮挡（本轮实测：223 节点概览显示约 128 个，遮挡 95 个）。
- **永不遮挡**：枢纽节点（连接数 ≥6）、当前悬停/选中节点的邻居、搜索命中节点——保证上下文完整。
- 放大即显现：滚轮放大后小节点逐步回归；左侧"显示选项"可关闭简化视图查看全部。
- 标签避让：标签按优先级（焦点 > 类型 > 连接数）放置，重叠者自动省略，避免文字糊成一团。
- 节点图像：134/223 个节点使用真实图像——人物照片来自维基百科（Wikimedia，各自版权，多为 CC-BY-SA 或公有领域），大学校徽与公司 Logo 来自维基百科页面图或官网 favicon（商标归各自机构所有，此处仅作识别性使用）；其余 89 个节点（多为无公开照片的学者/学生）回退为配色首字母徽章。图像以 base64 内嵌于 HTML，亦独立存放于 `atlas-img.json`。左侧筛选面板为**下拉折叠式**（手风琴单开），标题行右侧实时显示当前选择（"全部 / 名称 / 已选 N/M"）。

## 复现

```bash
python build_atlas.py          # 重新生成 quantum_atlas.json / nodes.csv / links.csv
python - <<'PY'
tpl = open('template.html', encoding='utf-8').read()
data = open('quantum_atlas.json', encoding='utf-8').read()
open('quantum_atlas.html','w',encoding='utf-8').write(tpl.replace('__ATLAS_DATA__', data))
PY
```
