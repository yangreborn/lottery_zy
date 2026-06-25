# 批量删除 + 批量归组 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 「我的号码」页支持多选批量删除与批量归组，后端提供原子批量接口。

**Architecture:** 后端 `usernumber` app 加 `BatchDeleteView`/`BatchGroupView`（`filter(id__in=ids, user_id=uid)` 原子操作，只动当前用户记录）。前端 `mine/index.vue` 加「管理」多选模式（勾选圈 + 底部全选/批量归组/批量删除栏），复用 `utils/picker.js` 的 `toggleIndex`。

**Tech Stack:** Django 5.2 + DRF（pytest + APIClient）；uni-app Vue3（vitest，mock request）。

## Global Constraints

- 后端用 `logging` 标准库，不用 `print`；异常 `logging.error(..., exc_info=True)`。
- API 统一 `make_response`；成功 `code=0` 失败 `code=1`。
- 用户标识 hash：`current_user_id(request)`；批量操作必须带 `user_id=uid` 过滤，只动自己的记录。
- 前端无 Pinia/Vuex；api 走 `request` 封装；复用现有 `toggleIndex`，不新写 toggle。
- 批量删除必须 `showModal` 确认（note 24），并显示选中条数。
- 不删既有测试；单条操作（归组/比对/删除）保持不变。

---

### Task 1: 后端批量接口

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（加两个 View）
- Modify: `lottery_backend/usernumber/urls.py`（加两条路由）
- Test: `lottery_backend/usernumber/tests/test_number_batch.py`

**Interfaces:**
- Produces:
  - `POST /api/user/number/batch_delete` body `{ids: [int]}` → `make_response(data={"deleted": n})`
  - `POST /api/user/number/batch_group` body `{ids: [int], group_name: str}` → `make_response(data={"updated": n})`

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_number_batch.py`：
```python
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery
from usernumber.models import UserNumber
from common.auth import hash_user_id


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


def _make_record(user_openid, lottery, group_name=""):
    return UserNumber.objects.create(
        user_id=hash_user_id(user_openid), lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]}, group_name=group_name,
    )


