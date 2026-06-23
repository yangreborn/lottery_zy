# M3b · 我的号码 H5 前端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把已就绪的 M3 记录号码后端做成 uni-app H5 "我的"页面：自动登录、选号器(手动/机选/定胆)、我的号码列表(删除)、中奖比对。

**Architecture:** 后端小改为 token-in-header 鉴权(current_user_id 兜底读 X-User-Id；登录返回 token)。前端新增 auth store(持久 token + 自动登录)、user api、选号器纯逻辑与可点球组件、mine 两页，tabBar 加"我的"。复用已有 request/Ball/LotteryTabs/lotteryStore。

**Tech Stack:** Django 5.2 + DRF + django-cors-headers；uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 登录态用 **token-in-header**：登录返回 `data.token`(=user_id hash)，前端每次用户接口带请求头 `X-User-Id: <token>`；后端 `current_user_id` 先读 session 再兜底读该头。
- 后端日志用 logging 禁止 print；返回统一 `make_response`(成功 code=0，应用级错误 code=1 且 HTTP 200)。
- 前端 uni-app(Vue3+Vite) JS，不引 Pinia/Vuex(状态用 reactive)；API 返回 {code,msg,data,error}，request 在 code=0 时 resolve body.data。
- CORS 仅 DEBUG 放开，并在 DEBUG 下允许自定义头 `x-user-id`。
- 号码球红 #e53935 / 蓝 #1e88e5(全前端统一，复用 ballColor)。
- 中奖比对仅展示，无兑奖/资金逻辑。
- 前端命令在 `lottery_frontend/`；后端命令在 `lottery_backend/`(先激活 .venv)。后端测试 DB Docker lottery_pg 127.0.0.1:5433。
- 本机端口：后端用 8123、前端用 5199(默认 8000/5173 常被占)；前端 vite.config 已绑 host:true+port:5199；`.env.development` VITE_API_BASE=http://127.0.0.1:8123。

---

## File Structure

- `lottery_backend/common/auth.py`(改)：`current_user_id` 读 X-User-Id 头兜底。
- `lottery_backend/usernumber/views.py`(改)：`LoginView` 返回 token。
- `lottery_backend/config/settings.py`(改)：DEBUG 下 CORS 允许 x-user-id 头。
- `lottery_backend/usernumber/tests/test_token_auth.py`(新)：header 鉴权 + 登录 token 测试。
- `lottery_frontend/src/store/auth.js`(新)：authState.token + loadToken/setToken。
- `lottery_frontend/src/utils/device.js`(新)：getOrCreateDeviceCode 持久 UUID。
- `lottery_frontend/src/api/request.js`(改)：有 token 带 X-User-Id 头。
- `lottery_frontend/src/api/user.js`(新)：login/createNumber/listNumbers/deleteNumber/checkNumber/ensureLogin。
- `lottery_frontend/src/utils/picker.js`(新)：toggleBall/selectionComplete 纯逻辑。
- `lottery_frontend/src/components/BallSelectable.vue`(新)：可点选号码球。
- `lottery_frontend/src/pages/mine/index.vue`(新)：我的号码列表。
- `lottery_frontend/src/pages/mine/picker.vue`(新)：选号器。
- `lottery_frontend/src/pages.json`(改)：注册 mine 两页 + tabBar 加"我的"。
- 前端测试：`tests/{authstore,device,request_token,user,picker}.test.js`。

---

### Task 1: 后端 token-header 鉴权

**Files:**
- Modify: `lottery_backend/common/auth.py`
- Modify: `lottery_backend/usernumber/views.py`
- Modify: `lottery_backend/config/settings.py`
- Test: `lottery_backend/usernumber/tests/test_token_auth.py`

