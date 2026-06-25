# 首页/导航重排 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 反馈/购买/我的号码收进「我的」hub；通知活动从玩法说明拆出独立页；彩种 Tab 缩写长名 + 不热门彩种下拉收纳。

**Architecture:** 后端 guide 列表加多类型过滤（`type__in`，向后兼容）；前端新增 `utils/lottery.js`（缩写 + Tab 切分）供 `LotteryTabs` 用；`pages/mine/index` 改为 hub、号码列表迁到 `pages/mine/numbers`；新增 `pages/notice/index`，`HOME_MENU` 重排。

**Tech Stack:** Django 5 + DRF（后端）；uni-app Vue3 setup + vitest（前端）。

## Global Constraints

- 后端 guide 模型/表不拆分，仅加过滤能力（note 32「后端可以放一起」）。
- guide 列表 `type` 支持逗号分隔多类型，`type__in` 过滤，单值向后兼容。
- 彩种缩写：`SHORT_NAMES = { dlt: '大乐透' }`；常驻 Tab 白名单 `HOT_CODES = ['ssq','dlt','3d','pl3','kl8']`；溢出彩种进「更多 ▾」下拉，溢出为空时不渲染「更多」。
- 「我的」hub 三入口：我的号码 `/pages/mine/numbers`、购买记录 `/pages/purchase/index`、我要反馈 `/pages/feedback/index`。
- `HOME_MENU` 移除 `mine`/`feedback`/`purchase`，新增 `notice`（通知活动，navigateTo `/pages/notice/index`）。
- 玩法说明页类型：`intro,rule`；通知活动页类型：`activity,notice`。
- 中文回复与注释；后端日志用 logging 不用 print。

---

### Task 1: 后端 guide 列表多类型过滤

**Files:**
- Modify: `lottery_backend/guide/views.py`（`GuideListView.get`）
- Test: `lottery_backend/guide/tests/test_api_guide.py`

**Interfaces:**
- Produces: `GET /api/openapi/guide/list?type=intro,rule` → 仅返回 type ∈ {intro,rule} 的条目；单值 `type=notice` 仍正常。

- [ ] **Step 1: 写失败测试**

在 `lottery_backend/guide/tests/test_api_guide.py` 末尾追加（沿用文件已有的 `client` fixture 与 `PlayGuide`/`Lottery` 导入；若导入缺失则在文件顶部补 `from guide.models import PlayGuide`）：

```python
@pytest.mark.django_db
def test_list_multi_type_filter(client):
    PlayGuide.objects.create(title="玩法A", type="intro", is_active=True)
    PlayGuide.objects.create(title="奖级B", type="rule", is_active=True)
    PlayGuide.objects.create(title="活动C", type="activity", is_active=True)
    PlayGuide.objects.create(title="通知D", type="notice", is_active=True)

    res = client.get("/api/openapi/guide/list", {"type": "intro,rule"})
    titles = {g["title"] for g in res.json()["data"]}
    assert titles == {"玩法A", "奖级B"}

    res2 = client.get("/api/openapi/guide/list", {"type": "activity,notice"})
    titles2 = {g["title"] for g in res2.json()["data"]}
    assert titles2 == {"活动C", "通知D"}

    res3 = client.get("/api/openapi/guide/list", {"type": "notice"})
    titles3 = {g["title"] for g in res3.json()["data"]}
    assert titles3 == {"通知D"}
```

- [ ] **Step 2: 运行确认失败**

Run: `cd lottery_backend && python -m pytest guide/tests/test_api_guide.py::test_list_multi_type_filter -v`
Expected: FAIL（`type=intro,rule` 现整体当单值过滤 → 返回空，断言不等）。

- [ ] **Step 3: 实现多类型过滤**

`guide/views.py` 把单值过滤改为多类型：

```python
        gtype = request.query_params.get("type")
        if gtype:
            types = [t for t in gtype.split(",") if t]
            if types:
                qs = qs.filter(type__in=types)
```

- [ ] **Step 4: 运行确认通过**

