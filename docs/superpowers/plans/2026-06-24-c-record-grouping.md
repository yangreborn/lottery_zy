# C · 选号记录显示时间 + 分组 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 选号记录显示选号时间，支持把已有记录归到分组，"我的号码"按组展示。

**Architecture:** 后端 UserNumber 加 group_name 字段 + 归组接口；前端纯函数 formatTime/groupRecords；mine/index.vue 显示时间 + 按组渲染 + 每条"归组"操作。

**Tech Stack:** Django 5.2 + DRF（后端）；uni-app(Vue3+Vite, JS) + vitest（前端）。

## Global Constraints

- 后端日志用 logging，禁止 print；统一 make_response({code,msg,data,error})，code=0 成功/code=1 应用错误（HTTP 200）。
- 归组接口本人记录隔离：`UserNumber.objects.filter(id=rec_id, user_id=uid).first()`；未登录/不存在/非本人 → code=1。
- group_name 规则：`str(request.data.get("group_name") or "").strip()[:50]`（去空白、超 50 截断；空串=取消分组）。
- NumberGroupView authentication_classes=[]（与其他 number 接口一致，认证靠 current_user_id 读 X-User-Id/session）；url `number/group` 放 `number/<int:pk>` 之前。
- formatTime(iso)→`YYYY-MM-DD HH:mm`（本地时间，补零）；空/非法返回 ''。
- groupRecords(items)→`[{name, records}]`；空名归 '未分组'；命名组 name 升序在前，'未分组' 殿后；非数组返回 []；不改入参。
- 前端 Vue3 JS 不引 Pinia/Vuex；无 console。后端命令在 `lottery_backend/`（先激活 .venv），测试 DB Docker lottery_pg 127.0.0.1:5433；前端在 `lottery_frontend/`。

---

## File Structure

- `lottery_backend/usernumber/models.py`(改)：加 group_name 字段。
- `lottery_backend/usernumber/migrations/000X_*.py`(新)：makemigrations 生成。
- `lottery_backend/usernumber/serializers.py`(改)：fields 加 group_name。
- `lottery_backend/usernumber/views.py`(改)：加 NumberGroupView。
- `lottery_backend/usernumber/urls.py`(改)：加 number/group 路由。
- `lottery_backend/usernumber/tests/test_number_group.py`(新)。
- `lottery_frontend/src/utils/records.js`(新)：formatTime + groupRecords。
- `lottery_frontend/tests/records.test.js`(新)。
- `lottery_frontend/src/api/user.js`(改)：加 setGroup。
- `lottery_frontend/src/pages/mine/index.vue`(改)：按组渲染 + 时间 + 归组。

---

### Task 1: 后端分组字段 + 归组接口

**Files:**
- Modify: `lottery_backend/usernumber/models.py`、`lottery_backend/usernumber/serializers.py`、`lottery_backend/usernumber/views.py`、`lottery_backend/usernumber/urls.py`
- Create: `lottery_backend/usernumber/migrations/`(makemigrations 生成)、`lottery_backend/usernumber/tests/test_number_group.py`

**Interfaces:**
- Consumes: `current_user_id`、`make_response`、`UserNumber`、`UserNumberSerializer`（均已在 views.py 顶部 import）
- Produces: `POST /api/user/number/group` {id, group_name}；`UserNumber.group_name`；序列化含 group_name。

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_number_group.py`:
```python
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery
from usernumber.models import UserNumber


