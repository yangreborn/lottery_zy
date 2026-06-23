# M2b · uni-app H5 查询前端 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用 uni-app(Vue3+Vite) 做出可在浏览器(H5)直接看到效果的查询前端：当期/历史/详情/统计四页，调用已就绪的 M2a 只读接口。

**Architecture:** 新建 `lottery_frontend/`(uni-app, 与 lottery_backend 平级)。后端加 CORS + 示例数据命令让 H5 有内容可看。前端分层：utils 纯函数 → api 封装(uni.request 解析 {code,msg,data,error}) → components(Ball/LotteryTabs/Heatmap) → pages/draw/*。可单测的是 utils 与 api(vitest)，页面/组件靠浏览器目测。

**Tech Stack:** uni-app(Vue3 + Vite, JS)、vitest；后端 Django 5.2 + django-cors-headers。

## Global Constraints

- 前端用 uni-app(Vue3 + Vite)，JavaScript，不引 TS；不引 Pinia/Vuex(状态用 reactive)。
- API 返回结构是 `{code, msg, data, error}`：code=0 成功取 data，code!=0 为应用级错误。
- 统计功能是**纯数据陈列**，不得出现"预测/推荐"字样(合规红线)。
- 后端日志用 logging，禁止 print；异常 exc_info=True。
- CORS 仅 DEBUG 下放开：`if DEBUG: CORS_ALLOW_ALL_ORIGINS = True`；生产不开。
- 前端 API 基址读 `import.meta.env.VITE_API_BASE`，缺省 `http://127.0.0.1:8000`。
- 号码球红区色 `#e53935`，蓝区色 `#1e88e5`(全前端统一)。
- 前端命令统一在 `lottery_frontend/` 下跑；后端命令在 `lottery_backend/`(先激活 .venv)。
- 后端测试 DB：Docker 容器 lottery_pg(127.0.0.1:5433)，pytest.ini 已配 pythonpath。

---

## File Structure

- `lottery_backend/config/settings.py`(改)：加 corsheaders 到 INSTALLED_APPS/MIDDLEWARE + DEBUG 下 CORS 开关。
- `lottery_backend/requirements.txt`(改)：加 `django-cors-headers`。
- `lottery_backend/lottery/management/commands/seed_sample_draws.py`(新)：插入示例已发布开奖。
- `lottery_backend/lottery/tests/test_seed_sample_draws.py`(新)：命令测试。
- `lottery_frontend/`(新)：uni-app 工程
  - `src/utils/format.js`：纯函数(金额格式化、球色、统计分档)。
  - `src/api/request.js`：uni.request 封装。
  - `src/api/lottery.js`：5 个接口函数。
  - `src/store/lottery.js`：当前彩种 code(reactive)。
  - `src/components/{Ball,LotteryTabs,Heatmap}.vue`。
  - `src/pages/draw/{latest,history,detail,stats}.vue`。
  - `src/pages.json`、`src/App.vue`、`src/main.js`、`src/manifest.json`(脚手架生成)。
  - `tests/{format,request,lottery}.test.js`：vitest 单测。
  - `.env.development`、`vitest.config.js`、`vite.config.js`、`package.json`。

---

### Task 1: 后端启用 — CORS + 示例开奖数据命令

**Files:**
- Modify: `lottery_backend/requirements.txt`
- Modify: `lottery_backend/config/settings.py`
- Create: `lottery_backend/lottery/management/commands/seed_sample_draws.py`
- Test: `lottery_backend/lottery/tests/test_seed_sample_draws.py`

**Interfaces:**
- Consumes: `lottery.models.Lottery` / `DrawResult`、`lottery.validators.validate_numbers`
- Produces: management command `seed_sample_draws`，给 ssq/dlt 各插 ≥3 期 `status=published` 开奖；幂等(update_or_create 按 lottery+issue)。

- [ ] **Step 1: 装依赖并登记**

在 `lottery_backend` 激活 venv 后：
```bash
pip install django-cors-headers
```
`lottery_backend/requirements.txt` 追加一行：
```
django-cors-headers
```

- [ ] **Step 2: 改 settings 接入 CORS**

`lottery_backend/config/settings.py` — INSTALLED_APPS 在 `"rest_framework",` 后加 `"corsheaders",`：
```python
    "rest_framework",
    "corsheaders",
    "common",
```
MIDDLEWARE 在最前面插入 CorsMiddleware（必须在 CommonMiddleware 之前）：
```python
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
```
文件末尾追加（仅 DEBUG 放开）：
```python
# H5 本地开发跨域；生产同域 nginx，不放开
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
```

- [ ] **Step 3: 写失败测试**

`lottery_backend/lottery/tests/test_seed_sample_draws.py`:
```python
import pytest
from django.core.management import call_command
from lottery.models import Lottery, DrawResult
from lottery.validators import validate_numbers


@pytest.fixture
def seeded(db):
    call_command("seed_lotteries")


def test_creates_published_draws_for_both(seeded):
    call_command("seed_sample_draws")
    for code in ("ssq", "dlt"):
        qs = DrawResult.objects.filter(lottery__code=code,
                                       status=DrawResult.STATUS_PUBLISHED)
        assert qs.count() >= 3


def test_sample_numbers_are_valid(seeded):
    call_command("seed_sample_draws")
    for draw in DrawResult.objects.select_related("lottery"):
        errors = validate_numbers(draw.lottery.rule_config, draw.numbers)
        assert errors == []


def test_idempotent(seeded):
    call_command("seed_sample_draws")
    call_command("seed_sample_draws")
    # 第二次不应重复插入（按 lottery+issue 唯一）
    assert DrawResult.objects.filter(lottery__code="ssq").count() == \
        DrawResult.objects.filter(lottery__code="ssq", status=DrawResult.STATUS_PUBLISHED).count()
```

- [ ] **Step 4: 跑测试确认失败**

Run: `python -m pytest lottery/tests/test_seed_sample_draws.py -v`
Expected: FAIL（`Unknown command: 'seed_sample_draws'`）

- [ ] **Step 5: 写命令**

`lottery_backend/lottery/management/commands/seed_sample_draws.py`:
```python
import logging
import datetime
from django.core.management.base import BaseCommand
from lottery.models import Lottery, DrawResult

logger = logging.getLogger(__name__)

# 示例开奖（合理示例值，号码均符合各自 rule_config）
SAMPLES = {
    "ssq": [
        {"issue": "2026060", "draw_date": "2026-06-01",
         "numbers": {"red": [3, 8, 15, 22, 27, 31], "blue": [5]},
         "pool_amount": "1532000000",
         "prize_grades": [{"level": 1, "count": 6, "amount": "8500000"},
                          {"level": 2, "count": 120, "amount": "180000"}]},
        {"issue": "2026061", "draw_date": "2026-06-04",
         "numbers": {"red": [1, 9, 12, 20, 28, 33], "blue": [11]},
         "pool_amount": "1488000000",
         "prize_grades": [{"level": 1, "count": 4, "amount": "9200000"},
                          {"level": 2, "count": 98, "amount": "210000"}]},
        {"issue": "2026062", "draw_date": "2026-06-06",
         "numbers": {"red": [6, 11, 17, 24, 29, 32], "blue": [2]},
         "pool_amount": "1605000000",
         "prize_grades": [{"level": 1, "count": 7, "amount": "7800000"},
                          {"level": 2, "count": 130, "amount": "165000"}]},
    ],
    "dlt": [
        {"issue": "2026060", "draw_date": "2026-06-02",
         "numbers": {"red": [4, 13, 21, 28, 34], "blue": [3, 9]},
         "pool_amount": "980000000",
         "prize_grades": [{"level": 1, "count": 3, "amount": "10000000"},
                          {"level": 2, "count": 50, "amount": "250000"}]},
        {"issue": "2026061", "draw_date": "2026-06-04",
         "numbers": {"red": [7, 16, 22, 30, 35], "blue": [1, 12]},
         "pool_amount": "1020000000",
         "prize_grades": [{"level": 1, "count": 2, "amount": "11000000"},
                          {"level": 2, "count": 44, "amount": "270000"}]},
        {"issue": "2026062", "draw_date": "2026-06-07",
         "numbers": {"red": [2, 10, 19, 26, 33], "blue": [5, 8]},
         "pool_amount": "1055000000",
         "prize_grades": [{"level": 1, "count": 5, "amount": "9000000"},
                          {"level": 2, "count": 61, "amount": "230000"}]},
    ],
}


class Command(BaseCommand):
    help = "插入双色球/大乐透示例已发布开奖（开发演示用，幂等）"

    def handle(self, *args, **options):
        for code, draws in SAMPLES.items():
            lottery = Lottery.objects.filter(code=code).first()
            if lottery is None:
                logger.warning("彩种 %s 不存在，先跑 seed_lotteries", code)
                continue
            for d in draws:
                obj, created = DrawResult.objects.update_or_create(
                    lottery=lottery, issue=d["issue"],
                    defaults={
                        "draw_date": datetime.date.fromisoformat(d["draw_date"]),
                        "numbers": d["numbers"],
                        "pool_amount": d["pool_amount"],
                        "prize_grades": d["prize_grades"],
                        "source": DrawResult.SOURCE_MANUAL,
                        "status": DrawResult.STATUS_PUBLISHED,
                    },
                )
                logger.info("sample draw %s %s %s", code, d["issue"],
                            "created" if created else "updated")
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python -m pytest lottery/tests/test_seed_sample_draws.py -v`
Expected: PASS（3 passed）

- [ ] **Step 7: 提交**

```bash
git add lottery_backend/requirements.txt lottery_backend/config/settings.py lottery_backend/lottery/management/commands/seed_sample_draws.py lottery_backend/lottery/tests/test_seed_sample_draws.py
git commit -m "feat: 后端 CORS 接入 + 示例开奖数据命令 seed_sample_draws"
```

---

### Task 2: uni-app 脚手架 + vitest 起步

**Files:**
- Create: `lottery_frontend/`（uni-app Vite 预设）
- Create: `lottery_frontend/.env.development`
- Create: `lottery_frontend/vitest.config.js`
- Create: `lottery_frontend/tests/smoke.test.js`
- Modify: `lottery_frontend/package.json`（加 test 脚本与 vitest）
- Modify: `lottery_backend/../.gitignore` 根 `.gitignore`（忽略 node_modules）

**Interfaces:**
- Produces: 可运行的 uni-app 工程；`npm run dev:h5` 能启动；`npm test` 能跑 vitest。

- [ ] **Step 1: 拉取 uni-app Vite 预设**

在仓库根 `lottery`(即 D:\PythonProject\ma3you_community\lotteryy)下：
```bash
npx degit dcloudio/uni-preset-vue#vite lottery_frontend
cd lottery_frontend
npm install
npm install -D vitest
```

- [ ] **Step 2: 配置 H5 端口与 API 基址**

`lottery_frontend/.env.development`:
```
VITE_API_BASE=http://127.0.0.1:8000
```

`lottery_frontend/vitest.config.js`（独立于 uni 插件，纯 node 环境跑单测）:
```js
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node',
    include: ['tests/**/*.test.js'],
  },
})
```

根 `.gitignore`(D:\PythonProject\ma3you_community\lotteryy\.gitignore) 追加：
```
lottery_frontend/node_modules/
lottery_frontend/dist/
lottery_frontend/unpackage/
```

- [ ] **Step 3: 写冒烟测试**

`lottery_frontend/tests/smoke.test.js`:
```js
import { describe, it, expect } from 'vitest'