Run: `cd lottery_backend && python -m pytest guide/tests/test_api_guide.py -v`
Expected: PASS（新用例 + 原有用例全绿）。

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/guide/views.py lottery_backend/guide/tests/test_api_guide.py
git commit -m "feat(guide): 列表支持逗号分隔多类型过滤(type__in)"
```

---

### Task 2: 前端 utils/lottery.js + LotteryTabs 缩写与下拉

**Files:**
- Create: `lottery_frontend/src/utils/lottery.js`
- Modify: `lottery_frontend/src/components/LotteryTabs.vue`
- Test: `lottery_frontend/tests/lottery.test.js`

**Interfaces:**
- Produces:
  - `shortLotteryName(item)` → string（dlt→大乐透，否则 item.name）。
  - `splitTabs(list, hotCodes?)` → `{ visible, overflow }`。
  - `SHORT_NAMES`、`HOT_CODES` 常量。

- [ ] **Step 1: 写失败测试 `tests/lottery.test.js`**

```js
import { describe, it, expect } from 'vitest'
import { shortLotteryName, splitTabs, HOT_CODES } from '../src/utils/lottery.js'

describe('shortLotteryName', () => {
  it('超级大乐透缩写为大乐透', () => {
    expect(shortLotteryName({ code: 'dlt', name: '超级大乐透' })).toBe('大乐透')
  })
  it('其它彩种返回原名', () => {
    expect(shortLotteryName({ code: 'ssq', name: '双色球' })).toBe('双色球')
  })
  it('空值安全', () => {
    expect(shortLotteryName(null)).toBe('')
  })
})