def test_batch_delete_own_skip_others(ssq, auth_client):
    r1 = _make_record("tester-openid", ssq)
    r2 = _make_record("tester-openid", ssq)
    other = _make_record("other-openid", ssq)
    resp = auth_client.post("/api/user/number/batch_delete",
                            {"ids": [r1.id, r2.id, other.id]}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["deleted"] == 2
    assert not UserNumber.objects.filter(id__in=[r1.id, r2.id]).exists()
    assert UserNumber.objects.filter(id=other.id).exists()


def test_batch_delete_empty_ids(ssq, auth_client):
    resp = auth_client.post("/api/user/number/batch_delete", {"ids": []}, format="json")
    assert resp.json()["code"] == 1


def test_batch_delete_unauthenticated(ssq):
    resp = APIClient().post("/api/user/number/batch_delete", {"ids": [1]}, format="json")
    assert resp.json()["code"] == 1


def test_batch_group_set_skip_others(ssq, auth_client):
    r1 = _make_record("tester-openid", ssq)
    r2 = _make_record("tester-openid", ssq)
    other = _make_record("other-openid", ssq)
    resp = auth_client.post("/api/user/number/batch_group",
                            {"ids": [r1.id, r2.id, other.id], "group_name": "甲组"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["updated"] == 2
    r1.refresh_from_db(); r2.refresh_from_db(); other.refresh_from_db()
    assert r1.group_name == "甲组"
    assert r2.group_name == "甲组"
    assert other.group_name == ""


def test_batch_group_clear(ssq, auth_client):
    r1 = _make_record("tester-openid", ssq, group_name="旧组")
    resp = auth_client.post("/api/user/number/batch_group",
                            {"ids": [r1.id], "group_name": ""}, format="json")
    assert resp.json()["code"] == 0
    r1.refresh_from_db()
    assert r1.group_name == ""
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_number_batch.py -v`
Expected: FAIL（接口 404）

- [ ] **Step 3: 加两个 View**

`lottery_backend/usernumber/views.py` 文件末尾追加：
```python
class BatchDeleteView(APIView):
    """POST /api/user/number/batch_delete —— 批量删除自己的记录。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not ids:
            return Response(make_response(code=1, msg="请选择记录"))
        n, _ = UserNumber.objects.filter(id__in=ids, user_id=uid).delete()
        return Response(make_response(data={"deleted": n}))


class BatchGroupView(APIView):
    """POST /api/user/number/batch_group —— 批量设置/清除分组。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not ids:
            return Response(make_response(code=1, msg="请选择记录"))
        group_name = str(request.data.get("group_name") or "").strip()[:50]
        n = UserNumber.objects.filter(id__in=ids, user_id=uid).update(group_name=group_name)
        return Response(make_response(data={"updated": n}))
```

- [ ] **Step 4: 注册路由**

`lottery_backend/usernumber/urls.py`：在 `number/group` 行之后、`number/<int:pk>` 行之前插入两条：
```python
    path("number/batch_delete", views.BatchDeleteView.as_view(), name="user-number-batch-delete"),
    path("number/batch_group", views.BatchGroupView.as_view(), name="user-number-batch-group"),
```

- [ ] **Step 5: 跑测试确认通过 + 全量回归**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_number_batch.py -v && python -m pytest -q`
Expected: 5 用例 PASS；全量无回归。

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_number_batch.py
git commit -m "feat: 后端批量删除/批量归组接口"
```

---

### Task 2: 前端多选模式

**Files:**
- Modify: `lottery_frontend/src/api/user.js`（加 batchDelete/batchGroup）
- Modify: `lottery_frontend/src/pages/mine/index.vue`（多选模式）
- Test: `lottery_frontend/tests/user.test.js`（加 batchDelete/batchGroup 用例）

**Interfaces:**
- Consumes: `POST /api/user/number/batch_delete`、`/api/user/number/batch_group`（Task 1）；`toggleIndex(set, i)`（utils/picker.js）。
- Produces: `batchDelete(ids)`、`batchGroup(ids, group_name)`。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/user.test.js`：import 行追加 `batchDelete, batchGroup`：
```js
import { login, createNumber, listNumbers, deleteNumber, checkNumber, generateNumbers, submitFeedback, batchDelete, batchGroup } from '../src/api/user.js'
```
在 `describe('user api', ...)` 内追加：
```js
  it('batchDelete', async () => {
    await batchDelete([1, 2])
    expect(request).toHaveBeenCalledWith('/api/user/number/batch_delete', { method: 'POST', data: { ids: [1, 2] } })
  })
  it('batchGroup', async () => {
    await batchGroup([1, 2], 'A')
    expect(request).toHaveBeenCalledWith('/api/user/number/batch_group', { method: 'POST', data: { ids: [1, 2], group_name: 'A' } })
  })
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- user`
Expected: FAIL（batchDelete/batchGroup 未导出）

- [ ] **Step 3: api 加批量函数**

`lottery_frontend/src/api/user.js` 末尾追加：
```js
export function batchDelete(ids) {
  return request('/api/user/number/batch_delete', { method: 'POST', data: { ids } })
}

export function batchGroup(ids, group_name) {
  return request('/api/user/number/batch_group', { method: 'POST', data: { ids, group_name } })
}
```

- [ ] **Step 4: 改 mine/index.vue（整体替换）**

`lottery_frontend/src/pages/mine/index.vue` 整体替换为：
```vue
<template>
  <view class="page" :class="{ 'has-batch': manageMode }">
    <TopBanner title="我的号码" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar">
      <button v-if="items.length" class="manage" size="mini" @click="toggleManage">{{ manageMode ? '完成' : '管理' }}</button>
      <button class="go" size="mini" @click="goPicker">去选号</button>
    </view>
    <view v-for="grp in groups" :key="grp.name" class="group">
      <view class="group-title">{{ grp.name }}（{{ grp.records.length }}）</view>
      <view
        v-for="rec in grp.records" :key="rec.id"
        class="card" :class="{ sel: manageMode && selectedIds.includes(rec.id) }"
        @click="manageMode && toggleSel(rec.id)"
      >
        <view class="top">
          <view class="top-left">
            <text v-if="manageMode" class="chk">{{ selectedIds.includes(rec.id) ? '✓' : '○' }}</text>
            <text class="tag">{{ genLabel(rec.gen_type) }}</text>
          </view>
          <text v-if="rec.target_issue" class="issue">目标 {{ rec.target_issue }}</text>
        </view>
        <view class="balls">
          <template v-for="(nums, key) in rec.numbers">
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
          </template>
        </view>
        <view v-if="rec.note" class="note">{{ rec.note }}</view>
        <view class="time">{{ formatTime(rec.created_at) }}</view>
        <view v-if="!manageMode" class="ops">
          <text class="op" @click="doGroup(rec)">归组</text>
          <text v-if="rec.target_issue" class="op" @click="doCheck(rec.id)">比对</text>
          <text class="op del" @click="doDelete(rec.id)">删除</text>
        </view>
      </view>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
    <view v-if="manageMode" class="batchbar">
      <text class="bb" @click="selectAll">{{ allSelected ? '取消全选' : '全选' }}</text>
      <text class="bb" :class="{ disabled: !selectedIds.length }" @click="doBatchGroup">归组({{ selectedIds.length }})</text>
      <text class="bb del" :class="{ disabled: !selectedIds.length }" @click="doBatchDelete">删除({{ selectedIds.length }})</text>
    </view>
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
import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup, batchDelete, batchGroup } from '../../api/user.js'
import { reportAccess } from '../../utils/report.js'
import { formatTime, groupRecords } from '../../utils/records.js'
import { toggleIndex } from '../../utils/picker.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

const manageMode = ref(false)
const selectedIds = ref([])

const groups = computed(() => groupRecords(items.value))
const allIds = computed(() => items.value.map((r) => r.id))
const allSelected = computed(() => allIds.value.length > 0 && selectedIds.value.length === allIds.value.length)

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

function onChange(code) { exitManage(); setCode(code); load() }
function goPicker() { uni.switchTab({ url: '/pages/mine/picker' }) }

function toggleManage() {
  manageMode.value = !manageMode.value
  selectedIds.value = []
}
function exitManage() { manageMode.value = false; selectedIds.value = [] }
function toggleSel(id) { selectedIds.value = toggleIndex(selectedIds.value, id) }
function selectAll() { selectedIds.value = allSelected.value ? [] : [...allIds.value] }

function doBatchDelete() {
  if (!selectedIds.value.length) return
  const ids = [...selectedIds.value]
  uni.showModal({
    title: '确认删除',
    content: `删除选中的 ${ids.length} 条？删除后不可恢复`,
    success: async (res) => {
      if (!res.confirm) return
      try { await batchDelete(ids); exitManage(); load() }
      catch (e) { uni.showToast({ title: e.msg || '删除失败', icon: 'none' }) }
    },
  })
}

function doBatchGroup() {
  if (!selectedIds.value.length) return
  const ids = [...selectedIds.value]
  uni.showModal({
    title: '批量归组',
    editable: true,
    placeholderText: '输入组名(留空取消分组)',
    success: async (res) => {
      if (!res.confirm) return
      try { await batchGroup(ids, (res.content || '').trim()); exitManage(); load() }
      catch (e) { uni.showToast({ title: e.msg || '归组失败', icon: 'none' }) }
    },
  })
}

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
      content: `${r.desc}，${r.label}`,
      showCancel: false,
    })
  } catch (e) {
    uni.showToast({ title: e.msg || '比对失败', icon: 'none' })
  }
}

function doDelete(id) {
  uni.showModal({
    title: '确认删除',
    content: '删除后不可恢复，确定删除这条号码？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteNumber(id)
        load()
      } catch (e) {
        uni.showToast({ title: e.msg || '删除失败', icon: 'none' })
      }
    },
  })
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
.page.has-batch { padding-bottom: 120rpx; }
.bar { display: flex; justify-content: flex-end; padding: 16rpx 20rpx 0; }
.manage { background: #fff; color: #e53935; border: 1rpx solid #e53935; margin-right: 16rpx; }
.go { background: #e53935; color: #fff; }
.group-title { padding: 16rpx 24rpx 4rpx; font-size: 28rpx; color: #e53935; font-weight: bold; }
.card { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.card.sel { box-shadow: 0 0 0 2rpx #e53935; }
.top { display: flex; justify-content: space-between; font-size: 28rpx; color: #888; }
.top-left { display: flex; align-items: center; }
.chk { font-size: 34rpx; color: #e53935; margin-right: 12rpx; }
.tag { color: #e53935; }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.note { font-size: 28rpx; color: #999; }
.time { font-size: 24rpx; color: #bbb; margin-top: 6rpx; }
.ops { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.op { margin-left: 28rpx; font-size: 30rpx; color: #1e88e5; }
.op.del { color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
.batchbar { position: fixed; left: 0; right: 0; bottom: 0; display: flex; background: #fff; border-top: 1rpx solid #eee; padding: 20rpx 0; }
.bb { flex: 1; text-align: center; font-size: 30rpx; color: #1e88e5; }
.bb.del { color: #e53935; }
.bb.disabled { color: #ccc; }
</style>
```

- [ ] **Step 5: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/api/user.js lottery_frontend/src/pages/mine/index.vue lottery_frontend/tests/user.test.js
git commit -m "feat: 我的号码页批量删除/批量归组多选模式"
```

---

## 计划自检

**1. Spec 覆盖：**
- 后端 batch_delete/batch_group（spec §1）→ Task 1 ✓
- user_id 过滤只动自己的（spec §1/§3）→ Task 1 View filter + 测试 skip_others ✓
- 前端多选模式/管理按钮/勾选/底部栏（spec §2）→ Task 2 Step 4 ✓
- 批量删除确认显示条数（spec §2.4 + note 24）→ Task 2 doBatchDelete showModal ✓
- 单条操作不变（spec §0）→ Task 2 保留 doGroup/doCheck/doDelete + 非 manageMode 显示 ops ✓
- api（spec §2.5）→ Task 2 Step 3 ✓
- 测试（spec §4）→ Task 1 Step 1（5 后端用例）、Task 2 Step 1（api 用例）✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码与确切命令。

**3. 类型/签名一致性：** `batchDelete(ids)`/`batchGroup(ids, group_name)` 在 api、测试、mine 页一致；端点 `/api/user/number/batch_delete`、`/batch_group` 在 url、view、api、测试一致；`toggleIndex(set, i)` 复用既有；`{deleted}`/`{updated}` 返回字段前端未读取（仅 reload）一致。
