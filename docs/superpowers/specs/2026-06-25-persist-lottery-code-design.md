# 往期开奖记住彩种（持久化全局彩种）· 设计文档

- 日期：2026-06-25
- 定位：修正「进入往期开奖默认双色球、不记住用户上次选择」的问题。对应 note.txt 第 16 项。纯前端。

---

## 0. 范围与意图澄清

note 16 字面为「进入往期开奖要先选彩种再展示」。与用户确认后，真实意图不是做空白引导页强制先选，而是：**往期页照常直接展示，但默认展示「用户上次查看的彩种」（兜底双色球），并记住选择**。

根因：`src/store/lottery.js` 的 `code` 硬编码 `'ssq'` 且不持久化，导致每次进入都回到双色球。

**本期做**：持久化全局彩种 code（读存储初始化 + 选择时写存储）。
**不做**：不改后端；不做空白引导/强制选择浮层；不做彩种合法性校验；不动 history/latest/stats/picker 页（它们已读 `lotteryStore.code`、切换时已调 `setCode`，自动获得「记住上次」效果）。

## 1. 架构（单点改造）

只改 `src/store/lottery.js`。其余彩种相关页面无需改动。

- 存储 key：`'lottery_code'`
- `readStoredCode()`：从 `uni.getStorageSync('lottery_code')` 读取，读不到/异常/无 `uni` 全局时兜底 `'ssq'`。必须带 `typeof uni !== 'undefined'` 守卫并 try 包裹——因为本函数在模块导入时被调用初始化 `code`，而 vitest 为 node 环境无 `uni` 全局，无守卫会导致 import 即崩。
- `lotteryStore = reactive({ code: readStoredCode() })`：导入时即用存储值（或兜底）初始化。
- `setCode(c)`：设 `lotteryStore.code = c` 的同时，`try { uni.setStorageSync('lottery_code', c) }` 持久化（同样 typeof 守卫 + try，写失败不影响内存态）。

## 2. 数据流

1. 任意彩种页加载 → 读 `lotteryStore.code`（已是上次持久化的值或 ssq 兜底）。
2. 用户在往期页（或任意页）切换彩种 → `onChange` → `setCode(code)` → 内存 + 存储同步更新。
3. 下次进入往期/当前开奖/统计/选号 → `lotteryStore.code` 已是上次选的彩种。

## 3. 接口

`src/store/lottery.js` 导出：
- `lotteryStore`（reactive，含 `code`）— 不变
- `setCode(c)`（写内存 + 持久化）— 签名不变，新增持久化副作用
- `readStoredCode()`（新增导出，纯读取函数，便于单测）

消费方（history/latest/stats/picker/detail）的现有引用 `lotteryStore.code` / `setCode(c)` 全部不变。

## 4. 错误处理

- 存储读异常或无 `uni` → `readStoredCode` 返回 `'ssq'`。
- 存储写异常 → 吞掉，内存态 `lotteryStore.code` 仍已更新，不影响本次使用。
- 存了已下架彩种 code（极少）→ 不校验，彩种列表稳定，YAGNI。

## 5. 测试

`tests/lotterystore.test.js`（新建），照 `tests/device.test.js` 的 `globalThis.uni` stub 模式：
- `readStoredCode()`：存储有值（如 `'dlt'`）→ 返回该值；存储空 → 返回 `'ssq'`。
- `setCode('dlt')`：`lotteryStore.code === 'dlt'` 且存储被写入 `'dlt'`（再次 `readStoredCode()` 返回 `'dlt'`）。
- 不删除既有测试。

## 6. 里程碑定位

note.txt 第 16 项。后续：记录区重构(15/25/23) → 通知体系(19/17/18) → 微信登录(14) → 开奖海报(22)。