**Interfaces:**
- Consumes: `set_user_session`(返回 uid hash)、现有 `current_user_id`
- Produces: `current_user_id(request)` 兼容 `request.headers["X-User-Id"]`；`POST /api/user/login` 返回 `data:{logged_in:true, token:<uid hash>}`；用户接口在无 session 但带 X-User-Id 头时按该 token 识别用户。

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_token_auth.py`:
```python
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_login_returns_token(db):
    resp = APIClient().post("/api/user/login", {"code": "dev-abc"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["logged_in"] is True
    assert isinstance(body["data"]["token"], str) and len(body["data"]["token"]) == 64


def test_header_token_identifies_user(ssq):
    # 无 session，仅靠 X-User-Id 头识别身份
    c = APIClient()
    c.credentials(HTTP_X_USER_ID="tokenAAA")
    c.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    }, format="json")
    resp = c.get("/api/user/number/list")
    assert resp.json()["code"] == 0
    assert len(resp.json()["data"]) == 1


def test_header_token_isolates_users(ssq):
    a = APIClient(); a.credentials(HTTP_X_USER_ID="tokenAAA")
    a.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    }, format="json")
    b = APIClient(); b.credentials(HTTP_X_USER_ID="tokenBBB")
    assert b.get("/api/user/number/list").json()["data"] == []