describe('splitTabs', () => {
  const list = [
    { code: 'ssq', name: '双色球' },
    { code: 'dlt', name: '超级大乐透' },
    { code: 'xyz', name: '新彩种' },
  ]
  it('热门进 visible，非热门进 overflow', () => {
    const { visible, overflow } = splitTabs(list)
    expect(visible.map((x) => x.code)).toEqual(['ssq', 'dlt'])
    expect(overflow.map((x) => x.code)).toEqual(['xyz'])
  })
  it('HOT_CODES 含 5 个常驻热门彩种', () => {
    expect(HOT_CODES).toEqual(['ssq', 'dlt', '3d', 'pl3', 'kl8'])
  })
  it('空列表安全', () => {
    expect(splitTabs(null)).toEqual({ visible: [], overflow: [] })
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd lottery_frontend && npm test -- lottery`
Expected: FAIL（模块不存在）。

- [ ] **Step 3: 创建 `src/utils/lottery.js`**

```js
export const SHORT_NAMES = { dlt: '大乐透' }
export const HOT_CODES = ['ssq', 'dlt', '3d', 'pl3', 'kl8']

export function shortLotteryName(item) {
  return (item && (SHORT_NAMES[item.code] || item.name)) || ''
}

export function splitTabs(list, hotCodes = HOT_CODES) {
  const arr = list || []
  return {
    visible: arr.filter((x) => hotCodes.includes(x.code)),
    overflow: arr.filter((x) => !hotCodes.includes(x.code)),
  }
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd lottery_frontend && npm test -- lottery`
Expected: PASS。

- [ ] **Step 5: 重写 `src/components/LotteryTabs.vue`**

```vue
<template>
  <view class="tabs">
    <view
      v-for="item in visible"
      :key="item.code"
      class="tab"
      :class="{ active: item.code === active }"
      @click="$emit('change', item.code)"
    >
      <text>{{ shortLotteryName(item) }}</text>
    </view>
    <view
      v-if="overflow.length"
      class="tab more"
      :class="{ active: activeInOverflow }"
      @click="open = !open"
    >
      <text>更多 ▾</text>
    </view>
    <view v-if="open && overflow.length" class="dropdown">
      <view
        v-for="item in overflow"
        :key="item.code"
        class="ditem"
        :class="{ active: item.code === active }"
        @click="pick(item.code)"
      >
        <text>{{ shortLotteryName(item) }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { shortLotteryName, splitTabs } from '../utils/lottery.js'

const props = defineProps({
  list: { type: Array, default: () => [] },
  active: { type: String, default: '' },
})
const emit = defineEmits(['change'])

const open = ref(false)
const parts = computed(() => splitTabs(props.list))
const visible = computed(() => parts.value.visible)
const overflow = computed(() => parts.value.overflow)
const activeInOverflow = computed(() => overflow.value.some((x) => x.code === props.active))

function pick(code) {
  open.value = false
  emit('change', code)
}
</script>

<style scoped>
.tabs { display: flex; border-bottom: 1px solid #eee; position: relative; }
.tab { flex: 1; text-align: center; padding: 20rpx 0; color: #666; }
.tab.active { color: #e53935; border-bottom: 4rpx solid #e53935; font-weight: 600; }
.more { flex: 0 0 120rpx; }
.dropdown { position: absolute; right: 0; top: 100%; z-index: 20; background: #fff; box-shadow: 0 6rpx 20rpx rgba(0,0,0,0.12); border-radius: 0 0 12rpx 12rpx; min-width: 180rpx; }
.ditem { padding: 20rpx 28rpx; color: #666; }
.ditem.active { color: #e53935; font-weight: 600; }
</style>
```

- [ ] **Step 6: 全量前端测试确认无回归**

Run: `cd lottery_frontend && npm test`
Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/utils/lottery.js lottery_frontend/tests/lottery.test.js lottery_frontend/src/components/LotteryTabs.vue
git commit -m "feat(tabs): 彩种 Tab 缩写长名 + 不热门彩种更多下拉"
```

---

### Task 3: 「我的」hub + 号码列表迁移

**Files:**
- Create: `lottery_frontend/src/pages/mine/numbers.vue`
- Modify: `lottery_frontend/src/pages/mine/index.vue`（改 hub）
- Modify: `lottery_frontend/src/pages.json`（注册 numbers，标题）

**Interfaces:**
- Consumes: `ensureLogin`/`wechatLogin`（api/user.js）、`authState`/`setToken`（store/auth.js）、`LotteryTabs`。

- [ ] **Step 1: 新建 `src/pages/mine/numbers.vue`（搬运原号码列表，去掉登录条）**

把原 `pages/mine/index.vue` 内容整体迁入，并删除登录条相关：模板去掉 `<view class="authbar">…</view>`；脚本去掉 `wechatLogin` 导入、`auth` 常量、`doWechatLogin`/`doLogout`；`TopBanner` 标题保持「我的号码」`:back="true"`；`reportAccess('mine/index'...)` 改为 `reportAccess('mine/numbers'...)`。完整文件：

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
          <text class="op" @click="doMarkPurchased(rec)">标为已购</text>
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
import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup, batchDelete, batchGroup, purchaseCreate } from '../../api/user.js'
import { reportAccess } from '../../utils/report.js'
import { formatTime, groupRecords, todayStr } from '../../utils/records.js'
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

function doMarkPurchased(rec) {
  uni.showModal({
    title: '标为已购',
    editable: true,
    placeholderText: '输入购买期号',
    success: async (res) => {
      if (!res.confirm) return
      const issue = (res.content || '').trim()
      if (!issue) { uni.showToast({ title: '请填期号', icon: 'none' }); return }
      try {
        await purchaseCreate({ code: store.code, issue, numbers: rec.numbers, bet_count: 1, purchase_date: todayStr() })
        uni.showToast({ title: '已记录购买', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.msg || '记录失败', icon: 'none' })
      }
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
  reportAccess('mine/numbers', { lottery_code: lotteryStore.code })
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

- [ ] **Step 2: 重写 `src/pages/mine/index.vue` 为 hub**

```vue
<template>
  <view class="page">
    <TopBanner title="我的" :back="false" />
    <view class="authbar">
      <text class="astate">{{ auth.isWechat ? '已微信登录' : '匿名使用中' }}</text>
      <text class="abtn" @click="auth.isWechat ? doLogout() : doWechatLogin()">{{ auth.isWechat ? '退出' : '微信登录' }}</text>
    </view>
    <view class="menu">
      <view class="entry" @click="go('/pages/mine/numbers')">
        <text class="ic">⭐</text><text class="tx">我的号码</text><text class="arr">›</text>
      </view>
      <view class="entry" @click="go('/pages/purchase/index')">
        <text class="ic">🛒</text><text class="tx">购买记录</text><text class="arr">›</text>
      </view>
      <view class="entry" @click="go('/pages/feedback/index')">
        <text class="ic">💬</text><text class="tx">我要反馈</text><text class="arr">›</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { ensureLogin, wechatLogin } from '../../api/user.js'
import { authState, setToken } from '../../store/auth.js'
import { reportAccess } from '../../utils/report.js'

const auth = authState
function go(url) { uni.navigateTo({ url }) }

function doWechatLogin() {
  uni.login({
    success: async (r) => {
      if (!r.code) { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }); return }
      try {
        const res = await wechatLogin(r.code)
        setToken(res.token, true)
        uni.showToast({ title: '登录成功', icon: 'success' })
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
}

onShow(() => {
  reportAccess('mine/index', {})
  ensureLogin()
})
</script>

<style scoped>
.authbar { display: flex; justify-content: space-between; align-items: center; padding: 24rpx; }
.astate { font-size: 28rpx; color: #888; }
.abtn { font-size: 28rpx; color: #e53935; }
.menu { margin: 12rpx 20rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.entry { display: flex; align-items: center; padding: 32rpx 28rpx; border-bottom: 1rpx solid #f3f3f3; }
.entry:last-child { border-bottom: none; }
.ic { font-size: 40rpx; margin-right: 20rpx; }
.tx { flex: 1; font-size: 32rpx; color: #333; }
.arr { color: #ccc; font-size: 36rpx; }
</style>
```

- [ ] **Step 3: `pages.json` 注册 numbers 页、改我的标题**

把第 10 行 `pages/mine/index` 标题改为「我的」，并在其后新增 numbers 页：

```json
    { "path": "pages/mine/index", "style": { "navigationBarTitleText": "我的" } },
    { "path": "pages/mine/numbers", "style": { "navigationBarTitleText": "我的号码" } },
```

- [ ] **Step 4: 全量前端测试确认无回归**

Run: `cd lottery_frontend && npm test`
Expected: PASS（无组件级单测，逻辑搬运不影响 util/api 测试）。

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/pages/mine/numbers.vue lottery_frontend/src/pages/mine/index.vue lottery_frontend/src/pages.json
git commit -m "feat(mine): 我的改为 hub(号码/购买/反馈)，号码列表迁到 mine/numbers"
```

---

### Task 4: 通知活动独立 + 首页菜单重排

**Files:**
- Create: `lottery_frontend/src/pages/notice/index.vue`
- Modify: `lottery_frontend/src/utils/menu.js`
- Modify: `lottery_frontend/src/pages/guide/index.vue`（类型收窄为玩法相关）
- Modify: `lottery_frontend/src/pages/home/index.vue`（goNotices 指向通知页）
- Modify: `lottery_frontend/src/pages.json`（注册 notice，guide 标题）
- Test: `lottery_frontend/tests/menu.test.js`（更新）

**Interfaces:**
- Consumes: `getGuideList(code, type)`（api/guide.js，type 支持逗号多值）、`LotteryTabs`、`getLotteryList`。

- [ ] **Step 1: 更新失败测试 `tests/menu.test.js`**

```js
import { describe, it, expect, beforeEach } from 'vitest'
import { HOME_MENU, goMenu } from '../src/utils/menu.js'

describe('HOME_MENU', () => {
  it('7 项且字段完整', () => {
    expect(HOME_MENU.length).toBe(7)
    for (const m of HOME_MENU) {
      expect(typeof m.key).toBe('string')
      expect(typeof m.title).toBe('string')
      expect(typeof m.icon).toBe('string')
      expect(m.path.startsWith('/pages/')).toBe(true)
      expect(['switchTab', 'navigateTo']).toContain(m.nav)
    }
  })

  it('已移除 mine/feedback/purchase，新增 notice', () => {
    const keys = HOME_MENU.map((m) => m.key)
    expect(keys).not.toContain('mine')
    expect(keys).not.toContain('feedback')
    expect(keys).not.toContain('purchase')
    expect(keys).toContain('notice')
  })

  it('导航类型与文案正确', () => {
    const byKey = Object.fromEntries(HOME_MENU.map((m) => [m.key, m]))
    expect(byKey.stats.nav).toBe('switchTab')
    expect(byKey.picker.nav).toBe('switchTab')
    expect(byKey.latest.nav).toBe('navigateTo')
    expect(byKey.history.nav).toBe('navigateTo')
    expect(byKey.guide.nav).toBe('navigateTo')
    expect(byKey.guide.title).toBe('玩法说明')
    expect(byKey.notice.nav).toBe('navigateTo')
    expect(byKey.notice.path).toBe('/pages/notice/index')
    expect(byKey.poster.nav).toBe('navigateTo')
  })
})

describe('goMenu', () => {
  let calls
  beforeEach(() => {
    calls = []
    globalThis.uni = {
      switchTab: (o) => calls.push(['switchTab', o.url]),
      navigateTo: (o) => calls.push(['navigateTo', o.url]),
    }
  })

  it('switchTab 项', () => {
    goMenu({ nav: 'switchTab', path: '/pages/draw/stats' })
    expect(calls).toEqual([['switchTab', '/pages/draw/stats']])
  })

  it('navigateTo 项', () => {
    goMenu({ nav: 'navigateTo', path: '/pages/draw/latest' })
    expect(calls).toEqual([['navigateTo', '/pages/draw/latest']])
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd lottery_frontend && npm test -- menu`
Expected: FAIL（HOME_MENU 现 9 项含 mine/feedback/purchase、无 notice）。

- [ ] **Step 3: 重写 `src/utils/menu.js` 的 HOME_MENU**

```js
export const HOME_MENU = [
  { key: 'latest', title: '当期中奖', icon: '🎯', path: '/pages/draw/latest', nav: 'navigateTo' },
  { key: 'history', title: '往期开奖', icon: '📅', path: '/pages/draw/history', nav: 'navigateTo' },
  { key: 'stats', title: '号码统计', icon: '📊', path: '/pages/draw/stats', nav: 'switchTab' },
  { key: 'picker', title: '选号', icon: '✏️', path: '/pages/mine/picker', nav: 'switchTab' },
  { key: 'guide', title: '玩法说明', icon: '📖', path: '/pages/guide/index', nav: 'navigateTo' },
  { key: 'notice', title: '通知活动', icon: '📢', path: '/pages/notice/index', nav: 'navigateTo' },
  { key: 'poster', title: '开奖海报', icon: '🖼️', path: '/pages/poster/index', nav: 'navigateTo' },
]

export function goMenu(item) {
  if (item.nav === 'switchTab') {
    uni.switchTab({ url: item.path })
  } else {
    uni.navigateTo({ url: item.path })
  }
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd lottery_frontend && npm test -- menu`
Expected: PASS。

- [ ] **Step 5: 新建 `src/pages/notice/index.vue`（通知活动）**

```vue
<template>
  <view class="page">
    <TopBanner title="通知活动" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="types">
      <view
        v-for="t in types" :key="t.key"
        class="type" :class="{ active: t.key === curType }"
        @click="chooseType(t.key)"
      >
        <text>{{ t.label }}</text>
      </view>
    </view>
    <view v-for="g in items" :key="g.id" class="row" @click="goDetail(g.id)">
      <text class="title">{{ g.title }}</text>
      <text class="tag">{{ g.type_label }}</text>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { getGuideList } from '../../api/guide.js'
import { reportAccess } from '../../utils/report.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')
const types = [
  { key: 'activity,notice', label: '全部' },
  { key: 'activity', label: '活动' },
  { key: 'notice', label: '通知' },
]
const curType = ref('activity,notice')

async function load() {
  emptyMsg.value = '加载中…'
  try {
    items.value = await getGuideList(store.code, curType.value)
    if (!items.value.length) emptyMsg.value = '暂无内容'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) { setCode(code); load() }
function chooseType(k) { curType.value = k; load() }
function goDetail(id) { uni.navigateTo({ url: `/pages/guide/detail?id=${id}` }) }

onShow(async () => {
  reportAccess('notice/index', { lottery_code: lotteryStore.code })
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞列表 */ }
  }
  load()
})
</script>

<style scoped>
.types { display: flex; padding: 16rpx 20rpx; }
.type { padding: 10rpx 24rpx; margin-right: 14rpx; background: #fff; border-radius: 30rpx; color: #666; font-size: 30rpx; }
.type.active { background: #e53935; color: #fff; }
.row { background: #fff; margin: 12rpx 20rpx; padding: 24rpx; border-radius: 12rpx; display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 34rpx; color: #333; }
.tag { font-size: 22rpx; color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 6: `src/pages/guide/index.vue` 类型收窄为玩法相关**

把 `types` 与默认 `curType` 改为：

```js
const types = [
  { key: 'intro,rule', label: '全部' },
  { key: 'intro', label: '玩法说明' },
  { key: 'rule', label: '奖级规则' },
]
const curType = ref('intro,rule')
```

（其余逻辑不动；活动/通知不再出现在本页。）

- [ ] **Step 7: `src/pages/home/index.vue` goNotices 指向通知页**

```js
function goNotices() { uni.navigateTo({ url: '/pages/notice/index' }) }
```

- [ ] **Step 8: `pages.json` 注册 notice 页、guide 标题改名**

把第 8 行 `pages/guide/index` 标题「玩法介绍」改「玩法说明」，并新增 notice 页：

```json
    { "path": "pages/guide/index", "style": { "navigationBarTitleText": "玩法说明" } },
    { "path": "pages/notice/index", "style": { "navigationBarTitleText": "通知活动" } },
```

- [ ] **Step 9: 全量前端测试确认通过**

Run: `cd lottery_frontend && npm test`
Expected: PASS。

- [ ] **Step 10: 提交**

```bash
git add lottery_frontend/src/pages/notice/index.vue lottery_frontend/src/utils/menu.js lottery_frontend/src/pages/guide/index.vue lottery_frontend/src/pages/home/index.vue lottery_frontend/src/pages.json lottery_frontend/tests/menu.test.js
git commit -m "feat(notice): 通知活动独立成页，玩法说明只留玩法/奖级，首页菜单重排"
```

---

## Self-Review

**Spec coverage:**
- note 28（反馈/购买/我的号码进我的）→ Task 3 hub + numbers 迁移 + Task 4 HOME_MENU 移除三项 ✓
- note 32（通知活动独立、后端共表）→ Task 1 多类型过滤 + Task 4 notice 页/guide 收窄/menu ✓
- note 30（缩写 + 下拉）→ Task 2 lottery.js + LotteryTabs ✓

**Placeholder scan:** 无 TBD/TODO；每个代码步骤含完整代码。

**Type consistency:** `shortLotteryName(item)`/`splitTabs(list,hotCodes)` 在 Task 2 定义、LotteryTabs 消费一致；`getGuideList(code, type)` type 多值由 Task 1 后端支持、Task 4 前端 `intro,rule`/`activity,notice` 消费；HOME_MENU `notice.path='/pages/notice/index'` 与 Task 4 新页、pages.json 注册一致；hub 三入口路径与 pages.json/已存在页一致（`/pages/mine/numbers` 新建、`/pages/purchase/index`、`/pages/feedback/index` 已存在）。

**注意：** Task 3 与 Task 4 都改 `pages.json`，按顺序执行避免冲突（Task 3 加 numbers 行，Task 4 加 notice 行、改 guide 标题）。
