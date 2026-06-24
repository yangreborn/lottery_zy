# 开奖展示/导航 Bug 批量修复 · 设计文档

- 日期：2026-06-24
- 定位：修复测试中发现的 7 个展示/导航问题（金额解析、奖级表、历史页彩种选择、返回按钮）。纯前端，不动后端/已入库数据。
- 来源：用户在 H5/小程序实测反馈。

---

## 0. 范围

**本期做**：① formatAmount 解析千分位逗号；② 奖级表组件化（过滤空行 + 快乐8码翻译/分组折叠 + 列对齐）；③ 历史页加彩种切换；④ TopBanner 加返回按钮。
**不做**：不改后端、不改爬虫、不动已入库 DrawResult 数据（金额带逗号是官方原值，前端解析即可）。

## 1. 金额解析（问题 1、3）

- 现象：大乐透奖池/奖金显示 `-元`。
- 根因：奖池/奖金官方值带千分位（`757,966,457.83`、`7,110,906`），`formatAmount` 用 `Number('757,...')`→NaN→`—`；双色球无逗号才正常。
- 修复：`utils/format.js` 的 `formatAmount` 在 `Number()` 前 `String(raw).replace(/,/g, '')` 去逗号。

## 2. 奖级表组件化（问题 2、4、6）

抽共享组件 `components/PrizeGrades.vue`（latest/detail 共用），逻辑放纯函数 `utils/prize.js` 的 `normalizePrizes(grades)`：
- **过滤空行**（问题 6）：剔除 `count` 为空串/None 的行（福彩给双色球返回的空"7等奖"占位）。
- **快乐8码翻译 + 分组**（问题 4）：奖级码 `x{pick}z{hit}`（如 `x10z10`）→ `选{pick}中{hit}`；按 pick 分组为"选10…选1"，每组**默认折叠**、点击展开。
- **奖级中文**：数字 level（双色球 1–6）→ `一等奖…`；字符串 level（大乐透"一等奖"）原样。
- **列对齐**（问题 2）：奖级/注数/单注奖金固定三列（flex 2/1/2，左/中/右对齐）。
- `normalizePrizes` 返回 `{grouped:false, flat:[{label,count,amount}]}` 或 `{grouped:true, groups:[{pick,label,rows:[{label,count,amount}]}]}`。
- latest.vue / detail.vue 用 `<PrizeGrades :grades="draw.prize_grades" />` 替换原奖级表块。

## 3. 历史页彩种选择（问题 5）

- 现象：历史开奖不能选彩种，固定双色球。
- 根因：`history.vue` 无 `LotteryTabs`（当期页有）。
- 修复：history.vue 加 `LotteryTabs`（onMounted 拉 getLotteryList），切换彩种 setCode + 重新拉该彩种历史（reset 分页）。

## 4. 返回按钮（问题 8）

- 现象：号码统计、选号记录无返回按钮。
- 根因：二者是 tabBar 页（从首页菜单 switchTab 进入），tabBar 页无原生返回。
- 修复：`TopBanner` 加可选 `back` 布尔 prop —— 显示"‹ 返回"，点击：`getCurrentPages().length>1` 则 navigateBack，否则 `switchTab` 回首页。在 tabBar 内容页（stats / picker / mine-index）启用 `:back="true"`；navigateTo 进入的页（latest/history/detail/guide）本有原生返回，不启用避免重复。

## 5. 测试

- vitest：`formatAmount('7,110,906')` 正确解析；`normalizePrizes` —— 双色球过滤空 7 等奖 + level 中文、快乐8 翻译 `x10z10`→选10中10 + 按 pick 分组降序、空数组安全。
- 人工：起后端 dev:h5 看 大乐透奖池/奖金有值、快乐8奖级折叠展开、历史页可切彩种、统计/选号页有返回。

## 6. 里程碑定位

实测 bug 批量修复（金额/奖级/历史彩种/返回）。不影响后续 A2（3D/排列三）。
