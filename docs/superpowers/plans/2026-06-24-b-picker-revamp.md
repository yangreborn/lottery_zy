# B · 选号器改造 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 选号器支持机选先预览不保存→勾选→保存选中，机选 5 注/10 注，隐藏定胆。

**Architecture:** 后端加预览生成接口(不写库) + create 接受机选选中的具体号码(gen_type=random+numbers)。前端 api 加 generateNumbers、utils 加 toggleIndex，picker.vue 重构为手动/机选双模式（机选批量预览+勾选筛选+保存选中+换一批），去掉定胆 UI。

**Tech Stack:** Django 5.2 + DRF；uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 返回统一 `make_response`（成功 code=0，应用级错误 code=1 且 HTTP 200）；后端日志 logging 禁止 print。
- 用户态接口 authentication_classes=[]，用 `current_user_id`（X-User-Id 头或 session）鉴权；未登录 code=1。
- generate 预览**不写库**；count 钳制 `[1,10]`，缺省/非整数按 5；号码用 `random_numbers(rule_config)` 生成并经 `validate_numbers` 校验合法。
- create：gen_type=random 且带非空 numbers → 用传入 numbers（validate_numbers 校验，非法 code=1）入库且 gen_type 仍记 random；不带 numbers → 服务端生成（旧行为兼容）。manual/dan_random 分支不变。
- 前端 uni-app(Vue3) JS 不引 Pinia/Vuex；request code=0 resolve body.data；机选保存对每个选中注调 createNumber(gen_type='random', numbers)。
- 定胆仅前端隐藏，后端 dan_random 代码保留不动。
- 前端命令在 `lottery_frontend/`；后端命令在 `lottery_backend/`(先激活 .venv)；端口后端 8123/前端 5199。

---

## File Structure

- `lottery_backend/usernumber/views.py`(改)：加 NumberGenerateView；NumberCreateView 的 random 分支接受 numbers。
- `lottery_backend/usernumber/urls.py`(改)：加 number/generate 路由。
- `lottery_backend/usernumber/tests/test_number_generate.py`(新)、`test_number_create.py`(改：加 random+numbers 用例)。
- `lottery_frontend/src/api/user.js`(改)：加 generateNumbers。
- `lottery_frontend/src/utils/picker.js`(改)：加 toggleIndex。
- `lottery_frontend/src/pages/mine/picker.vue`(改)：双模式重构。
- `lottery_frontend/tests/user.test.js`(改)、`picker.test.js`(改)。

---

### Task 1: 后端预览生成接口 generate

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（加 NumberGenerateView）
- Modify: `lottery_backend/usernumber/urls.py`
- Test: `lottery_backend/usernumber/tests/test_number_generate.py`

**Interfaces:**
- Consumes: `current_user_id`、`lottery.views._get_active_lottery`、`generator.random_numbers`、`make_response`
- Produces: `POST /api/user/number/generate {code, count}` → `data:{sets:[{red,blue},...]}`，不写库；未登录/未知彩种 code=1；count 钳制 [1,10]，非法按 5。

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_number_generate.py`:
```python
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery
from lottery.validators import validate_numbers
from usernumber.models import UserNumber


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


def test_generate_returns_count_valid_sets(ssq, auth_client):
    body = auth_client.post("/api/user/number/generate",
                            {"code": "ssq", "count": 5}, format="json").json()
    assert body["code"] == 0
    sets = body["data"]["sets"]
    assert len(sets) == 5
    for s in sets:
        assert validate_numbers(ssq.rule_config, s) == []


def test_generate_no_db_write(ssq, auth_client):
    auth_client.post("/api/user/number/generate", {"code": "ssq", "count": 5}, format="json")
    assert UserNumber.objects.count() == 0