@pytest.fixture
def lottery(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth(db):
    c = APIClient()
    r = c.post("/api/user/login", {"code": "grp-user"}, format="json")
    token = r.json()["data"]["token"]
    c.credentials(HTTP_X_USER_ID=token)
    return c, token


def _create(c):
    r = c.post("/api/user/number/create",
               {"code": "ssq", "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}},
               format="json")
    return r.json()["data"]["id"]


def test_group_sets_name_stripped(auth, lottery):
    c, _ = auth
    rec_id = _create(c)
    r = c.post("/api/user/number/group",
               {"id": rec_id, "group_name": "  周末跟号  "}, format="json")
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["group_name"] == "周末跟号"


def test_group_truncates_50(auth, lottery):
    c, _ = auth
    rec_id = _create(c)
    r = c.post("/api/user/number/group",
               {"id": rec_id, "group_name": "x" * 80}, format="json")
    assert len(r.json()["data"]["group_name"]) == 50


def test_group_clear_with_empty(auth, lottery):
    c, _ = auth
    rec_id = _create(c)
    c.post("/api/user/number/group", {"id": rec_id, "group_name": "g"}, format="json")
    r = c.post("/api/user/number/group", {"id": rec_id, "group_name": ""}, format="json")
    assert r.json()["data"]["group_name"] == ""


def test_group_not_own_record(auth, lottery):
    c, _ = auth
    other = UserNumber.objects.create(
        user_id="someone-else", lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    r = c.post("/api/user/number/group",
               {"id": other.id, "group_name": "g"}, format="json")
    assert r.json()["code"] == 1


def test_group_unauthenticated(db, lottery):
    c = APIClient()
    rec = UserNumber.objects.create(
        user_id="x", lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    r = c.post("/api/user/number/group",
               {"id": rec.id, "group_name": "g"}, format="json")
    assert r.json()["code"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_number_group.py -v`
Expected: FAIL（无 number/group 路由 / group_name 字段不存在）

- [ ] **Step 3: 加 group_name 字段**

`lottery_backend/usernumber/models.py` 在 `target_issue` 行之后、`created_at` 之前加：
```python
    group_name = models.CharField("分组", max_length=50, blank=True, default="")
```

- [ ] **Step 4: 生成迁移**

Run: `python manage.py makemigrations usernumber`
Expected: 生成 `usernumber/migrations/000X_usernumber_group_name.py`（新增字段迁移）

- [ ] **Step 5: 序列化器加 group_name**

`lottery_backend/usernumber/serializers.py` 的 fields 改为：
```python
        fields = ["id", "code", "numbers", "gen_type", "dan_numbers",
                  "note", "target_issue", "group_name", "created_at"]
```

- [ ] **Step 6: 加 NumberGroupView**

`lottery_backend/usernumber/views.py` 末尾追加（与 NumberCheckView 同款 own-record + int(id) 模式）：
```python
class NumberGroupView(APIView):
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        raw_id = request.data.get("id")
        try:
            rec_id = int(raw_id)
        except (TypeError, ValueError):
            return Response(make_response(code=1, msg="参数非法", error=f"id={raw_id}"))
        rec = UserNumber.objects.filter(id=rec_id, user_id=uid).first()
        if rec is None:
            return Response(make_response(code=1, msg="记录不存在"))
        group_name = str(request.data.get("group_name") or "").strip()[:50]
        rec.group_name = group_name
        rec.save(update_fields=["group_name"])
        return Response(make_response(data=UserNumberSerializer(rec).data))
```

- [ ] **Step 7: 加路由**

`lottery_backend/usernumber/urls.py` 在 `number/<int:pk>` 之前加：
```python
    path("number/group", views.NumberGroupView.as_view(), name="user-number-group"),
```

- [ ] **Step 8: 跑测试确认通过 + 全量回归**

Run: `python -m pytest usernumber/tests/test_number_group.py -v`
Expected: PASS（5 passed）
Run: `python -m pytest -q`
Expected: PASS（之前 126 + 本任务新增，全绿）

- [ ] **Step 9: 提交**

```bash
git add lottery_backend/usernumber/models.py lottery_backend/usernumber/migrations/ lottery_backend/usernumber/serializers.py lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_number_group.py
git commit -m "feat: UserNumber 分组字段 + 归组接口"
```

---

### Task 2: 前端纯函数 formatTime + groupRecords

**Files:**
- Create: `lottery_frontend/src/utils/records.js`、`lottery_frontend/tests/records.test.js`

**Interfaces:**
- Produces: `formatTime(iso) -> string`、`groupRecords(items) -> [{name, records}]`。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/records.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { formatTime, groupRecords } from '../src/utils/records.js'

describe('formatTime', () => {
  it('格式化为 YYYY-MM-DD HH:mm', () => {
    const d = new Date(2026, 5, 23, 10, 5) // 本地 2026-06-23 10:05
    expect(formatTime(d.toISOString())).toBe('2026-06-23 10:05')
  })

  it('空/非法返回空串', () => {
    expect(formatTime('')).toBe('')
    expect(formatTime(null)).toBe('')
    expect(formatTime('not-a-date')).toBe('')
  })
})

describe('groupRecords', () => {
  const items = [
    { id: 1, group_name: 'B组' },
    { id: 2, group_name: '' },
    { id: 3, group_name: 'A组' },
    { id: 4, group_name: 'A组' },
    { id: 5 },
  ]

  it('按组分块，命名组升序在前，未分组殿后', () => {
    const g = groupRecords(items)
    expect(g.map((x) => x.name)).toEqual(['A组', 'B组', '未分组'])
    expect(g[0].records.map((r) => r.id)).toEqual([3, 4])
    expect(g[2].records.map((r) => r.id)).toEqual([2, 5])
  })

  it('空/非数组返回 []', () => {
    expect(groupRecords([])).toEqual([])
    expect(groupRecords(null)).toEqual([])
  })

  it('不改入参', () => {
    const before = items.map((x) => x.id)
    groupRecords(items)
    expect(items.map((x) => x.id)).toEqual(before)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（找不到 records.js）

- [ ] **Step 3: 写实现**

`lottery_frontend/src/utils/records.js`:
```js
export function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

export function groupRecords(items) {
  if (!Array.isArray(items)) return []
  const map = new Map()
  for (const it of items) {
    const name = ((it.group_name || '') + '').trim() || '未分组'
    if (!map.has(name)) map.set(name, [])
    map.get(name).push(it)
  }
  const named = [...map.keys()]
    .filter((n) => n !== '未分组')
    .sort((a, b) => a.localeCompare(b))
  const result = named.map((name) => ({ name, records: map.get(name) }))
  if (map.has('未分组')) result.push({ name: '未分组', records: map.get('未分组') })
  return result
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS（records 全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/records.js lottery_frontend/tests/records.test.js
git commit -m "feat: 记录时间格式化 formatTime + 分组 groupRecords"
```

---

### Task 3: 我的号码页接入时间 + 分组 + 归组

**Files:**
- Modify: `lottery_frontend/src/api/user.js`、`lottery_frontend/src/pages/mine/index.vue`（index.vue 整体替换）

**Interfaces:**
- Consumes: `formatTime`/`groupRecords`(utils/records)、`setGroup`(api/user)、既有 listNumbers/deleteNumber/checkNumber/ensureLogin、组件 TopBanner/LotteryTabs/Ball
- Produces: 我的号码页按组展示 + 每条选号时间 + 归组操作。

- [ ] **Step 1: api/user.js 加 setGroup**

`lottery_frontend/src/api/user.js` 末尾追加：
```js
export function setGroup(id, group_name) {
  return request('/api/user/number/group', { method: 'POST', data: { id, group_name } })
}
```
（`request` 已在文件顶部 import；与既有 createNumber/deleteNumber 同款。）

- [ ] **Step 2: 整体替换 mine/index.vue**

`lottery_frontend/src/pages/mine/index.vue`:
```vue
<template>
  <view class="page">
    <TopBanner title="我的号码" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar">
      <button class="go" size="mini" @click="goPicker">去选号</button>
    </view>
    <view v-for="grp in groups" :key="grp.name" class="group">
      <view class="group-title">{{ grp.name }}（{{ grp.records.length }}）</view>
      <view v-for="rec in grp.records" :key="rec.id" class="card">
        <view class="top">
          <text class="tag">{{ genLabel(rec.gen_type) }}</text>
          <text v-if="rec.target_issue" class="issue">目标 {{ rec.target_issue }}</text>
        </view>
        <view class="balls">
          <Ball v-for="(n, i) in rec.numbers.red" :key="'r'+i" :value="n" zone="red" />
          <Ball v-for="(n, i) in rec.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
        </view>
        <view v-if="rec.note" class="note">{{ rec.note }}</view>
        <view class="time">{{ formatTime(rec.created_at) }}</view>
        <view class="ops">
          <text class="op" @click="doGroup(rec)">归组</text>
          <text v-if="rec.target_issue" class="op" @click="doCheck(rec.id)">比对</text>
          <text class="op del" @click="doDelete(rec.id)">删除</text>
        </view>
      </view>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup } from '../../api/user.js'
import { reportAccess } from '../../utils/report.js'
import { formatTime, groupRecords } from '../../utils/records.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

const groups = computed(() => groupRecords(items.value))

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
function goPicker() { uni.switchTab({ url: '/pages/mine/picker' }) }

function doGroup(rec) {
  uni.showModal({
    title: '归组',
    editable: true,
    placeholderText: '输入组名(留空取消分组)',
    content: rec.group_name || '',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await setGroup(rec.id, (res.content || '').trim())
        load()
      } catch (e) {
        uni.showToast({ title: e.msg || '归组失败', icon: 'none' })
      }
    },
  })
}

async function doCheck(id) {
  try {
    const r = await checkNumber(id)
    reportAccess('mine/check', { lottery_code: store.code, action: 'check_number' })
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
  reportAccess('mine/index', { lottery_code: lotteryStore.code })
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞列表 */ }
  }
  load()
})
</script>

<style scoped>
.bar { display: flex; justify-content: flex-end; padding: 16rpx 20rpx 0; }
.go { background: #e53935; color: #fff; }
.group-title { padding: 16rpx 24rpx 4rpx; font-size: 28rpx; color: #e53935; font-weight: bold; }
.card { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.top { display: flex; justify-content: space-between; font-size: 28rpx; color: #888; }
.tag { color: #e53935; }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.note { font-size: 28rpx; color: #999; }
.time { font-size: 24rpx; color: #bbb; margin-top: 6rpx; }
.ops { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.op { margin-left: 28rpx; font-size: 30rpx; color: #1e88e5; }
.op.del { color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 3: build + 目测**

后端 8123 在跑（有数据）。前端 `npm run build:h5`（确认通过）→ `npm run dev:h5`。
Expected:
- 我的号码页记录按组分块，组名标题 + 条数；未分组在最下。
- 每条卡片有选号时间（YYYY-MM-DD HH:mm）。
- 点某条"归组"→ 弹输入框 → 输入"周末跟号"确认 → 该条移入"周末跟号"组；再点输入空 → 回未分组。

- [ ] **Step 4: 全量前端测试**

Run: `npm test`
Expected: PASS（records + 既有全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/api/user.js lottery_frontend/src/pages/mine/index.vue
git commit -m "feat: 我的号码页显示选号时间 + 按组展示 + 归组操作"
```

---

## 计划自检

**1. Spec 覆盖：**
- group_name 字段 + 迁移 + 序列化 → Task 1 ✓
- 归组接口(本人/未登录/不存在 code=1, strip+50 截断, 空清除) → Task 1 ✓
- formatTime + groupRecords → Task 2 ✓
- 显示时间 + 按组渲染 + 归组操作 + setGroup → Task 3 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `setGroup(id, group_name)`(Task3 api) → `POST /api/user/number/group {id, group_name}`(Task1 view) 一致。
- `groupRecords(items)->[{name,records}]`、`formatTime(iso)`(Task2) 被 mine/index.vue(Task3) 引用一致。
- 序列化器 group_name(Task1) 被前端 rec.group_name(Task3 doGroup content / groupRecords)消费一致。

**4. 注意点（给执行者）：**
- Task1 url number/group 必须在 number/<int:pk> 之前（虽 <int:pk> 不匹配 "group"，仍按规范前置）。
- NumberGroupView 与既有 number 接口一致 authentication_classes=[]，认证靠 current_user_id。
- uni.showModal editable:true 取 res.content 作组名；res.confirm 才提交。
- groupRecords 命名组 localeCompare 升序；测试用 'A组'/'B组' 首字符即可判定，避免 CJK 排序歧义。
- Task3 目测需后端 8123 + 该用户有若干记录（可先在 picker 存几注）。
