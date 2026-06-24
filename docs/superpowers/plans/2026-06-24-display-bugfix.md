# 开奖展示/导航 Bug 修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复金额解析、奖级表（空行/快乐8码/分组/对齐）、历史页彩种选择、返回按钮 7 个展示/导航 bug。

**Architecture:** 纯前端。formatAmount 去逗号；新增 utils/prize.js + components/PrizeGrades.vue 处理奖级（latest/detail 共用）；history.vue 加 LotteryTabs；TopBanner 加可选返回。

**Tech Stack:** uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 纯前端，不动后端/爬虫/已入库数据。不引 Pinia/Vuex；无 console。命令在 `lottery_frontend/`。
- formatAmount：`Number()` 前 `String(raw).replace(/,/g, '')` 去千分位逗号。
- normalizePrizes(grades)：过滤 count 空行；快乐8码 `x{pick}z{hit}`→`选{pick}中{hit}` 并按 pick 降序分组；数字 level→中文`N等奖`，字符串 level 原样。返回 `{grouped, flat}` 或 `{grouped, groups}`。
- PrizeGrades：flat 三列对齐(flex 2/1/2)，快乐8按"选N"组默认折叠点击展开。
- TopBanner back：getCurrentPages().length>1→navigateBack 否则 switchTab 回 /pages/home/index；仅 tabBar 内容页(stats/picker/mine-index)启用。

---

## File Structure

- `lottery_frontend/src/utils/format.js`(改)：formatAmount 去逗号。
- `lottery_frontend/src/utils/prize.js`(新)：normalizePrizes。
- `lottery_frontend/src/components/PrizeGrades.vue`(新)：奖级表。
- `lottery_frontend/src/pages/draw/latest.vue` `detail.vue`(改)：用 PrizeGrades。
- `lottery_frontend/src/pages/draw/history.vue`(改)：加 LotteryTabs。
- `lottery_frontend/src/components/TopBanner.vue`(改)：加 back。
- `lottery_frontend/src/pages/draw/stats.vue` `mine/picker.vue` `mine/index.vue`(改)：TopBanner :back。

---

### Task 1: formatAmount 解析千分位逗号

**Files:**
- Modify: `lottery_frontend/src/utils/format.js`
- Test: `lottery_frontend/tests/format.test.js`（新建或追加）

**Interfaces:**
- Produces: `formatAmount(raw)` 支持带逗号字符串。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/format.test.js`（若已存在则在末尾追加 describe）:
```js
import { describe, it, expect } from 'vitest'
import { formatAmount } from '../src/utils/format.js'

