# 里程碑G 访问日志精简 设计（note 45）

**目标：** 访问日志只记「登录 + 实际操作（选号/改昵称/设已购/反馈/比对）」，不再记每个页面的浏览埋点。纯前端（后端 AccessLog 模型不变，action 为自由字段）。

## 背景

`reportAccess` 现在在几乎每个页面 `onShow` 上报页面浏览（action=view），日志量大。note 45：只记登录记录 + 操作日志。

## 方案

### 移除页面浏览埋点（删 reportAccess 调用与该页 import）

- `notice/index.vue`、`draw/stats.vue`、`guide/index.vue`、`draw/latest.vue`、`draw/history.vue`、`guide/detail.vue`、`draw/detail.vue`：删除 onShow/onLoad 内的 `reportAccess('…/…')` 浏览上报及未再使用的 import。
- `mine/index.vue`：删 onShow 的 `reportAccess('mine/index', {})`（保留 import，下面要加改昵称/登录操作上报）。
- `mine/numbers.vue`：删 onShow 的 `reportAccess('mine/numbers', …)`（保留 import，已有比对、下面加设已购上报）。

### 保留的操作埋点

- `mine/picker.vue`：选号保存 `reportAccess('mine/create', {action:'save_number'})`（×2）保留。
- `mine/numbers.vue`：比对 `reportAccess('mine/check', {action:'check_number'})` 保留。

### 新增操作/登录埋点

- 登录：`api/user.js` `ensureLogin` 首次登录成功后 `reportAccess('login', {action:'login'})`；`mine/index.vue` 微信登录成功后同样上报。
- 改昵称：`mine/index.vue` `editNickname` 成功后 `reportAccess('mine/nickname', {action:'set_nickname'})`。
- 设已购：`mine/numbers.vue` `onPickPurchase` 成功后 `reportAccess('mine/purchase', {action:'mark_purchased', lottery_code: store.code})`。
- 反馈：`feedback/index.vue` 提交成功后 `reportAccess('feedback', {action:'feedback'})`（加 import）。

## 文件

- 修改：`src/api/user.js`、`src/pages/mine/index.vue`、`src/pages/mine/numbers.vue`、`src/pages/mine/picker.vue`(无改，保留)、`src/pages/feedback/index.vue`、以及移除浏览埋点的 7 个页面（notice/stats/guide-index/latest/history/guide-detail/draw-detail）。

## 测试

- 全为埋点调用增删，`reportAccess`/`api` 已有单测；新增 `login` 等仅 action 字符串。全量前端测试通过 + 手测：浏览不再产日志，登录/选号/改昵称/设已购/反馈各产一条。
- 后端 AccessLog/看板不改（action 自由字段，看板 actions 分布自动反映新动作）。
