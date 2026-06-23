# M3b · 我的号码 H5 前端 · 设计文档

- 日期：2026-06-23
- 定位：把已就绪的 M3 记录号码后端（登录/选号/我的号码/中奖比对）做成 uni-app H5 页面，新增"我的"tab。
- 前置：M3 后端接口已合并到 master；M2b H5 前端基座（api/store/utils/components/pages + tabBar）已就绪。

---

## 0. 范围

**本期做**：自动登录（H5 无微信，用持久 UUID 走 mock 登录）、选号器（手动/机选/定胆随机）、我的号码列表（删除）、中奖比对（仅展示）。新增"我的"tab。
**不做**：真实微信登录（已有 provider seam，注册主体后接）；微信小程序端编译；运营看板（M4）。

## 1. 登录态传输：token 放 header（关键决策）

H5 无 `wx.login`；且现 CORS 用通配 `*`，带 cookie 的跨域请求会被浏览器拒绝，小程序对 cookie 也不友好。故改用 **token-in-header**：

- 登录成功后端返回 `data:{logged_in:true, token:<uid hash>}`。
- 前端存 token（localStorage），之后每个用户接口请求带头 `X-User-Id: <token>`。
- 后端 `current_user_id(request)` 先读 session，再兜底读 `X-User-Id` 头。
- **安全**：token = `sha256(SECRET_KEY:openid)`，客户端只能从登录拿到自己的；算不出别人的（需 SECRET_KEY+他人 openid）。对免费工具、无敏感数据/支付的场景足够。小程序端将来直接复用此 header 机制。

## 2. 后端改动（小）

- `lottery_backend/common/auth.py`：`current_user_id(request)` 改为 `request.session.get("uid") or request.headers.get("X-User-Id")`。
- `lottery_backend/usernumber/views.py` `LoginView`：响应改为 `make_response(data={"logged_in": True, "token": uid})`（uid 来自 set_user_session 返回值）。
- `lottery_backend/config/settings.py`：DEBUG 下 CORS 允许自定义头 `X-User-Id`（`CORS_ALLOW_HEADERS` 扩展）。
- 不动 create/list/delete/check 的业务逻辑（它们已用 current_user_id）。

## 3. 前端结构（lottery_frontend 内新增/改）

```
src/api/request.js     改: 读 authStore.token, 有则请求带 header X-User-Id
src/api/user.js        新: login(code) / createNumber(payload) / listNumbers(code) /
                            deleteNumber(id) / checkNumber(id)
src/store/auth.js      新: reactive token; loadToken(); ensureLogin() 自动登录
src/utils/device.js    新: getOrCreateDeviceCode() 持久 UUID(localStorage)
src/utils/picker.js    新: 纯逻辑 toggleBall/selectionComplete(可单测)
src/components/
  BallSelectable.vue   新: 可点选号码球(选中加描边/置灰未选)
src/pages/mine/
  index.vue            新: 我的号码列表(彩种切换/比对/删除/进选号器)
  picker.vue           新: 选号器(手动/机选/定胆 + 备注/目标期号 + 保存)
src/pages.json         改: 注册 mine 两页 + tabBar 加"我的"
```

## 4. 自动登录流程

进入"我的"页（onShow）调 `authStore.ensureLogin()`：

1. 若已有 token，直接用。
2. 否则 `getOrCreateDeviceCode()` 取/生成持久 UUID（localStorage 键 `lottery_device_code`），作为 code。
3. POST `/api/user/login {code}` → 取 `data.token` 存入 authStore + localStorage（键 `lottery_token`）。
4. 失败 `uni.showToast` 提示，列表显示空态。

每个浏览器一个稳定身份，用户零操作。

## 5. 选号器（picker.vue，读 rule_config 动态渲染）

进入时按当前彩种 `rule_config` 渲染红/蓝两区可点球（BallSelectable）。

- **手动**：点选红区 count 个、蓝区 count 个；选满才可保存；保存 `createNumber({code, gen_type:'manual', numbers:{red,blue}, note, target_issue})`。
- **机选**：一键 `createNumber({code, gen_type:'random'})`（后端生成号码），保存后回列表。
- **定胆随机**：在红/蓝区点选胆码（每区少于 count）；`createNumber({code, gen_type:'dan_random', dan_numbers:{red,blue}})`，后端锁胆补全。
- 公共：备注输入、目标期号输入（可空）；保存成功 `uni.navigateBack` 回列表。
- 号码个数/范围校验由后端 validate_numbers 兜底；前端"选满才可保存"做即时反馈。

`utils/picker.js` 纯逻辑（可单测）：
- `toggleBall(selected:Array, n:Number, max:Number) -> Array`：已选则移除；未选且未达 max 则加入；达 max 不变。
- `selectionComplete(numbers, rule) -> Boolean`：红蓝两区都达到各自 count。

## 6. 我的号码列表（index.vue）

- 顶部 LotteryTabs 切彩种（复用）；调 `listNumbers(code)` 拉本人记录。
- 每条：号码球（Ball）、生成方式标签、备注、目标期号；有 target_issue 的显"比对"按钮；"删除"按钮。
- "比对" → `checkNumber(id)` → 弹层（uni.showModal 或自绘）显示命中红/蓝个数 + 第几等奖/未中奖。
- "删除" → `deleteNumber(id)` → 成功后刷新列表。
- 右上/底部"去选号"入口 → `navigateTo` picker.vue。
- 空态："还没有记录，去选号吧"。

## 7. 错误处理

- 接口 code!=0 / 网络失败：request reject，页面 uni.showToast(msg)。
- 未登录（token 缺失且 ensureLogin 失败）：提示并禁用保存/列表为空态。
- 比对：目标期未开奖后端返 code=1，弹层提示"该期暂未开奖"。

## 8. 测试策略

- **后端 pytest**：`current_user_id` 读 X-User-Id 头兜底；`LoginView` 返回含 token；带 header 的 create/list 能识别用户（无 session 也行）。
- **前端 vitest**：
  - `request.js` 带 token 时请求头含 X-User-Id、无 token 时不带。
  - `utils/picker.js` toggleBall（增/删/达上限不变）、selectionComplete。
  - `utils/device.js` getOrCreateDeviceCode 持久性（mock storage）。
- **人工**：`npm run dev:h5` 浏览器目测"我的"四类操作。

## 9. 怎么看效果

后端 8123 + 前端 5199，多出"我的"tab：可机选/手动/定胆存号、看列表、删除、对目标期比对中奖。示例数据已有 2026060-2026062 期开奖，记录目标期填这些即可看到中奖比对结果。

## 10. 里程碑定位

总设计文档模块二（记录号码）的 H5 落地。后续：M4 玩法介绍+看板 → 微信小程序端编译。