describe('formatAmount 千分位', () => {
  it('带逗号正确解析', () => {
    expect(formatAmount('7,110,906')).toBe('7,110,906')
    expect(formatAmount('757,966,457.83')).toBe('757,966,457.83')
  })
  it('无逗号不变', () => {
    expect(formatAmount('398183968')).toBe('398,183,968')
  })
  it('空/非法返回 —', () => {
    expect(formatAmount('')).toBe('—')
    expect(formatAmount(null)).toBe('—')
    expect(formatAmount('abc')).toBe('—')
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（`formatAmount('7,110,906')` 现返回 '—'）

- [ ] **Step 3: 改 formatAmount**

`lottery_frontend/src/utils/format.js` 的 formatAmount 改为：
```js
export function formatAmount(raw) {
  if (raw === null || raw === undefined || raw === '') return '—'
  const n = Number(String(raw).replace(/,/g, ''))
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString('en-US')
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/format.js lottery_frontend/tests/format.test.js
git commit -m "fix: formatAmount 解析千分位逗号(大乐透/快乐8金额)"
```

---

### Task 2: utils/prize.js normalizePrizes

**Files:**
- Create: `lottery_frontend/src/utils/prize.js`、`lottery_frontend/tests/prize.test.js`

**Interfaces:**
- Produces: `normalizePrizes(grades) -> {grouped:false, flat:[{label,count,amount}]} | {grouped:true, groups:[{pick,label,rows:[{label,count,amount}]}]}`

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/prize.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { normalizePrizes } from '../src/utils/prize.js'

describe('normalizePrizes', () => {
  it('双色球：过滤空行 + 数字 level 转中文', () => {
    const grades = [
      { count: '8', level: 1, amount: '5867768' },
      { count: '2419', level: 3, amount: '3000' },
      { count: '', level: 7, amount: '' },
    ]
    const r = normalizePrizes(grades)
    expect(r.grouped).toBe(false)
    expect(r.flat.length).toBe(2)
    expect(r.flat[0].label).toBe('一等奖')
  })

  it('大乐透：字符串 level 原样保留', () => {
    const r = normalizePrizes([{ count: '8', level: '一等奖', amount: '7,110,906' }])
    expect(r.flat[0].label).toBe('一等奖')
  })

  it('快乐8：x码翻译 + 按 pick 降序分组', () => {
    const grades = [
      { count: '0', level: 'x10z10', amount: '0' },
      { count: '36', level: 'x10z9', amount: '8000' },
      { count: '1', level: 'x9z9', amount: '250000' },
    ]
    const r = normalizePrizes(grades)
    expect(r.grouped).toBe(true)
    expect(r.groups.map((g) => g.pick)).toEqual([10, 9])
    expect(r.groups[0].label).toBe('选10')
    expect(r.groups[0].rows[0].label).toBe('选10中10')
    expect(r.groups[1].rows[0].label).toBe('选9中9')
  })

  it('空数组安全', () => {
    expect(normalizePrizes([])).toEqual({ grouped: false, flat: [] })
    expect(normalizePrizes(null)).toEqual({ grouped: false, flat: [] })
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（无 prize.js）

- [ ] **Step 3: 写 prize.js**

`lottery_frontend/src/utils/prize.js`:
```js
const CN = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
const KENO_RE = /^x(\d+)z(\d+)$/

function isEmpty(g) {
  return g.count === '' || g.count === null || g.count === undefined
}

function flatLabel(g) {
  if (g.level_label) return g.level_label
  if (typeof g.level === 'number') return `${CN[g.level] || g.level}等奖`
  return String(g.level)
}

export function normalizePrizes(grades) {
  const rows = (grades || []).filter((g) => !isEmpty(g))
  const isKeno = rows.some((g) => KENO_RE.test(String(g.level)))
  if (!isKeno) {
    return {
      grouped: false,
      flat: rows.map((g) => ({ label: flatLabel(g), count: g.count, amount: g.amount })),
    }
  }
  const map = new Map()
  for (const g of rows) {
    const m = KENO_RE.exec(String(g.level))
    if (!m) continue
    const pick = Number(m[1])
    if (!map.has(pick)) map.set(pick, [])
    map.get(pick).push({ label: `选${pick}中${m[2]}`, count: g.count, amount: g.amount })
  }
  const groups = [...map.keys()]
    .sort((a, b) => b - a)
    .map((pick) => ({ pick, label: `选${pick}`, rows: map.get(pick) }))
  return { grouped: true, groups }
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/prize.js lottery_frontend/tests/prize.test.js
git commit -m "feat: normalizePrizes 奖级归一(过滤空行/快乐8翻译分组/中文奖级)"
```

---

### Task 3: PrizeGrades 组件 + 接入 latest/detail

**Files:**
- Create: `lottery_frontend/src/components/PrizeGrades.vue`
- Modify: `lottery_frontend/src/pages/draw/latest.vue`、`lottery_frontend/src/pages/draw/detail.vue`

**Interfaces:**
- Consumes: `normalizePrizes`(utils/prize)、`formatAmount`(utils/format)
- Produces: `<PrizeGrades :grades="..." />`

- [ ] **Step 1: 写 PrizeGrades.vue**

`lottery_frontend/src/components/PrizeGrades.vue`:
```vue
<template>
  <view class="grades">
    <view class="grade head-row">
      <text class="c1">奖级</text><text class="c2">注数</text><text class="c3">单注奖金</text>
    </view>
    <template v-if="!data.grouped">
      <view v-for="(g, i) in data.flat" :key="i" class="grade">
        <text class="c1">{{ g.label }}</text>
        <text class="c2">{{ g.count }}</text>
        <text class="c3">{{ formatAmount(g.amount) }}</text>
      </view>
      <view v-if="!data.flat.length" class="none">暂无奖级数据</view>
    </template>
    <template v-else>
      <view v-for="grp in data.groups" :key="grp.pick" class="kgroup">
        <view class="ghead" @click="toggle(grp.pick)">
          <text>{{ grp.label }}（{{ grp.rows.length }}档）</text>
          <text>{{ open.includes(grp.pick) ? '▲' : '▼' }}</text>
        </view>
        <template v-if="open.includes(grp.pick)">
          <view v-for="(g, i) in grp.rows" :key="i" class="grade">
            <text class="c1">{{ g.label }}</text>
            <text class="c2">{{ g.count }}</text>
            <text class="c3">{{ formatAmount(g.amount) }}</text>
          </view>
        </template>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { normalizePrizes } from '../utils/prize.js'
import { formatAmount } from '../utils/format.js'

const props = defineProps({ grades: { type: Array, default: () => [] } })
const data = computed(() => normalizePrizes(props.grades))
const open = ref([])
function toggle(pick) {
  open.value = open.value.includes(pick)
    ? open.value.filter((p) => p !== pick)
    : [...open.value, pick]
}
</script>

<style scoped>
.grades { border-top: 1px solid #f0f0f0; padding-top: 16rpx; }
.grade { display: flex; padding: 10rpx 0; font-size: 30rpx; color: #555; }
.c1 { flex: 2; }
.c2 { flex: 1; text-align: center; }
.c3 { flex: 2; text-align: right; }
.head-row { color: #999; font-weight: 600; }
.kgroup { border-bottom: 1px solid #f5f5f5; }
.ghead { display: flex; justify-content: space-between; padding: 16rpx 0; font-size: 30rpx; color: #e53935; font-weight: 600; }
.none { text-align: center; color: #999; padding: 20rpx 0; font-size: 28rpx; }
</style>
```

- [ ] **Step 2: latest.vue 接入**

`lottery_frontend/src/pages/draw/latest.vue`：
1. 模板里把：
```html
      <view class="grades">
        <view v-for="(g, i) in draw.prize_grades" :key="i" class="grade">
          <text>{{ g.level_label || g.level }}</text>
          <text>{{ g.count }} 注</text>
          <text>{{ formatAmount(g.amount) }} 元</text>
        </view>
      </view>
```
替换为：
```html
      <PrizeGrades :grades="draw.prize_grades" />
```
2. script 加 `import PrizeGrades from '../../components/PrizeGrades.vue'`。
3. style 删除 `.grades` 与 `.grade` 两条（已移入组件；`.pool`/`.head`/`.balls`/`.empty` 等保留）。

- [ ] **Step 3: detail.vue 接入**

`lottery_frontend/src/pages/draw/detail.vue`：
1. 模板里把：
```html
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
```
替换为：
```html
      <PrizeGrades :grades="draw.prize_grades" />
```
2. script 加 `import PrizeGrades from '../../components/PrizeGrades.vue'`。
3. style 删除 `.grades`、`.grade`、`.head-row` 三条（`.pool`/`.head`/`.balls`/`.empty` 保留）。

- [ ] **Step 4: build + 目测 + 测试**

Run: `npm run build:h5`（Build complete）；`npm test`（全绿）
目测(后端 8123)：大乐透/双色球奖级三列对齐、无空 7 等奖、金额有值；快乐8奖级按"选10…选1"折叠，点击展开显示选N中M。

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/components/PrizeGrades.vue lottery_frontend/src/pages/draw/latest.vue lottery_frontend/src/pages/draw/detail.vue
git commit -m "feat: PrizeGrades 奖级表组件(对齐/过滤/快乐8折叠) 接入当期+详情"
```

---

### Task 4: history.vue 加彩种切换

**Files:**
- Modify: `lottery_frontend/src/pages/draw/history.vue`

**Interfaces:**
- Consumes: `LotteryTabs`、`getLotteryList`、`setCode`

- [ ] **Step 1: 改 history.vue**

`lottery_frontend/src/pages/draw/history.vue`：
1. 模板在 `<TopBanner title="历史开奖" />` 之后、`<scroll-view ...>` 之前插入：
```html
    <LotteryTabs :list="lotteries" :active="lotteryStore.code" @change="onChange" />
```
2. script：
- import 加 `import LotteryTabs from '../../components/LotteryTabs.vue'`、并把 `import { lotteryStore } from '../../store/lottery.js'` 改为 `import { lotteryStore, setCode } from '../../store/lottery.js'`、`import { getHistory, getLotteryList } from '../../api/lottery.js'`（在原 getHistory import 上加 getLotteryList）。
- 新增 `const lotteries = ref([])`。
- 新增切换处理：
```js
function onChange(code) {
  setCode(code)
  loadedCode = code
  fetchPage(true)
}
```
- onShow 内拉彩种列表（首次）：在 `onShow(() => {` 后、reportAccess 之前加：
```js
  if (!lotteries.value.length) {
    getLotteryList().then((l) => { lotteries.value = l }).catch(() => {})
  }
```

- [ ] **Step 2: build + 目测 + 测试**

Run: `npm run build:h5`（Build complete）；`npm test`（全绿）
目测：历史页顶部出现彩种切换条，点大乐透/快乐8切换并重新加载该彩种历史。

- [ ] **Step 3: 提交**

```bash
git add lottery_frontend/src/pages/draw/history.vue
git commit -m "fix: 历史开奖页加彩种切换(LotteryTabs)"
```

---

### Task 5: TopBanner 返回按钮 + tabBar 页启用

**Files:**
- Modify: `lottery_frontend/src/components/TopBanner.vue`、`lottery_frontend/src/pages/draw/stats.vue`、`lottery_frontend/src/pages/mine/picker.vue`、`lottery_frontend/src/pages/mine/index.vue`

**Interfaces:**
- Produces: `<TopBanner :back="true" />` 显示返回按钮。

- [ ] **Step 1: 改 TopBanner.vue**

`lottery_frontend/src/components/TopBanner.vue` 整体替换为：
```vue
<template>
  <view class="top-banner">
    <text v-if="back" class="tb-back" @click="goBack">‹ 返回</text>
    <text class="tb-title">{{ title }}</text>
  </view>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  back: { type: Boolean, default: false },
})
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}
</script>

<style scoped>
.top-banner { position: relative; background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: 28rpx 0; text-align: center; }
.tb-back { position: absolute; left: 24rpx; top: 50%; transform: translateY(-50%); color: #fff; font-size: 30rpx; }
.tb-title { color: #fff; font-size: 34rpx; font-weight: 700; letter-spacing: 4rpx; }
</style>
```

- [ ] **Step 2: 三个 tabBar 内容页启用 back**

分别把这三个文件的 `<TopBanner title="..." />` 改为带 `:back="true"`：
- `lottery_frontend/src/pages/draw/stats.vue`：`<TopBanner title="号码统计" />` → `<TopBanner title="号码统计" :back="true" />`
- `lottery_frontend/src/pages/mine/picker.vue`：`<TopBanner title="选号" />` → `<TopBanner title="选号" :back="true" />`
- `lottery_frontend/src/pages/mine/index.vue`：`<TopBanner title="我的号码" />` → `<TopBanner title="我的号码" :back="true" />`

- [ ] **Step 3: build + 目测 + 测试**

Run: `npm run build:h5`（Build complete）；`npm test`（全绿）
目测：号码统计/选号/我的页左上出现"‹ 返回"，点击回首页；从菜单 navigateTo 的当期/历史/详情仍走原生返回。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/components/TopBanner.vue lottery_frontend/src/pages/draw/stats.vue lottery_frontend/src/pages/mine/picker.vue lottery_frontend/src/pages/mine/index.vue
git commit -m "fix: TopBanner 加返回按钮, tabBar 内容页(统计/选号/我的)启用"
```

---

## 计划自检

**1. Spec 覆盖：**
- 金额逗号(1,3) → Task 1 ✓
- 奖级表过滤空行(6)/快乐8翻译分组(4)/对齐(2) → Task 2+3 ✓
- 历史彩种(5) → Task 4 ✓
- 返回按钮(8) → Task 5 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `formatAmount`(Task1) 被 PrizeGrades(Task3) 用；`normalizePrizes`(Task2) 被 PrizeGrades(Task3) 用，返回 {grouped,flat|groups} 与组件渲染一致。
- `LotteryTabs`/`setCode`/`getLotteryList`(Task4) 与 latest.vue 既有用法一致。
- `TopBanner` back prop(Task5) 被 stats/picker/mine 传 :back="true"。

**4. 注意点（给执行者）：**
- normalizePrizes：count='0'(快乐8 0 注)不算空行(只过滤空串/None)；快乐8判定靠 level 匹配 /^x\d+z\d+$/。
- PrizeGrades 折叠 open 默认空数组(全折叠)。
- TopBanner back 用 getCurrentPages 判断：tabBar 页(switchTab 进)length=1→switchTab 首页；navigateTo 页 length>1→navigateBack。
- 目测需后端 8123（已有 ssq/dlt/kl8 数据）。