describe('vitest 起步', () => {
  it('能跑通', () => {
    expect(1 + 1).toBe(2)
  })
})
```

- [ ] **Step 4: 加 test 脚本**

`lottery_frontend/package.json` 的 `scripts` 加一行（与已有 dev:h5/build:h5 并列）：
```json
    "test": "vitest run",
```

- [ ] **Step 5: 跑测试 + 验证 H5 能启动**

Run: `npm test`
Expected: PASS（1 passed）

Run（验证启动后用 Ctrl+C 退出，不需长跑）: `npm run dev:h5`
Expected: 输出本地访问地址（如 `http://localhost:5173`），无报错即可。

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/.env.development lottery_frontend/vitest.config.js lottery_frontend/tests/smoke.test.js lottery_frontend/package.json lottery_frontend/package-lock.json lottery_frontend/src lottery_frontend/index.html lottery_frontend/vite.config.js .gitignore
git commit -m "feat: uni-app H5 脚手架 + vitest 起步"
```
（注：`lottery_frontend/node_modules` 已被 .gitignore 排除，不要 add。）

---

### Task 3: utils/format.js 纯函数

**Files:**
- Create: `lottery_frontend/src/utils/format.js`
- Test: `lottery_frontend/tests/format.test.js`

**Interfaces:**
- Produces:
  - `ballColor(zone) -> string`：'red'→'#e53935'，'blue'→'#1e88e5'，其他→'#9e9e9e'
  - `formatAmount(raw) -> string`：数字字符串千分位分组；空/非法→'—'
  - `statsTier(count, max) -> number`：0..4，按 count/max 占比分档（max<=0 时返回 0）

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/format.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { ballColor, formatAmount, statsTier } from '../src/utils/format.js'

describe('ballColor', () => {
  it('红蓝灰', () => {
    expect(ballColor('red')).toBe('#e53935')
    expect(ballColor('blue')).toBe('#1e88e5')
    expect(ballColor('x')).toBe('#9e9e9e')
  })
})

describe('formatAmount', () => {
  it('千分位', () => {
    expect(formatAmount('1532000000')).toBe('1,532,000,000')
    expect(formatAmount('1000')).toBe('1,000')
  })
  it('空或非法返回破折号', () => {
    expect(formatAmount('')).toBe('—')
    expect(formatAmount(null)).toBe('—')
    expect(formatAmount('abc')).toBe('—')
  })
})

describe('statsTier', () => {
  it('按占比分 0..4', () => {
    expect(statsTier(0, 10)).toBe(0)
    expect(statsTier(10, 10)).toBe(4)
    expect(statsTier(5, 10)).toBe(2)
  })
  it('max<=0 返回 0', () => {
    expect(statsTier(3, 0)).toBe(0)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（`Cannot find module ../src/utils/format.js`）

- [ ] **Step 3: 写实现**

`lottery_frontend/src/utils/format.js`:
```js
export function ballColor(zone) {
  if (zone === 'red') return '#e53935'
  if (zone === 'blue') return '#1e88e5'
  return '#9e9e9e'
}