def test_no_token_no_session_unauthenticated(ssq):
    resp = APIClient().get("/api/user/number/list")
    assert resp.json()["code"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_token_auth.py -v`
Expected: FAIL（login 无 token 字段；header 不被识别）

- [ ] **Step 3: 改 current_user_id 读 header 兜底**

`lottery_backend/common/auth.py` — 把 `current_user_id` 改为：
```python
def current_user_id(request):
    """当前用户 hash：先读 session，再兜底读 X-User-Id 头；都没有返回 None。"""
    return request.session.get("uid") or request.headers.get("X-User-Id")
```

- [ ] **Step 4: LoginView 返回 token**

`lottery_backend/usernumber/views.py` 的 `LoginView.post` 最后两行改为：
```python
        uid = set_user_session(request, openid)
        return Response(make_response(data={"logged_in": True, "token": uid}))
```

- [ ] **Step 5: settings 允许 x-user-id 头(DEBUG)**

`lottery_backend/config/settings.py` 末尾的 `if DEBUG:` 块改为：
```python
# H5 本地开发跨域；生产同域 nginx，不放开
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    from corsheaders.defaults import default_headers
    CORS_ALLOW_HEADERS = list(default_headers) + ["x-user-id"]
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_token_auth.py -v`
Expected: PASS（4 passed）

- [ ] **Step 7: 全量回归**

Run: `python -m pytest -q`
Expected: PASS（之前 83 + 本任务新增，全绿）

- [ ] **Step 8: 提交**

```bash
git add lottery_backend/common/auth.py lottery_backend/usernumber/views.py lottery_backend/config/settings.py lottery_backend/usernumber/tests/test_token_auth.py
git commit -m "feat: 后端 token-in-header 鉴权，登录返回 token"
```

---

### Task 2: 前端 auth store + device code

**Files:**
- Create: `lottery_frontend/src/store/auth.js`
- Create: `lottery_frontend/src/utils/device.js`
- Test: `lottery_frontend/tests/authstore.test.js`
- Test: `lottery_frontend/tests/device.test.js`

**Interfaces:**
- Produces:
  - `auth.js`：`authState = reactive({token:''})`；`loadToken() -> string`(从 storage 读入 authState)；`setToken(t)`(写 authState + storage，t 假值则清除)
  - `device.js`：`getOrCreateDeviceCode() -> string`(storage 键 `lottery_device_code`，无则生成持久 UUID)

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/authstore.test.js`:
```js
import { describe, it, expect, beforeEach } from 'vitest'
import { authState, loadToken, setToken } from '../src/store/auth.js'

function stubStorage() {
  const store = {}
  globalThis.uni = {
    getStorageSync: (k) => store[k] || '',
    setStorageSync: (k, v) => { store[k] = v },
    removeStorageSync: (k) => { delete store[k] },
  }
}

describe('auth store', () => {
  beforeEach(() => { stubStorage(); setToken('') })

  it('setToken 写入 state 与 storage，loadToken 读回', () => {
    setToken('TOK123')
    expect(authState.token).toBe('TOK123')
    authState.token = ''
    expect(loadToken()).toBe('TOK123')
    expect(authState.token).toBe('TOK123')
  })

  it('setToken 假值清除', () => {
    setToken('X'); setToken('')
    expect(authState.token).toBe('')
    expect(loadToken()).toBe('')
  })
})
```

`lottery_frontend/tests/device.test.js`:
```js
import { describe, it, expect, beforeEach } from 'vitest'
import { getOrCreateDeviceCode } from '../src/utils/device.js'

function stubStorage() {
  const store = {}
  globalThis.uni = {
    getStorageSync: (k) => store[k] || '',
    setStorageSync: (k, v) => { store[k] = v },
  }
}

describe('device code', () => {
  beforeEach(stubStorage)

  it('首次生成并持久，二次返回同值', () => {
    const a = getOrCreateDeviceCode()
    expect(a).toBeTruthy()
    const b = getOrCreateDeviceCode()
    expect(b).toBe(a)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（找不到 auth.js / device.js）

- [ ] **Step 3: 写 auth store**

`lottery_frontend/src/store/auth.js`:
```js
import { reactive } from 'vue'

const TOKEN_KEY = 'lottery_token'

export const authState = reactive({ token: '' })

export function loadToken() {
  const t = uni.getStorageSync(TOKEN_KEY)
  if (t) authState.token = t
  return authState.token
}

export function setToken(t) {
  authState.token = t || ''
  if (t) uni.setStorageSync(TOKEN_KEY, t)
  else uni.removeStorageSync(TOKEN_KEY)
}
```

- [ ] **Step 4: 写 device**

`lottery_frontend/src/utils/device.js`:
```js
const DEVICE_KEY = 'lottery_device_code'

export function getOrCreateDeviceCode() {
  let code = uni.getStorageSync(DEVICE_KEY)
  if (!code) {
    code = 'dev-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10)
    uni.setStorageSync(DEVICE_KEY, code)
  }
  return code
}
```

- [ ] **Step 5: 跑测试确认通过**

Run: `npm test`
Expected: PASS（authstore + device 全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/store/auth.js lottery_frontend/src/utils/device.js lottery_frontend/tests/authstore.test.js lottery_frontend/tests/device.test.js
git commit -m "feat: 前端 auth store(持久 token) 与 device code"
```

---

### Task 3: request 带 token 头 + user api

**Files:**
- Modify: `lottery_frontend/src/api/request.js`
- Create: `lottery_frontend/src/api/user.js`
- Test: `lottery_frontend/tests/request_token.test.js`
- Test: `lottery_frontend/tests/user.test.js`

**Interfaces:**
- Consumes: `authState`/`setToken`(store/auth)、`getOrCreateDeviceCode`(utils/device)
- Produces:
  - `request` 在 `authState.token` 非空时给 uni.request 带 `header:{ 'X-User-Id': token }`
  - `user.js`：`login(code)`→POST /api/user/login {code}；`createNumber(payload)`→POST /api/user/number/create payload；`listNumbers(code)`→GET /api/user/number/list (code 非空才带)；`deleteNumber(id)`→DELETE /api/user/number/{id}；`checkNumber(id)`→GET /api/user/number/check {id}；`ensureLogin()`→有 token 直接返回，否则用 device code 调 login 并 setToken

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/request_token.test.js`:
```js
import { describe, it, expect, beforeEach } from 'vitest'
import { request } from '../src/api/request.js'
import { authState } from '../src/store/auth.js'

let captured
function stubUni() {
  globalThis.uni = {
    request: (opts) => { captured = opts; opts.success({ statusCode: 200, data: { code: 0, msg: 'ok', data: {}, error: null } }) },
  }
}

describe('request token header', () => {
  beforeEach(() => { stubUni(); authState.token = '' })

  it('有 token 带 X-User-Id 头', async () => {
    authState.token = 'TOK9'
    await request('/api/user/number/list')
    expect(captured.header['X-User-Id']).toBe('TOK9')
  })

  it('无 token 不带该头', async () => {
    await request('/api/openapi/lottery/list')
    expect(captured.header && captured.header['X-User-Id']).toBeFalsy()
  })
})
```

`lottery_frontend/tests/user.test.js`:
```js
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({
  request: vi.fn(() => Promise.resolve({ token: 'T' })),
}))
import { request } from '../src/api/request.js'
import { login, createNumber, listNumbers, deleteNumber, checkNumber } from '../src/api/user.js'

