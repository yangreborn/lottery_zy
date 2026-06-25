# 微信登录 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 支持真实微信授权登录（uni.login→后端 code2session），保留默认 device 匿名；「我的号码」页顶部登录状态条 + 微信登录/退出。

**Architecture:** 后端把匿名登录（LoginView→mock）与微信登录（新 WechatLoginView→code2session）分开两条；前端 auth store 加 isWechat 标记，mine 页加登录状态条。无新模型/迁移。

**Tech Stack:** Django 5.2 + DRF（pytest + monkeypatch）；uni-app Vue3（vitest）。

## Global Constraints

- 后端 logging 不用 print；make_response 统一（code=0/1）；用户标识 hash。
- 匿名与微信登录分开（不合并成 selector 分发）。
- 无新数据表、无迁移；WECHAT_APPID/SECRET 走 settings 密钥。
- 前端无 Pinia/Vuex；不迁移匿名数据（独立账号）。
- 不删既有测试。

---

### Task 1: 后端 匿名/微信登录分流

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（LoginView 改 mock + 新增 WechatLoginView）
- Modify: `lottery_backend/usernumber/urls.py`（加 login/wechat 路由）
- Test: `lottery_backend/usernumber/tests/test_wechat_login.py`

**Interfaces:**
- Produces: `POST /api/user/login/wechat {code}` → `{logged_in, token}` 或 code=1；`LoginView` 匿名走 mock。

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_wechat_login.py`：
```python
from rest_framework.test import APIClient


def test_wechat_login_success(db, monkeypatch):
    monkeypatch.setattr("usernumber.views.wechat_code_to_openid", lambda code: "wx-openid-123")
    c = APIClient()
    resp = c.post("/api/user/login/wechat", {"code": "wxcode"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["logged_in"] is True
    assert len(body["data"]["token"]) == 64
    assert c.session.get("uid")


def test_wechat_login_failure(db, monkeypatch):
    monkeypatch.setattr("usernumber.views.wechat_code_to_openid", lambda code: None)
    resp = APIClient().post("/api/user/login/wechat", {"code": "badcode"}, format="json")
    assert resp.json()["code"] == 1


def test_wechat_login_missing_code(db):
    resp = APIClient().post("/api/user/login/wechat", {}, format="json")
    assert resp.json()["code"] == 1


def test_anonymous_login_uses_mock(db):
    resp = APIClient().post("/api/user/login", {"code": "dev-xyz"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["token"]) == 64
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_wechat_login.py -v`
Expected: FAIL（`/login/wechat` 404）

- [ ] **Step 3: views import 调整 + LoginView 改 mock**

`lottery_backend/usernumber/views.py`：
- import 行 `from common.auth import code_to_openid, set_user_session, current_user_id` 改为：
```python
from common.auth import mock_code_to_openid, wechat_code_to_openid, set_user_session, current_user_id
```
- `LoginView.post` 里 `openid = code_to_openid(code)` 改为 `openid = mock_code_to_openid(code)`。

- [ ] **Step 4: 新增 WechatLoginView**

`lottery_backend/usernumber/views.py` 文件末尾追加：
```python
class WechatLoginView(APIView):
    """POST /api/user/login/wechat —— 真实微信 code2session 登录。"""
    authentication_classes = []

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(make_response(code=1, msg="缺少 code"))
        openid = wechat_code_to_openid(code)
        if not openid:
            return Response(make_response(code=1, msg="微信登录失败", error="code 无效或已过期"))
        uid = set_user_session(request, openid)
        return Response(make_response(data={"logged_in": True, "token": uid}))
```

- [ ] **Step 5: 注册路由**

`lottery_backend/usernumber/urls.py`：在 `login` 行之后加：
```python
    path("login/wechat", views.WechatLoginView.as_view(), name="user-login-wechat"),
```

- [ ] **Step 6: 跑测试通过 + 全量回归**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_wechat_login.py -v && python -m pytest -q`
Expected: 4 用例 PASS；全量无回归（既有 test_login/test_token_auth 仍绿，mock 把 code 当 openid 不变）。

- [ ] **Step 7: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_wechat_login.py
git commit -m "feat: 微信登录接口+匿名登录改用mock分流"
```

---

### Task 2: 前端 登录状态与入口

**Files:**
- Modify: `lottery_frontend/src/store/auth.js`（加 isWechat）
- Modify: `lottery_frontend/src/api/user.js`（加 wechatLogin）
- Modify: `lottery_frontend/src/pages/mine/index.vue`（登录状态条 + 登录/退出）
- Test: `lottery_frontend/tests/authstore.test.js`、`lottery_frontend/tests/user.test.js`

**Interfaces:**
- Consumes: `POST /api/user/login/wechat`（Task 1）。
- Produces: `authState.isWechat`、`setToken(t, isWechat)`、`wechatLogin(code)`。

- [ ] **Step 1: 写失败测试（auth store + api）**

`lottery_frontend/tests/authstore.test.js`：在 describe 内追加：
```js
  it('setToken 带 isWechat 标记并持久化', () => {
    setToken('WXTOK', true)
    expect(authState.isWechat).toBe(true)
    authState.isWechat = false
    loadToken()
    expect(authState.isWechat).toBe(true)
  })
  it('退出清除 isWechat', () => {
    setToken('WXTOK', true)
    setToken('')
    expect(authState.isWechat).toBe(false)
    expect(loadToken()).toBe('')
  })
```

`lottery_frontend/tests/user.test.js`：import 行追加 `wechatLogin`：
```js
import { login, createNumber, listNumbers, deleteNumber, checkNumber, generateNumbers, submitFeedback, batchDelete, batchGroup, purchaseCreate, purchaseList, purchaseDelete, wechatLogin } from '../src/api/user.js'
```
在 describe 内追加：
```js
  it('wechatLogin', async () => {
    await wechatLogin('wxcode')
    expect(request).toHaveBeenCalledWith('/api/user/login/wechat', { method: 'POST', data: { code: 'wxcode' } })
  })
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- authstore user`
Expected: FAIL（isWechat 未定义 / wechatLogin 未导出）

- [ ] **Step 3: auth store 加 isWechat**

`lottery_frontend/src/store/auth.js` 整体替换为：
```js
import { reactive } from 'vue'

const TOKEN_KEY = 'lottery_token'
const WECHAT_KEY = 'lottery_is_wechat'

export const authState = reactive({ token: '', isWechat: false })

export function loadToken() {
  const t = uni.getStorageSync(TOKEN_KEY)
  if (t) authState.token = t
  authState.isWechat = !!uni.getStorageSync(WECHAT_KEY)
  return authState.token
}

export function setToken(t, isWechat = false) {
  authState.token = t || ''
  authState.isWechat = !!t && isWechat
  if (t) uni.setStorageSync(TOKEN_KEY, t)
  else uni.removeStorageSync(TOKEN_KEY)
  if (t && isWechat) uni.setStorageSync(WECHAT_KEY, '1')
  else uni.removeStorageSync(WECHAT_KEY)
}
```

- [ ] **Step 4: api 加 wechatLogin**

`lottery_frontend/src/api/user.js`：在 `login` 函数之后加：
```js
export function wechatLogin(code) {
  return request('/api/user/login/wechat', { method: 'POST', data: { code } })
}
```

- [ ] **Step 5: mine 页登录状态条**

`lottery_frontend/src/pages/mine/index.vue`：
① import：`import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup, batchDelete, batchGroup, purchaseCreate } from '../../api/user.js'` 追加 `wechatLogin`；并新增一行 `import { authState, setToken } from '../../store/auth.js'`。

② 模板里 `<view class="bar">` 之前插入登录状态条：
```html
    <view class="authbar">
      <text class="astate">{{ auth.isWechat ? '已微信登录' : '匿名使用中' }}</text>
      <text class="abtn" @click="auth.isWechat ? doLogout() : doWechatLogin()">{{ auth.isWechat ? '退出' : '微信登录' }}</text>
    </view>
```

③ script 顶部（const store = lotteryStore 附近）加 `const auth = authState`；并加两个函数（放在 load 之后）：
```js
function doWechatLogin() {
  uni.login({
    success: async (r) => {
      if (!r.code) { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }); return }
      try {
        const res = await wechatLogin(r.code)
        setToken(res.token, true)
        uni.showToast({ title: '登录成功', icon: 'success' })
        load()
      } catch (e) {
        uni.showToast({ title: e.msg || '登录失败', icon: 'none' })
      }
    },
    fail: () => { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }) },
  })
}