def test_generate_count_clamp(ssq, auth_client):
    big = auth_client.post("/api/user/number/generate", {"code": "ssq", "count": 99}, format="json").json()
    assert len(big["data"]["sets"]) == 10
    zero = auth_client.post("/api/user/number/generate", {"code": "ssq", "count": 0}, format="json").json()
    assert len(zero["data"]["sets"]) == 1
    bad = auth_client.post("/api/user/number/generate", {"code": "ssq", "count": "x"}, format="json").json()
    assert len(bad["data"]["sets"]) == 5


def test_generate_unknown_code(auth_client):
    assert auth_client.post("/api/user/number/generate",
                            {"code": "nope", "count": 5}, format="json").json()["code"] == 1


def test_generate_unauthenticated(ssq):
    assert APIClient().post("/api/user/number/generate",
                            {"code": "ssq", "count": 5}, format="json").json()["code"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_number_generate.py -v`
Expected: FAIL（404 / 视图未定义）

- [ ] **Step 3: 写视图**

`lottery_backend/usernumber/views.py` 文件末尾追加（顶部已 import random_numbers / current_user_id / _get_active_lottery / make_response，无需新增 import）：
```python
class NumberGenerateView(APIView):
    """POST /api/user/number/generate —— 机选预览(不写库)。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        code = request.data.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        try:
            count = int(request.data.get("count", 5))
        except (TypeError, ValueError):
            count = 5
        count = max(1, min(count, 10))
        sets = [random_numbers(lottery.rule_config) for _ in range(count)]
        return Response(make_response(data={"sets": sets}))
```

- [ ] **Step 4: 加路由**

`lottery_backend/usernumber/urls.py` — 在 `number/<int:pk>` **之前**加一行：
```python
    path("number/generate", views.NumberGenerateView.as_view(), name="user-number-generate"),
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_number_generate.py -v`
Expected: PASS（5 passed）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_number_generate.py
git commit -m "feat: 机选预览生成接口 /api/user/number/generate"
```

---

### Task 2: create 接受机选选中号码

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（NumberCreateView 的 random 分支）
- Test: `lottery_backend/usernumber/tests/test_number_create.py`（追加用例）

**Interfaces:**
- Produces: create gen_type=random 时，带非空 numbers → 校验并用传入号码入库(gen_type 仍 random)；不带 → 服务端生成。

- [ ] **Step 1: 追加失败测试**

在 `lottery_backend/usernumber/tests/test_number_create.py` 末尾追加：
```python
def test_create_random_with_numbers_uses_provided(ssq, auth_client):
    nums = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}
    body = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random", "numbers": nums,
    }, format="json").json()
    assert body["code"] == 0
    assert body["data"]["gen_type"] == "random"
    assert body["data"]["numbers"] == nums


def test_create_random_with_invalid_numbers(ssq, auth_client):
    bad = {"red": [1, 2, 3], "blue": [7]}
    assert auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random", "numbers": bad,
    }, format="json").json()["code"] == 1


def test_create_random_without_numbers_generates(ssq, auth_client):
    body = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random",
    }, format="json").json()
    assert body["code"] == 0
    assert len(body["data"]["numbers"]["red"]) == 6
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_number_create.py -v`
Expected: FAIL（test_create_random_with_numbers_uses_provided：当前 random 分支忽略 numbers 自己生成，断言 numbers==nums 失败）

- [ ] **Step 3: 改 random 分支**

`lottery_backend/usernumber/views.py` 的 `NumberCreateView.post` 里，把：
```python
        if gen_type == UserNumber.GEN_RANDOM:
            numbers = random_numbers(lottery.rule_config)
```
改为：
```python
        if gen_type == UserNumber.GEN_RANDOM:
            provided = request.data.get("numbers")
            if provided:
                numbers = provided
                errors = validate_numbers(lottery.rule_config, numbers)
                if errors:
                    return Response(make_response(code=1, msg="号码非法", error="; ".join(errors)))
            else:
                numbers = random_numbers(lottery.rule_config)
```
（`validate_numbers` 已在文件顶部 import，无需新增。）

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_number_create.py -v`
Expected: PASS（含原有 6 + 新增 3）

- [ ] **Step 5: 全量回归**

Run: `python -m pytest -q`
Expected: PASS（之前 111 + generate 5 + create 3，全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/tests/test_number_create.py
git commit -m "feat: create 接受机选选中的具体号码(gen_type=random+numbers)"
```

---

### Task 3: 前端 generateNumbers + toggleIndex

**Files:**
- Modify: `lottery_frontend/src/api/user.js`
- Modify: `lottery_frontend/src/utils/picker.js`
- Test: `lottery_frontend/tests/user.test.js`（追加）、`tests/picker.test.js`（追加）

**Interfaces:**
- Produces:
  - `generateNumbers(code, count)` → POST `/api/user/number/generate` `{code, count}`
  - `toggleIndex(set, i)`：i 在集合则移除、否则加入并升序，返回新数组

- [ ] **Step 1: 追加失败测试**

在 `lottery_frontend/tests/user.test.js` 的 `import` 后把 user 导入补上 generateNumbers，并在 describe 内追加用例：
```js
// 顶部 import 改为含 generateNumbers
import { login, createNumber, listNumbers, deleteNumber, checkNumber, generateNumbers } from '../src/api/user.js'

// describe('user api') 内追加：
  it('generateNumbers', async () => {
    await generateNumbers('ssq', 5)
    expect(request).toHaveBeenCalledWith('/api/user/number/generate', { method: 'POST', data: { code: 'ssq', count: 5 } })
  })
```

在 `lottery_frontend/tests/picker.test.js` 顶部 import 补 toggleIndex，并追加 describe：
```js
// 顶部 import 改为含 toggleIndex
import { toggleBall, selectionComplete, toggleIndex } from '../src/utils/picker.js'

describe('toggleIndex', () => {
  it('未选则加入并升序', () => {
    expect(toggleIndex([2, 0], 1)).toEqual([0, 1, 2])
  })
  it('已选则移除', () => {
    expect(toggleIndex([0, 1, 2], 1)).toEqual([0, 2])
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（generateNumbers / toggleIndex 未定义）

- [ ] **Step 3: 写实现**

`lottery_frontend/src/api/user.js` 末尾追加：
```js
export function generateNumbers(code, count) {
  return request('/api/user/number/generate', { method: 'POST', data: { code, count } })
}
```

`lottery_frontend/src/utils/picker.js` 末尾追加：
```js
export function toggleIndex(set, i) {
  if (set.indexOf(i) >= 0) {
    return set.filter((x) => x !== i)
  }
  return [...set, i].sort((a, b) => a - b)
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS（user + picker 全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/api/user.js lottery_frontend/src/utils/picker.js lottery_frontend/tests/user.test.js lottery_frontend/tests/picker.test.js
git commit -m "feat: 前端 generateNumbers + toggleIndex 选中下标逻辑"
```

---

### Task 4: picker 双模式重构（机选预览筛选 + 隐藏定胆）

**Files:**
- Modify: `lottery_frontend/src/pages/mine/picker.vue`（整体替换）

**Interfaces:**
- Consumes: `generateNumbers`/`createNumber`/`ensureLogin`(api/user)、`getLotteryList`(api/lottery)、`lotteryStore`、`toggleBall`/`selectionComplete`/`toggleIndex`(utils/picker)、`Ball`/`BallSelectable`/`TopBanner`
- Produces: 选号页双模式（手动/机选）；机选批量预览+勾选+保存选中+换一批；无定胆。

- [ ] **Step 1: 整体替换 picker.vue**

`lottery_frontend/src/pages/mine/picker.vue`:
```vue
<template>
  <view class="page">
    <TopBanner title="选号" />
    <template v-if="rule">
      <view class="modes">
        <view class="mode" :class="{ active: mode === 'jixuan' }" @click="mode = 'jixuan'"><text>机选</text></view>
        <view class="mode" :class="{ active: mode === 'manual' }" @click="mode = 'manual'"><text>手动</text></view>
      </view>

      <view v-if="mode === 'jixuan'">
        <view class="gen-bar">
          <button class="btn" size="mini" @click="doGenerate(5)">机选5注</button>
          <button class="btn" size="mini" @click="doGenerate(10)">机选10注</button>
          <button class="btn alt" size="mini" :disabled="!sets.length" @click="reroll">换一批</button>
        </view>
        <view
          v-for="(s, i) in sets" :key="i"
          class="setrow" :class="{ sel: selected.includes(i) }" @click="toggleSel(i)"
        >
          <text class="chk">{{ selected.includes(i) ? '✓' : '○' }}</text>
          <view class="balls">
            <Ball v-for="(n, ri) in s.red" :key="'r'+ri" :value="n" zone="red" />
            <Ball v-for="(n, bi) in s.blue" :key="'b'+bi" :value="n" zone="blue" />
          </view>
        </view>
        <view v-if="!sets.length" class="hint">点上面“机选5注/10注”先生成，再勾选要保存的。</view>
      </view>

      <view v-else>
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
      </view>

      <view class="fields">
        <input class="ipt" v-model="note" placeholder="备注（可空）" />
        <input class="ipt" v-model="targetIssue" placeholder="目标期号（可空，用于比对）" />
      </view>
      <view class="actions">
        <button v-if="mode === 'jixuan'" class="btn save" :disabled="!selected.length" @click="saveBatch">
          保存选中({{ selected.length }})
        </button>
        <button v-else class="btn save" :disabled="!canSaveManual" @click="saveManual">保存手选</button>
      </view>
    </template>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import Ball from '../../components/Ball.vue'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, createNumber, generateNumbers } from '../../api/user.js'
import { toggleBall, selectionComplete, toggleIndex } from '../../utils/picker.js'

const rule = ref(null)
const emptyMsg = ref('加载中…')
const mode = ref('jixuan')
const code = lotteryStore.code

const sel = reactive({ red: [], blue: [] })
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

const sets = ref([])
const selected = ref([])
const lastCount = ref(5)

async function doGenerate(n) {
  lastCount.value = n
  try {
    await ensureLogin()
    const res = await generateNumbers(code, n)
    sets.value = res.sets || []
    selected.value = sets.value.map((_, i) => i)
  } catch (e) {
    uni.showToast({ title: e.msg || '生成失败', icon: 'none' })
  }
}
function reroll() { doGenerate(lastCount.value) }
function toggleSel(i) { selected.value = toggleIndex(selected.value, i) }

const note = ref('')
const targetIssue = ref('')

async function saveOne(numbers, genType) {
  await ensureLogin()
  return createNumber({ code, gen_type: genType, numbers, note: note.value, target_issue: targetIssue.value })
}

async function saveManual() {
  if (!canSaveManual.value) return
  try {
    await saveOne({ red: sel.red, blue: sel.blue }, 'manual')
    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.switchTab({ url: '/pages/mine/index' }), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
}

async function saveBatch() {
  if (!selected.value.length) {
    uni.showToast({ title: '请先勾选', icon: 'none' })
    return
  }
  let ok = 0
  let fail = 0
  for (const i of selected.value) {
    try { await saveOne(sets.value[i], 'random'); ok += 1 } catch (e) { fail += 1 }
  }
  uni.showToast({ title: fail ? `成功${ok}注 失败${fail}注` : `已保存${ok}注`, icon: fail ? 'none' : 'success' })
  if (ok && !fail) setTimeout(() => uni.switchTab({ url: '/pages/mine/index' }), 700)
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
.modes { display: flex; margin: 16rpx 20rpx; background: #fff; border-radius: 12rpx; overflow: hidden; }
.mode { flex: 1; text-align: center; padding: 20rpx 0; color: #666; font-size: 30rpx; }
.mode.active { background: #e53935; color: #fff; font-weight: 600; }
.gen-bar { display: flex; flex-wrap: wrap; padding: 12rpx 20rpx; }
.setrow { display: flex; align-items: center; background: #fff; margin: 12rpx 20rpx; padding: 18rpx; border-radius: 12rpx; border: 2rpx solid transparent; }
.setrow.sel { border-color: #e53935; }
.chk { font-size: 34rpx; color: #e53935; width: 48rpx; }
.balls { display: flex; flex-wrap: wrap; flex: 1; }
.hint { text-align: center; color: #999; padding: 40rpx 20rpx; font-size: 26rpx; }
.zone { background: #fff; margin: 16rpx 20rpx; padding: 20rpx; border-radius: 12rpx; }
.zt { font-size: 30rpx; color: #666; }
.grid { display: flex; flex-wrap: wrap; margin-top: 12rpx; }
.fields { margin: 0 20rpx; }
.ipt { background: #fff; border-radius: 10rpx; padding: 18rpx; margin-top: 16rpx; font-size: 28rpx; }
.actions { padding: 24rpx 20rpx; }
.btn { background: #e53935; color: #fff; font-size: 30rpx; margin: 8rpx; }
.btn.alt { background: #1e88e5; }
.btn.save { width: 100%; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 2: build + 端到端目测**

后端：`lottery_backend` 激活 venv → seed_lotteries → 后台 `runserver 127.0.0.1:8123`。前端：`npm run build:h5`(确认通过) 再 `npm run dev:h5`。
Expected:
- 进选号默认机选模式：「机选5注」出 5 注带 ✓（默认全选），点某注切换勾选；「换一批」重生成；「保存选中(N)」保存 → 我的号码出现选中注（机选标签）。
- 切「手动」：红/蓝点球、选满「保存手选」可用。
- 无定胆按钮。
curl 端到端：登录拿 token → generate `{code:ssq,count:5}` 返回 5 注 → 取一注 create `{code:ssq,gen_type:random,numbers:<那注>}` → list 出现该注 gen_type=random。

- [ ] **Step 3: 全量前端测试**

Run: `npm test`
Expected: PASS（picker 页改动不影响既有单测，全绿）

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/mine/picker.vue
git commit -m "feat: 选号器双模式(机选预览筛选+保存选中+换一批, 隐藏定胆)"
```

---

## 计划自检

**1. Spec 覆盖：**
- 预览生成接口(不写库, count 钳制) → Task 1 ✓
- create 接受机选选中号码(gen_type=random+numbers) → Task 2 ✓
- 前端 generateNumbers + toggleIndex → Task 3 ✓
- picker 双模式(机选预览/勾选/保存选中/换一批) + 隐藏定胆 → Task 4 ✓
- 备注/目标期号对保存生效 → Task 4 saveOne 带 note/target_issue ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `NumberGenerateView` 返回 `{sets:[{red,blue}]}`(Task1) 与前端 `res.sets`(Task4) 一致。
- create random+numbers(Task2) 与前端 saveBatch 调 createNumber(gen_type='random', numbers)(Task4) 一致。
- `generateNumbers(code,count)`/`toggleIndex(set,i)`(Task3) 被 picker(Task4) 引用一致。
- picker 仍是 tabBar 页：保存成功用 switchTab 回 mine/index（E 已确立），保留。

**4. 注意点（给执行者）：**
- generate 不写库（断言 UserNumber.count 不变）；count 钳 [1,10] 非法按 5。
- create random 带 numbers 才用传入（校验），不带仍生成——勿破坏旧 random 行为。
- picker 是 tabBar 页：保存成功 switchTab 到 /pages/mine/index（不可 navigateBack）。
- 定胆仅前端删 UI；后端 dan_random/generator 的 dan_random_numbers 不动。
- 机选默认全选（selected = 所有下标），勾选用 toggleIndex 维护下标集合。
- 端到端需后端 8123 + 数据；机选保存的注在「我的」显示 gen_type=random（机选）。