export function formatAmount(raw) {
  if (raw === null || raw === undefined || raw === '') return '—'
  const n = Number(raw)
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString('en-US')
}

export function statsTier(count, max) {
  if (!max || max <= 0) return 0
  const ratio = count / max
  if (ratio <= 0) return 0
  if (ratio >= 1) return 4
  return Math.min(4, Math.max(1, Math.ceil(ratio * 4)))
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS（format 全绿 + 之前 smoke）

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/format.js lottery_frontend/tests/format.test.js
git commit -m "feat: 前端纯函数 ballColor/formatAmount/statsTier"
```

---

### Task 4: API 封装 request + lottery

**Files:**
- Create: `lottery_frontend/src/api/request.js`
- Create: `lottery_frontend/src/api/lottery.js`
- Test: `lottery_frontend/tests/request.test.js`
- Test: `lottery_frontend/tests/lottery.test.js`

**Interfaces:**
- Produces:
  - `request(path, { method='GET', data } = {}) -> Promise`：拼 baseURL，调 `uni.request`；HTTP 200 且 body.code===0 → resolve `body.data`；body.code!==0 → reject `{code, msg}`；网络/非 200 → reject `{code:-1, msg}`。
  - `api/lottery.js`：`getLotteryList()`、`getLatest(code)`、`getHistory(code, params={})`、`getDetail(code, issue)`、`getStats(code, periods)`，均返回 `request(...)`。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/request.test.js`:
```js
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { request } from '../src/api/request.js'

function stubUni(handler) {
  globalThis.uni = { request: handler }
}

describe('request', () => {
  beforeEach(() => { globalThis.uni = undefined })

  it('code=0 resolve data', async () => {
    stubUni(({ success }) => success({ statusCode: 200, data: { code: 0, msg: 'ok', data: { x: 1 }, error: null } }))
    await expect(request('/api/openapi/lottery/list')).resolves.toEqual({ x: 1 })
  })

  it('code!=0 reject {code,msg}', async () => {
    stubUni(({ success }) => success({ statusCode: 200, data: { code: 1, msg: '未知彩种', data: null, error: 'x' } }))
    await expect(request('/api/openapi/draw/latest')).rejects.toMatchObject({ code: 1, msg: '未知彩种' })
  })

  it('网络失败 reject code=-1', async () => {
    stubUni(({ fail }) => fail({ errMsg: 'request:fail' }))
    await expect(request('/api/openapi/draw/latest')).rejects.toMatchObject({ code: -1 })
  })
})
```

`lottery_frontend/tests/lottery.test.js`:
```js
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({
  request: vi.fn(() => Promise.resolve('OK')),
}))
import { request } from '../src/api/request.js'
import { getLatest, getHistory, getStats } from '../src/api/lottery.js'

describe('lottery api', () => {
  beforeEach(() => { request.mockClear() })

  it('getLatest 带 code', async () => {
    await getLatest('ssq')
    expect(request).toHaveBeenCalledWith('/api/openapi/draw/latest', { data: { code: 'ssq' } })
  })

  it('getHistory 合并参数', async () => {
    await getHistory('dlt', { page: 2, date_from: '2026-06-01' })
    expect(request).toHaveBeenCalledWith('/api/openapi/draw/history',
      { data: { code: 'dlt', page: 2, date_from: '2026-06-01' } })
  })

  it('getStats 带 periods', async () => {
    await getStats('ssq', 30)
    expect(request).toHaveBeenCalledWith('/api/openapi/draw/stats', { data: { code: 'ssq', periods: 30 } })
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（找不到 api 模块）

- [ ] **Step 3: 写实现**

`lottery_frontend/src/api/request.js`:
```js
const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'

export function request(path, { method = 'GET', data } = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE + path,
      method,
      data,
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

`lottery_frontend/src/api/lottery.js`:
```js
import { request } from './request.js'

export function getLotteryList() {
  return request('/api/openapi/lottery/list')
}

export function getLatest(code) {
  return request('/api/openapi/draw/latest', { data: { code } })
}

export function getHistory(code, params = {}) {
  return request('/api/openapi/draw/history', { data: { code, ...params } })
}

export function getDetail(code, issue) {
  return request('/api/openapi/draw/detail', { data: { code, issue } })
}

export function getStats(code, periods) {
  return request('/api/openapi/draw/stats', { data: { code, periods } })
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS（request + lottery 全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/api/request.js lottery_frontend/src/api/lottery.js lottery_frontend/tests/request.test.js lottery_frontend/tests/lottery.test.js
git commit -m "feat: 前端 API 封装 request + lottery 接口函数"
```

---

### Task 5: 组件 Ball / LotteryTabs + store

**Files:**
- Create: `lottery_frontend/src/store/lottery.js`
- Create: `lottery_frontend/src/components/Ball.vue`
- Create: `lottery_frontend/src/components/LotteryTabs.vue`

**Interfaces:**
- Consumes: `utils/format.js` 的 `ballColor`、`api/lottery.js` 的 `getLotteryList`
- Produces:
  - `store/lottery.js`：`export const lotteryStore = reactive({ code: 'ssq' })` + `export function setCode(c)`
  - `Ball.vue`：props `{ value:Number, zone:String }`，圆形号码球，底色由 ballColor(zone)
  - `LotteryTabs.vue`：props `{ list:Array, active:String }`，emit `change`；list 元素含 `{code,name}`

- [ ] **Step 1: 写 store（无测试，纯状态）**

`lottery_frontend/src/store/lottery.js`:
```js
import { reactive } from 'vue'

export const lotteryStore = reactive({ code: 'ssq' })

export function setCode(c) {
  lotteryStore.code = c
}
```

- [ ] **Step 2: 写 Ball 组件**

`lottery_frontend/src/components/Ball.vue`:
```vue
<template>
  <view class="ball" :style="{ backgroundColor: color }">
    <text class="num">{{ display }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { ballColor } from '../utils/format.js'

const props = defineProps({
  value: { type: [Number, String], required: true },
  zone: { type: String, default: 'red' },
})

const color = computed(() => ballColor(props.zone))
const display = computed(() => String(props.value).padStart(2, '0'))
</script>

<style scoped>
.ball {
  width: 60rpx; height: 60rpx; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  margin: 6rpx;
}
.num { color: #fff; font-size: 28rpx; font-weight: 600; }
</style>
```

- [ ] **Step 3: 写 LotteryTabs 组件**

`lottery_frontend/src/components/LotteryTabs.vue`:
```vue
<template>
  <view class="tabs">
    <view
      v-for="item in list"
      :key="item.code"
      class="tab"
      :class="{ active: item.code === active }"
      @click="$emit('change', item.code)"
    >
      <text>{{ item.name }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  list: { type: Array, default: () => [] },
  active: { type: String, default: '' },
})
defineEmits(['change'])
</script>

<style scoped>
.tabs { display: flex; border-bottom: 1px solid #eee; }
.tab { flex: 1; text-align: center; padding: 20rpx 0; color: #666; }
.tab.active { color: #e53935; border-bottom: 4rpx solid #e53935; font-weight: 600; }
</style>
```

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/store/lottery.js lottery_frontend/src/components/Ball.vue lottery_frontend/src/components/LotteryTabs.vue
git commit -m "feat: 号码球 Ball、彩种切换 LotteryTabs、彩种 store"
```

---

### Task 6: 当期开奖页 latest + 路由/tabBar

**Files:**
- Create: `lottery_frontend/src/pages/draw/latest.vue`
- Modify: `lottery_frontend/src/pages.json`（注册 4 个页面 + tabBar 3 项）

**Interfaces:**
- Consumes: `getLotteryList`、`getLatest`、`lotteryStore`/`setCode`、`Ball`、`LotteryTabs`、`formatAmount`
- Produces: 首页 `pages/draw/latest`，浏览器可见当期开奖。

- [ ] **Step 1: 配 pages.json**

`lottery_frontend/src/pages.json`（整体替换为下面内容；脚手架原 index 页可删，但保留 globalStyle 习惯）:
```json
{
  "pages": [
    { "path": "pages/draw/latest", "style": { "navigationBarTitleText": "当期开奖" } },
    { "path": "pages/draw/history", "style": { "navigationBarTitleText": "历史开奖" } },
    { "path": "pages/draw/detail", "style": { "navigationBarTitleText": "开奖详情" } },
    { "path": "pages/draw/stats", "style": { "navigationBarTitleText": "号码统计" } }
  ],
  "tabBar": {
    "color": "#666",
    "selectedColor": "#e53935",
    "list": [
      { "pagePath": "pages/draw/latest", "text": "当期" },
      { "pagePath": "pages/draw/history", "text": "历史" },
      { "pagePath": "pages/draw/stats", "text": "统计" }
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

- [ ] **Step 2: 写 latest 页**

`lottery_frontend/src/pages/draw/latest.vue`:
```vue
<template>
  <view class="page">
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view v-if="draw" class="card">
      <view class="head">
        <text class="issue">第 {{ draw.issue }} 期</text>
        <text class="date">{{ draw.draw_date }}</text>
      </view>
      <view class="balls">
        <Ball v-for="(n, i) in draw.numbers.red" :key="'r'+i" :value="n" zone="red" />
        <Ball v-for="(n, i) in draw.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
      </view>
      <view class="pool">奖池：{{ formatAmount(draw.pool_amount) }} 元</view>
      <view class="grades">
        <view v-for="(g, i) in draw.prize_grades" :key="i" class="grade">
          <text>{{ g.level_label || g.level }}</text>
          <text>{{ g.count }} 注</text>
          <text>{{ formatAmount(g.amount) }} 元</text>
        </view>
      </view>
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getLatest } from '../../api/lottery.js'
import { formatAmount } from '../../utils/format.js'

const store = lotteryStore
const lotteries = ref([])
const draw = ref(null)
const emptyMsg = ref('加载中…')

async function load() {
  draw.value = null
  emptyMsg.value = '加载中…'
  try {
    draw.value = await getLatest(store.code)
  } catch (e) {
    emptyMsg.value = e.msg || '暂无数据'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) {
  setCode(code)
  load()
}

onMounted(async () => {
  try {
    lotteries.value = await getLotteryList()
  } catch (e) {
    uni.showToast({ title: e.msg || '彩种加载失败', icon: 'none' })
  }
})
onShow(load)
</script>

<style scoped>
.page { padding: 0 0 30rpx; }
.card { background: #fff; margin: 20rpx; padding: 30rpx; border-radius: 16rpx; }
.head { display: flex; justify-content: space-between; color: #888; font-size: 26rpx; }
.balls { display: flex; flex-wrap: wrap; margin: 24rpx 0; }
.pool { color: #e53935; font-size: 28rpx; margin-bottom: 16rpx; }
.grades { border-top: 1px solid #f0f0f0; padding-top: 16rpx; }
.grade { display: flex; justify-content: space-between; padding: 10rpx 0; font-size: 26rpx; color: #555; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 3: 浏览器目测**

后端先跑：`lottery_backend` 下激活 venv，`python manage.py migrate`（如首次）→ `python manage.py seed_lotteries` → `python manage.py seed_sample_draws` → `python manage.py runserver`。
前端：`lottery_frontend` 下 `npm run dev:h5`，浏览器打开地址。
Expected: "当期"页显示双色球第 2026062 期 6 红 1 蓝号码球 + 奖池 + 奖级；点顶部切到大乐透显示对应数据。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages.json lottery_frontend/src/pages/draw/latest.vue
git commit -m "feat: 当期开奖页 + tabBar 路由"
```

---

### Task 7: 历史页 history + 详情页 detail

**Files:**
- Create: `lottery_frontend/src/pages/draw/history.vue`
- Create: `lottery_frontend/src/pages/draw/detail.vue`

**Interfaces:**
- Consumes: `getHistory`、`getDetail`、`lotteryStore`、`Ball`、`formatAmount`
- Produces: 历史分页列表(点行跳详情)；详情页含奖级表。

- [ ] **Step 1: 写 history 页**

`lottery_frontend/src/pages/draw/history.vue`:
```vue
<template>
  <view class="page">
    <scroll-view scroll-y class="list" @scrolltolower="loadMore">
      <view
        v-for="d in items"
        :key="d.issue"
        class="row"
        @click="goDetail(d.issue)"
      >
        <view class="row-top">
          <text class="issue">第 {{ d.issue }} 期</text>
          <text class="date">{{ d.draw_date }}</text>
        </view>
        <view class="balls">
          <Ball v-for="(n, i) in d.numbers.red" :key="'r'+i" :value="n" zone="red" />
          <Ball v-for="(n, i) in d.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
        </view>
      </view>
      <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
      <view v-else-if="!hasMore" class="end">没有更多了</view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import Ball from '../../components/Ball.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getHistory } from '../../api/lottery.js'

const items = ref([])
const page = ref(1)
const hasMore = ref(true)
const loading = ref(false)
const emptyMsg = ref('加载中…')
let loadedCode = ''

async function fetchPage(reset) {
  if (loading.value) return
  loading.value = true
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  try {
    const res = await getHistory(lotteryStore.code, { page: page.value })
    const list = res.results || []
    items.value = items.value.concat(list)
    hasMore.value = items.value.length < (res.total || 0)
    if (!items.value.length) emptyMsg.value = '暂无数据'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function loadMore() {
  if (!hasMore.value) return
  page.value += 1
  fetchPage(false)
}

function goDetail(issue) {
  uni.navigateTo({ url: `/pages/draw/detail?code=${lotteryStore.code}&issue=${issue}` })
}

onShow(() => {
  if (loadedCode !== lotteryStore.code) {
    loadedCode = lotteryStore.code
    fetchPage(true)
  }
})
</script>

<style scoped>
.page { height: 100vh; }
.list { height: 100vh; }
.row { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.row-top { display: flex; justify-content: space-between; color: #888; font-size: 26rpx; }
.balls { display: flex; flex-wrap: wrap; margin-top: 14rpx; }
.empty, .end { text-align: center; color: #999; padding: 40rpx 0; font-size: 26rpx; }
</style>
```

- [ ] **Step 2: 写 detail 页**

`lottery_frontend/src/pages/draw/detail.vue`:
```vue
<template>
  <view class="page">
    <view v-if="draw" class="card">
      <view class="head">
        <text class="issue">第 {{ draw.issue }} 期</text>
        <text class="date">{{ draw.draw_date }}</text>
      </view>
      <view class="balls">
        <Ball v-for="(n, i) in draw.numbers.red" :key="'r'+i" :value="n" zone="red" />
        <Ball v-for="(n, i) in draw.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
      </view>
      <view class="pool">奖池：{{ formatAmount(draw.pool_amount) }} 元</view>
      <view class="grades">
        <view class="grade head-row">
          <text>奖级</text><text>中奖注数</text><text>单注奖金</text>
        </view>
        <view v-for="(g, i) in draw.prize_grades" :key="i" class="grade">
          <text>{{ g.level_label || g.level }}</text>
          <text>{{ g.count }}</text>
          <text>{{ formatAmount(g.amount) }}</text>
        </view>
      </view>
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import Ball from '../../components/Ball.vue'
import { getDetail } from '../../api/lottery.js'
import { formatAmount } from '../../utils/format.js'

const draw = ref(null)
const emptyMsg = ref('加载中…')

onLoad(async (q) => {
  try {
    draw.value = await getDetail(q.code, q.issue)
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
})
</script>

<style scoped>
.card { background: #fff; margin: 20rpx; padding: 30rpx; border-radius: 16rpx; }
.head { display: flex; justify-content: space-between; color: #888; font-size: 26rpx; }
.balls { display: flex; flex-wrap: wrap; margin: 24rpx 0; }
.pool { color: #e53935; font-size: 28rpx; margin-bottom: 16rpx; }
.grades { border-top: 1px solid #f0f0f0; padding-top: 16rpx; }
.grade { display: flex; justify-content: space-between; padding: 10rpx 0; font-size: 26rpx; color: #555; }
.head-row { color: #999; font-weight: 600; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 3: 浏览器目测**

`npm run dev:h5`（后端仍在跑）。
Expected: "历史"页倒序列出各期，触底加载下一页；点任意一行进入详情，显示奖级表（中文奖级来自 level_label）。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/draw/history.vue lottery_frontend/src/pages/draw/detail.vue
git commit -m "feat: 历史列表页 + 单期详情页"
```

---

### Task 8: 统计页 stats + Heatmap

**Files:**
- Create: `lottery_frontend/src/components/Heatmap.vue`
- Create: `lottery_frontend/src/pages/draw/stats.vue`

**Interfaces:**
- Consumes: `getStats`、`lotteryStore`、`statsTier`
- Produces: 统计页（选最近 N 期），Heatmap 展示每号码出现次数/遗漏值，按次数分档配色。纯陈列。

- [ ] **Step 1: 写 Heatmap 组件**

`lottery_frontend/src/components/Heatmap.vue`:
```vue
<template>
  <view class="grid">
    <view
      v-for="c in cells"
      :key="c.number"
      class="cell"
      :style="{ backgroundColor: tierColor(c.count) }"
    >
      <text class="n">{{ String(c.number).padStart(2, '0') }}</text>
      <text class="meta">{{ c.count }}次</text>
      <text class="meta">遗漏{{ c.miss }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { statsTier } from '../utils/format.js'

const props = defineProps({
  cells: { type: Array, default: () => [] },
})

const max = computed(() => props.cells.reduce((m, c) => Math.max(m, c.count), 0))

const TIER_COLORS = ['#eeeeee', '#ffe0b2', '#ffb74d', '#fb8c00', '#e65100']
function tierColor(count) {
  return TIER_COLORS[statsTier(count, max.value)]
}
</script>

<style scoped>
.grid { display: flex; flex-wrap: wrap; padding: 16rpx; }
.cell {
  width: 96rpx; height: 96rpx; margin: 8rpx; border-radius: 10rpx;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.n { font-size: 26rpx; font-weight: 600; color: #333; }
.meta { font-size: 18rpx; color: #555; }
</style>
```

- [ ] **Step 2: 写 stats 页**

`lottery_frontend/src/pages/draw/stats.vue`:
```vue
<template>
  <view class="page">
    <view class="periods">
      <view
        v-for="p in periodOptions"
        :key="p"
        class="opt"
        :class="{ active: p === periods }"
        @click="choose(p)"
      >
        <text>近{{ p }}期</text>
      </view>
    </view>
    <view class="zone-title">红球</view>
    <Heatmap :cells="redCells" />
    <view class="zone-title">蓝球</view>
    <Heatmap :cells="blueCells" />
    <view v-if="!redCells.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import Heatmap from '../../components/Heatmap.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getStats } from '../../api/lottery.js'

const periodOptions = [10, 30, 50, 100]
const periods = ref(30)
const redCells = ref([])
const blueCells = ref([])
const emptyMsg = ref('加载中…')

async function load() {
  try {
    const res = await getStats(lotteryStore.code, periods.value)
    redCells.value = res.red || []
    blueCells.value = res.blue || []
    if (!redCells.value.length) emptyMsg.value = '暂无数据'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function choose(p) {
  periods.value = p
  load()
}

onShow(load)
</script>

<style scoped>
.periods { display: flex; padding: 20rpx; }
.opt { padding: 12rpx 24rpx; margin-right: 16rpx; background: #fff; border-radius: 30rpx; color: #666; font-size: 26rpx; }
.opt.active { background: #e53935; color: #fff; }
.zone-title { padding: 16rpx 24rpx 0; color: #888; font-size: 26rpx; }
.empty { text-align: center; color: #999; padding: 60rpx 0; }
</style>
```

- [ ] **Step 3: 浏览器目测**

`npm run dev:h5`（后端在跑）。
Expected: "统计"页默认近30期，红球/蓝球各一组热力格子，显示号码+出现次数+遗漏；切近10/50/100期数据刷新；颜色按出现次数深浅分档。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/components/Heatmap.vue lottery_frontend/src/pages/draw/stats.vue
git commit -m "feat: 号码统计页 + 热力图组件"
```

---

## 计划自检

**1. Spec 覆盖：**
- uni-app H5 工程 + vitest → Task 2 ✓
- CORS + 示例数据 → Task 1 ✓
- 纯函数(球色/金额/分档) → Task 3 ✓
- API 封装(5 接口 + {code,msg,data,error}) → Task 4 ✓
- 组件 Ball/LotteryTabs/Heatmap → Task 5、Task 8 ✓
- store(reactive 当前彩种) → Task 5 ✓
- 当期/历史/详情/统计四页 + tabBar → Task 6/7/8 ✓
- 统计纯陈列不预测 → Task 8 文案无"预测/推荐" ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每个代码步骤含完整代码。

**3. 类型/签名一致性：**
- `ballColor/formatAmount/statsTier`(Task3) 被 Ball/latest/Heatmap 引用一致。
- `request(path,{method,data})`(Task4) 被 lottery.js 调用一致；`getLatest/getHistory/getDetail/getStats/getLotteryList` 签名 Task4 定义，Task6/7/8 引用一致。
- `lotteryStore.code`/`setCode`(Task5) 被各页引用一致。
- 接口返回字段：latest/detail 用 `numbers.{red,blue}`、`pool_amount`、`prize_grades[].{level_label,count,amount}`；history 用 `{results,total}`；stats 用 `{red,blue}` 每项 `{number,count,miss}` —— 均与 M2a serializers 对齐。

**4. 注意点（给执行者）：**
- 前端命令在 `lottery_frontend/`；后端命令在 `lottery_backend/` 先激活 .venv。
- `node_modules` 不入库（已 .gitignore）。
- 页面/组件无单测，靠 `npm run dev:h5` 浏览器目测；目测需后端 runserver + seed_lotteries + seed_sample_draws 有数据。
- vitest 用独立 `vitest.config.js`(node 环境)，不加载 uni 插件。
- `level_label` 是 M2a DrawDetailSerializer 提供的中文奖级；latest 用的是 DrawResultSerializer，可能无 level_label，故模板用 `g.level_label || g.level` 兜底。