function doLogout() {
  setToken('', false)
  uni.showToast({ title: '已退出', icon: 'none' })
  load()
}
```

④ style 加：
```css
.authbar { display: flex; justify-content: space-between; align-items: center; padding: 16rpx 24rpx 0; }
.astate { font-size: 28rpx; color: #888; }
.abtn { font-size: 28rpx; color: #e53935; }
```

- [ ] **Step 6: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/store/auth.js lottery_frontend/src/api/user.js lottery_frontend/src/pages/mine/index.vue lottery_frontend/tests/authstore.test.js lottery_frontend/tests/user.test.js
git commit -m "feat: 我的号码页微信登录状态条+登录退出"
```

---

## 计划自检

**1. Spec 覆盖：**
- LoginView 改 mock（spec §2.1）→ Task 1 Step 3 ✓
- WechatLoginView（spec §2.2）→ Task 1 Step 4 + url Step 5 ✓
- 无新模型/迁移（spec §2.3）→ 计划不含 migration ✓
- auth store isWechat（spec §3.1）→ Task 2 Step 3 ✓
- wechatLogin api（spec §3.2）→ Task 2 Step 4 ✓
- 登录状态条 + 登录/退出（spec §3.3）→ Task 2 Step 5 ✓
- ensureLogin 兼容（spec §3.4）→ 未改 ensureLogin（微信 token 走 `if(authState.token)return`；退出清 token 回匿名）✓
- 平台限制/错误（spec §4）→ Task 2 doWechatLogin fail/无 code toast ✓
- 测试（spec §5）→ Task 1（4 后端用例）、Task 2（authstore + wechatLogin）✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码与确切命令。

**3. 类型/签名一致性：** `wechatLogin(code)` 在 api、测试、mine 一致；`/api/user/login/wechat` 在 url、view、api、测试一致；`setToken(t, isWechat)` 在 auth、测试、mine 一致（旧调用 `setToken(res.token)` 兼容 isWechat 默认 false）；`authState.isWechat` 在 store、mine 一致；`mock_code_to_openid`/`wechat_code_to_openid` 均来自 common.auth（现有）。
