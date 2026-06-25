# 里程碑3 统计/选号 彩种切换 设计（note 29）

**目标：** 给「号码统计」和「选号」两页加上彩种切换（复用 `LotteryTabs`），与其它页面一致。纯前端。

## 背景

`draw/stats.vue` 和 `mine/picker.vue` 都直接读 `lotteryStore.code`，页面内无法切换彩种 —— 想看别的彩种统计/选别的彩种号，得先去别处切。note 29 要求这两页也能切。

## 方案

### 一、统计页 `draw/stats.vue`（简单接线）

- 顶部加 `LotteryTabs`（`:list="lotteries" :active="store.code" @change="onChange"`）。
- `onShow` 里若 `lotteries` 为空则 `getLotteryList()` 填充。
- `onChange(code)`：`setCode(code)` 后 `load()`（统计随当前 `lotteryStore.code` 拉取）。
- 其余统计逻辑不变。

### 二、选号页 `mine/picker.vue`（需小重构）

现状：`const code = lotteryStore.code` 在 setup 时一次性捕获，`onLoad` 内据此拉 `rule_config` 并初始化选号状态；多处 api 调用直接用 `code` 常量。要支持切换需：

- 用 `const store = lotteryStore`，把所有 `code` 引用改为 `store.code`（`doGenerate`/`saveOne`/`reportAccess`）。
- 抽出初始化函数 `initRule()`：从已拉取的彩种列表 `lotteries` 中找到 `store.code` 的 `rule_config`，重置选号状态（`sel` 结构、`sets`、`selected`、`pickCount`、`note`、`targetIssue`）；找不到则置空态。
- 顶部加 `LotteryTabs`；`onChange(code)`：`setCode(code)` → `initRule()`。
- `onLoad` 改为：拉 `getLotteryList()` 存入 `lotteries` ref，再 `initRule()`。
- 切换彩种时 `mode` 保留（机选/手动），其余选号上下文清空，避免把旧彩种的号码/期号带到新彩种。

### 三、彩种列表持有

两页都新增 `lotteries` ref 持有 `getLotteryList()` 结果，供 `LotteryTabs` 渲染与 picker 的 `initRule()` 查 rule，避免每次切换重复请求。

## 文件

- 修改：`lottery_frontend/src/pages/draw/stats.vue`
- 修改：`lottery_frontend/src/pages/mine/picker.vue`

## 测试

- 这两页改动均为组件内接线/状态重置（依赖 uni 运行时 + getLotteryList），项目无 .vue 组件级单测；靠现有 `picker.js`/`statsort.js`/`zones.js` 单测保证底层逻辑不变 + 全量回归 + 手测。
- 全量前端测试须保持通过（无回归）。
- 手测要点：两页能切彩种并正确刷新；选号页切换后旧彩种的已选号码/机选结果/期号被清空、玩法选项随新彩种刷新。