describe('user api', () => {
  beforeEach(() => { request.mockClear() })

  it('login', async () => {
    await login('dev-x')
    expect(request).toHaveBeenCalledWith('/api/user/login', { method: 'POST', data: { code: 'dev-x' } })
  })
  it('createNumber', async () => {
    await createNumber({ code: 'ssq', gen_type: 'random' })
    expect(request).toHaveBeenCalledWith('/api/user/number/create', { method: 'POST', data: { code: 'ssq', gen_type: 'random' } })
  })
  it('listNumbers 带 code', async () => {
    await listNumbers('ssq')
    expect(request).toHaveBeenCalledWith('/api/user/number/list', { data: { code: 'ssq' } })
  })
  it('listNumbers 无 code', async () => {
    await listNumbers('')
    expect(request).toHaveBeenCalledWith('/api/user/number/list', { data: {} })
  })
  it('deleteNumber', async () => {
    await deleteNumber(5)
    expect(request).toHaveBeenCalledWith('/api/user/number/5', { method: 'DELETE' })
  })
  it('checkNumber', async () => {
    await checkNumber(5)
    expect(request).toHaveBeenCalledWith('/api/user/number/check', { data: { id: 5 } })
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（request 未带 header；user.js 不存在）

- [ ] **Step 3: 改 request.js 带 token 头**

`lottery_frontend/src/api/request.js` 整体替换为：
```js
import { authState } from '../store/auth.js'

const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export function request(path, { method = 'GET', data } = {}) {
  const header = {}
  if (authState.token) header['X-User-Id'] = authState.token
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE + path,
      method,
      data,
      header,
      success: (res) => {
        if (res.statusCode !== 200) {
          reject({ code: -1, msg: `HTTP ${res.statusCode}` })
          return
        }
        const body = res.data || {}
        if (body.code === 0) {
          resolve(body.data)
        } else {
          reject({ code: body.code, msg: body.msg || '请求失败' })
        }
      },
      fail: (err) => reject({ code: -1, msg: (err && err.errMsg) || '网络错误' }),
    })
  })
}
```

- [ ] **Step 4: 写 user.js**

`lottery_frontend/src/api/user.js`:
```js
import { request } from './request.js'
import { authState, setToken } from '../store/auth.js'
import { getOrCreateDeviceCode } from '../utils/device.js'

export function login(code) {
  return request('/api/user/login', { method: 'POST', data: { code } })
}

export function createNumber(payload) {
  return request('/api/user/number/create', { method: 'POST', data: payload })
}

export function listNumbers(code) {
  return request('/api/user/number/list', { data: code ? { code } : {} })
}

export function deleteNumber(id) {
  return request(`/api/user/number/${id}`, { method: 'DELETE' })
}

export function checkNumber(id) {
  return request('/api/user/number/check', { data: { id } })
}

export async function ensureLogin() {
  if (authState.token) return authState.token
  const code = getOrCreateDeviceCode()
  const res = await login(code)
  setToken(res.token)
  return res.token
}
```

- [ ] **Step 5: 跑测试确认通过**

Run: `npm test`
Expected: PASS（request_token + user 全绿；既有测试不破）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/api/request.js lottery_frontend/src/api/user.js lottery_frontend/tests/request_token.test.js lottery_frontend/tests/user.test.js
git commit -m "feat: request 带 X-User-Id 头 + 用户接口 user.js(含自动登录)"
```

---

### Task 4: 选号纯逻辑 picker.js + BallSelectable

**Files:**
- Create: `lottery_frontend/src/utils/picker.js`
- Create: `lottery_frontend/src/components/BallSelectable.vue`
- Test: `lottery_frontend/tests/picker.test.js`

**Interfaces:**
- Consumes: `ballColor`(utils/format)
- Produces:
  - `toggleBall(selected, n, max) -> Array`：已选移除；未选且 length<max 加入并升序；达 max 不变
  - `selectionComplete(numbers, rule) -> Boolean`：red/blue 两区数量都等于各自 count
  - `BallSelectable.vue`：props `{value:Number, zone:String, selected:Boolean}`，emit `toggle(value)`；选中实心(ballColor)，未选描边

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/picker.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { toggleBall, selectionComplete } from '../src/utils/picker.js'

describe('toggleBall', () => {
  it('未选则加入并升序', () => {
    expect(toggleBall([3, 1], 2, 6)).toEqual([1, 2, 3])
  })
  it('已选则移除', () => {
    expect(toggleBall([1, 2, 3], 2, 6)).toEqual([1, 3])
  })
  it('达上限不再加入', () => {
    expect(toggleBall([1, 2], 3, 2)).toEqual([1, 2])
  })
})

describe('selectionComplete', () => {
  const rule = { red: { count: 6, min: 1, max: 33 }, blue: { count: 1, min: 1, max: 16 } }
  it('两区都满才 true', () => {
    expect(selectionComplete({ red: [1, 2, 3, 4, 5, 6], blue: [7] }, rule)).toBe(true)
  })
  it('红区不满 false', () => {
    expect(selectionComplete({ red: [1, 2, 3], blue: [7] }, rule)).toBe(false)
  })
  it('蓝区缺 false', () => {
    expect(selectionComplete({ red: [1, 2, 3, 4, 5, 6], blue: [] }, rule)).toBe(false)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（找不到 picker.js）

- [ ] **Step 3: 写 picker.js**

`lottery_frontend/src/utils/picker.js`:
```js
export function toggleBall(selected, n, max) {
  if (selected.indexOf(n) >= 0) {
    return selected.filter((x) => x !== n)
  }
  if (selected.length >= max) {
    return selected
  }
  return [...selected, n].sort((a, b) => a - b)
}

export function selectionComplete(numbers, rule) {
  for (const zone of ['red', 'blue']) {
    const r = rule[zone]
    if (!r) continue
    if ((numbers[zone] || []).length !== r.count) return false
  }
  return true
}
```

- [ ] **Step 4: 写 BallSelectable 组件**

`lottery_frontend/src/components/BallSelectable.vue`:
```vue
<template>
  <view
    class="sball"
    :style="selected ? { backgroundColor: color, color: '#fff' } : { borderColor: color, color: color }"
    @click="$emit('toggle', value)"
  >
    <text>{{ display }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { ballColor } from '../utils/format.js'

const props = defineProps({
  value: { type: Number, required: true },
  zone: { type: String, default: 'red' },
  selected: { type: Boolean, default: false },
})
defineEmits(['toggle'])

const color = computed(() => ballColor(props.zone))
const display = computed(() => String(props.value).padStart(2, '0'))
</script>

<style scoped>
.sball {
  width: 64rpx; height: 64rpx; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  margin: 8rpx; font-size: 26rpx; border: 2rpx solid transparent;
  background: #fff;
}
</style>
```

- [ ] **Step 5: 跑测试确认通过**

Run: `npm test`
Expected: PASS（picker 全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/utils/picker.js lottery_frontend/src/components/BallSelectable.vue lottery_frontend/tests/picker.test.js
git commit -m "feat: 选号纯逻辑 toggleBall/selectionComplete + 可点球组件"
```

---

### Task 5: 我的号码列表页 + tabBar"我的"

**Files:**
- Create: `lottery_frontend/src/pages/mine/index.vue`
- Modify: `lottery_frontend/src/pages.json`

**Interfaces:**
- Consumes: `ensureLogin`/`listNumbers`/`deleteNumber`/`checkNumber`(api/user)、`lotteryStore`(store/lottery)、`Ball`、`LotteryTabs`、`getLotteryList`(api/lottery)
- Produces: 页面 `pages/mine/index`，tabBar 第 4 项"我的"；列表展示本人记录，支持比对/删除/进选号器。

- [ ] **Step 1: 配 pages.json**

`lottery_frontend/src/pages.json` 整体替换为：
```json
{
  "pages": [
    { "path": "pages/draw/latest", "style": { "navigationBarTitleText": "当期开奖" } },
    { "path": "pages/draw/history", "style": { "navigationBarTitleText": "历史开奖" } },
    { "path": "pages/draw/detail", "style": { "navigationBarTitleText": "开奖详情" } },
    { "path": "pages/draw/stats", "style": { "navigationBarTitleText": "号码统计" } },
    { "path": "pages/mine/index", "style": { "navigationBarTitleText": "我的号码" } },
    { "path": "pages/mine/picker", "style": { "navigationBarTitleText": "选号" } }
  ],
  "tabBar": {
    "color": "#666",
    "selectedColor": "#e53935",
    "list": [
      { "pagePath": "pages/draw/latest", "text": "当期" },
      { "pagePath": "pages/draw/history", "text": "历史" },
      { "pagePath": "pages/draw/stats", "text": "统计" },
      { "pagePath": "pages/mine/index", "text": "我的" }
    ]
  },
  "globalStyle": {
    "navigationBarTextStyle": "black",
    "navigationBarTitleText": "彩票查询",
    "navigationBarBackgroundColor": "#fff",
    "backgroundColor": "#f5f5f5"
  }
}
```

- [ ] **Step 2: 写 index 页**

`lottery_frontend/src/pages/mine/index.vue`:
```vue
<template>
  <view class="page">
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar">
      <button class="go" size="mini" @click="goPicker">去选号</button>
    </view>
    <view v-for="rec in items" :key="rec.id" class="card">
      <view class="top">
        <text class="tag">{{ genLabel(rec.gen_type) }}</text>
        <text v-if="rec.target_issue" class="issue">目标 {{ rec.target_issue }}</text>
      </view>
      <view class="balls">
        <Ball v-for="(n, i) in rec.numbers.red" :key="'r'+i" :value="n" zone="red" />
        <Ball v-for="(n, i) in rec.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
      </view>
      <view v-if="rec.note" class="note">{{ rec.note }}</view>
      <view class="ops">
        <text v-if="rec.target_issue" class="op" @click="doCheck(rec.id)">比对</text>
        <text class="op del" @click="doDelete(rec.id)">删除</text>
      </view>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, listNumbers, deleteNumber, checkNumber } from '../../api/user.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

const GEN = { manual: '手动', random: '机选', dan_random: '定胆' }
function genLabel(g) { return GEN[g] || g }

async function load() {
  emptyMsg.value = '加载中…'
  try {
    await ensureLogin()
    items.value = await listNumbers(store.code)
    if (!items.value.length) emptyMsg.value = '还没有记录，去选号吧'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) { setCode(code); load() }
function goPicker() { uni.navigateTo({ url: '/pages/mine/picker' }) }

async function doCheck(id) {
  try {
    const r = await checkNumber(id)
    uni.showModal({
      title: '比对结果',
      content: `命中 红${r.red_hit} 蓝${r.blue_hit}，${r.label}`,
      showCancel: false,
    })
  } catch (e) {
    uni.showToast({ title: e.msg || '比对失败', icon: 'none' })
  }
}

async function doDelete(id) {
  try {
    await deleteNumber(id)
    load()
  } catch (e) {
    uni.showToast({ title: e.msg || '删除失败', icon: 'none' })
  }
}

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞列表 */ }
  }
  load()
})
</script>

<style scoped>
.bar { display: flex; justify-content: flex-end; padding: 16rpx 20rpx 0; }
.go { background: #e53935; color: #fff; }
.card { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.top { display: flex; justify-content: space-between; font-size: 24rpx; color: #888; }
.tag { color: #e53935; }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.note { font-size: 24rpx; color: #999; }
.ops { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.op { margin-left: 28rpx; font-size: 26rpx; color: #1e88e5; }
.op.del { color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 3: 浏览器/接口目测**

后端：`lottery_backend` 激活 venv → seed_lotteries → seed_sample_draws → `python manage.py runserver 127.0.0.1:8123`。
前端：`lottery_frontend` 下 `npm run dev:h5`。
Expected: 底部多出"我的"tab；进入后自动登录(无报错)，空列表显示"还没有记录，去选号吧"；点"去选号"能跳到选号页(Task6 后完整)。
可 curl 验证带 header 列表：先 `curl -s -XPOST http://127.0.0.1:8123/api/user/login -H "Content-Type: application/json" -d '{"code":"dev-test"}'` 取 token，再 `curl -s http://127.0.0.1:8123/api/user/number/list -H "X-User-Id: <token>"` 应 code:0。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/mine/index.vue lottery_frontend/src/pages.json
git commit -m "feat: 我的号码列表页 + tabBar 我的 入口"
```

---

### Task 6: 选号器页 picker

**Files:**
- Create: `lottery_frontend/src/pages/mine/picker.vue`

**Interfaces:**
- Consumes: `getLotteryList`(api/lottery)、`createNumber`/`ensureLogin`(api/user)、`lotteryStore`、`toggleBall`/`selectionComplete`(utils/picker)、`BallSelectable`
- Produces: 选号器页，三种方式存号后返回列表。

- [ ] **Step 1: 写 picker 页**

`lottery_frontend/src/pages/mine/picker.vue`:
```vue
<template>
  <view class="page" v-if="rule">
    <view class="zone">
      <text class="zt">红球（选 {{ rule.red.count }}）</text>
      <view class="grid">
        <BallSelectable
          v-for="n in redRange" :key="'r'+n" :value="n" zone="red"
          :selected="sel.red.includes(n)" @toggle="toggle('red', $event)"
        />
      </view>
    </view>
    <view class="zone">
      <text class="zt">蓝球（选 {{ rule.blue.count }}）</text>
      <view class="grid">
        <BallSelectable
          v-for="n in blueRange" :key="'b'+n" :value="n" zone="blue"
          :selected="sel.blue.includes(n)" @toggle="toggle('blue', $event)"
        />
      </view>
    </view>
    <view class="fields">
      <input class="ipt" v-model="note" placeholder="备注（可空）" />
      <input class="ipt" v-model="targetIssue" placeholder="目标期号（可空，用于比对）" />
    </view>
    <view class="actions">
      <button class="btn" @click="saveManual" :disabled="!canSaveManual">保存手选</button>
      <button class="btn alt" @click="saveRandom">机选保存</button>
      <button class="btn alt" @click="saveDan">定胆随机</button>
    </view>
  </view>
  <view v-else class="empty">{{ emptyMsg }}</view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, createNumber } from '../../api/user.js'
import { toggleBall, selectionComplete } from '../../utils/picker.js'

const rule = ref(null)
const emptyMsg = ref('加载中…')
const sel = reactive({ red: [], blue: [] })
const note = ref('')
const targetIssue = ref('')

const code = lotteryStore.code

function range(r) {
  const arr = []
  for (let i = r.min; i <= r.max; i++) arr.push(i)
  return arr
}
const redRange = computed(() => (rule.value ? range(rule.value.red) : []))
const blueRange = computed(() => (rule.value ? range(rule.value.blue) : []))
const canSaveManual = computed(() => rule.value && selectionComplete(sel, rule.value))

function toggle(zone, n) {
  sel[zone] = toggleBall(sel[zone], n, rule.value[zone].count)
}

async function save(payload) {
  try {
    await ensureLogin()
    await createNumber({ code, note: note.value, target_issue: targetIssue.value, ...payload })
    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
}

function saveManual() {
  if (!canSaveManual.value) return
  save({ gen_type: 'manual', numbers: { red: sel.red, blue: sel.blue } })
}
function saveRandom() {
  save({ gen_type: 'random' })
}
function saveDan() {
  save({ gen_type: 'dan_random', dan_numbers: { red: sel.red, blue: sel.blue } })
}

onLoad(async () => {
  try {
    const list = await getLotteryList()
    const found = list.find((l) => l.code === code)
    if (found) rule.value = found.rule_config
    else emptyMsg.value = '彩种不存在'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
})
</script>

<style scoped>
.zone { background: #fff; margin: 16rpx 20rpx; padding: 20rpx; border-radius: 12rpx; }
.zt { font-size: 26rpx; color: #666; }
.grid { display: flex; flex-wrap: wrap; margin-top: 12rpx; }
.fields { margin: 0 20rpx; }
.ipt { background: #fff; border-radius: 10rpx; padding: 18rpx; margin-top: 16rpx; font-size: 26rpx; }
.actions { display: flex; flex-wrap: wrap; padding: 24rpx 20rpx; }
.btn { flex: 1; margin: 8rpx; background: #e53935; color: #fff; font-size: 26rpx; }
.btn.alt { background: #1e88e5; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 2: 浏览器/接口端到端目测**

后端在 8123 跑（同 Task5）。前端 `npm run dev:h5`。
Expected:
- 进"我的"→"去选号"：红/蓝区按 rule_config 出可点球。
- 点满红6蓝1 →"保存手选"可点 → 保存成功回列表，列表出现该记录。
- "机选保存"：直接保存一注随机号，回列表可见。
- 选少量红/蓝作胆码 →"定胆随机"：保存后列表出现完整一注(含胆码)。
- 填目标期号 2026062 保存后，列表点"比对"弹中奖结果。
可 curl 端到端验证：登录拿 token → 带 X-User-Id 的 create(random) → list 出现该记录。

- [ ] **Step 3: 全量前端测试**

Run: `npm test`
Expected: PASS（页面不影响既有单测，全绿）

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/mine/picker.vue
git commit -m "feat: 选号器页(手动/机选/定胆随机)"
```

---

## 计划自检

**1. Spec 覆盖：**
- token-in-header(后端兜底 header + 登录返回 token + CORS 头) → Task 1 ✓
- auth store 持久 token + device code 自动登录 → Task 2、ensureLogin Task 3 ✓
- request 带 X-User-Id 头 + user api(login/create/list/delete/check) → Task 3 ✓
- 选号纯逻辑 + 可点球 → Task 4 ✓
- 我的号码列表(比对/删除/进选号器) + tabBar 我的 → Task 5 ✓
- 选号器(手动/机选/定胆 + 备注/目标期号) → Task 6 ✓
- 中奖比对仅展示 → Task 5 doCheck(showModal，无兑奖) ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每个代码步骤含完整代码。

**3. 类型/签名一致性：**
- `authState`/`setToken`/`loadToken`(Task2) 被 request(Task3)/user(Task3) 引用一致。
- `getOrCreateDeviceCode`(Task2) 被 ensureLogin(Task3) 引用一致。
- `request(path,{method,data})`(已有/Task3) 被 user.js 调用一致；`login/createNumber/listNumbers/deleteNumber/checkNumber/ensureLogin`(Task3) 被 index(Task5)/picker(Task6) 引用一致。
- `toggleBall`/`selectionComplete`(Task4) 被 picker 页(Task6) 引用一致；`BallSelectable` props `{value,zone,selected}` + emit toggle(Task4) 被 picker 用法一致。
- 后端 `current_user_id` header 兜底(Task1) 支撑前端 token 头识别。
- 接口返回字段：create/list 返回 UserNumberSerializer({id,code,numbers,gen_type,dan_numbers,note,target_issue,created_at})；check 返回 {red_hit,blue_hit,level,label} —— index 页取法一致。

**4. 注意点（给执行者）：**
- 前端 vitest 测试里 mock `globalThis.uni` 的 storage/request；request 测试需先设 `authState.token`。
- 模块引用无环：auth(store) 不 import user/request；request import auth；user import request+auth+device。
- 端到端目测需后端 8123 + 前端 5199(vite.config 已绑)；示例开奖 2026060-2026062 用于比对。
- token=user_id hash，仅本浏览器可得自己的；不下发他人身份。
- create 的 target_issue/note 即使为空也随 payload 传(后端按空串处理)，无副作用。
