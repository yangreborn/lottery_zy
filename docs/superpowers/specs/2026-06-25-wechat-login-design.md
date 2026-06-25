# 微信登录 · 设计文档

- 日期：2026-06-25
- 定位：里程碑 5。对应 note.txt 第 14 项（支持用户登录，默认匿名）。
- 后续里程碑：开奖海报(22)。

---

## 0. 范围

**本期做**：真实微信授权登录（uni.login → 后端 code2session）+ 保留默认匿名（device code）；「我的号码」页顶部登录状态条 + 微信登录/退出。
**不做**：不迁移匿名期数据（微信账号与匿名账号各自独立）；不取昵称头像；无新数据表。

## 1. 现状

- 前端 `ensureLogin`：用持久 device code（`dev-xxx`）调 `POST /api/user/login`，后端 `code_to_openid`（selector：配 appid 走微信，否则 mock 当 openid）→ hash → session token，`authState.token` 持久化（`lottery_token`）。
- 后端 `LoginView` 已存在；`common.auth` 有 `mock_code_to_openid`/`wechat_code_to_openid`/`code_to_openid`/`hash_user_id`/`set_user_session`/`current_user_id`。

问题：匿名 device code 走 `code_to_openid` selector，生产配 appid 时会被误送 code2session 失败。故需把匿名与微信两条登录分开。

## 2. 后端（usernumber app，匿名/微信分流）

### 2.1 `LoginView`（匿名）改用 mock
- `POST /api/user/login {code}`：改为 `openid = mock_code_to_openid(code)`（device code 始终当匿名标识，不走 code2session）。其余（缺 code → code=1；set_user_session 返回 token）不变。
- import 改 `code_to_openid` → `mock_code_to_openid`。

### 2.2 新增 `WechatLoginView`（微信）
- `POST /api/user/login/wechat {code}`，`authentication_classes = []`。
- 缺 code → `make_response(code=1, msg="缺少 code")`。
- `openid = wechat_code_to_openid(code)`；None（code2session 失败）→ `make_response(code=1, msg="微信登录失败", error="code 无效或已过期")`。
- 成功 `uid = set_user_session(request, openid)`，返回 `make_response(data={"logged_in": True, "token": uid})`。
- 路由注册 `usernumber/urls.py`：`path("login/wechat", views.WechatLoginView.as_view(), name="user-login-wechat")`。

### 2.3 无新模型/迁移
复用 session + hash_user_id。WECHAT_APPID/SECRET 已在 settings（密钥配置）。

## 3. 前端

### 3.1 auth store（`store/auth.js`）
- `authState` 加 `isWechat`（bool），持久化 key `lottery_is_wechat`。
- `loadToken` 同时读 isWechat；`setToken(t, isWechat=false)` 写 token + isWechat（退出时 `setToken('')` 清两者）。

### 3.2 api（`api/user.js`）
- 加 `wechatLogin(code)` → `request('/api/user/login/wechat', { method:'POST', data:{ code } })`。
- 现有 `login(code)`（匿名）、`ensureLogin`（device 匿名）保留不变。

### 3.3 登录流程（mine/index.vue 顶部状态条）
- 状态条：`authState.isWechat` 为真 → 显示「已微信登录 · 退出」；否则显示「微信登录」按钮。
- 微信登录：`uni.login({ success })` 取 `code` → `wechatLogin(code)` → `setToken(res.token, true)` → toast「登录成功」→ reload 列表（切到微信账号数据）。
- 退出：`setToken('', false)` → toast「已退出」→ reload（回 device 匿名数据；ensureLogin 会用 device 重新登录）。
- `uni.login` 不可用/失败（H5）→ toast「请在微信小程序中使用」。

### 3.4 ensureLogin 兼容
微信登录后 `authState.token` 已是 openid token，`ensureLogin` 现有逻辑（`if (authState.token) return authState.token`）直接复用该 token，不会覆盖。退出清 token 后，ensureLogin 回 device 匿名 login。无需改 ensureLogin。

## 4. 错误处理 / 平台限制

- `uni.login` 仅微信小程序端有效；H5/开发端 → toast 提示，不报错。
- code2session 失败 → `code=1`，前端 toast。
- 退出后 reload 触发 ensureLogin 重新匿名登录。

## 5. 测试

- 后端 pytest（`usernumber/tests/test_login.py` 追加或新建 `test_wechat_login.py`）：
  - `WechatLoginView`：patch `usernumber.views.wechat_code_to_openid` 返回 openid → code=0 + session uid 写入；patch 返回 None → code=1；缺 code → code=1。
  - `LoginView` 匿名：传 code → mock 当 openid，code=0（既有 test_login 应仍绿）。
- 前端 vitest（并入 `tests/user.test.js`）：`wechatLogin('wxcode')` 命中 `/api/user/login/wechat` POST data `{code:'wxcode'}`。
- 不删既有测试。

## 6. 里程碑定位

note.txt 第 14 项。后续：开奖海报(22)。
