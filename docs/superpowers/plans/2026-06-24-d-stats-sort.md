# D · 统计页排序筛选 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统计页加排序切换（号码顺序/出现最多/出现最少），本地重排红蓝热力图。

**Architecture:** 纯前端。新增纯函数 sortCells(cells,mode) 排序；stats.vue 加排序切换行 + sortMode，用 computed 把红/蓝 cells 排好再传 Heatmap（本地重排不重新请求）。不动后端、不动 Heatmap。

**Tech Stack:** uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 纯前端，不动后端（getStats 已返回每号码 count）；不动 Heatmap 组件。
- `sortCells(cells, mode)`：mode='number'(号码升序)/'most'(count 降序，平手号码升序)/'least'(count 升序，平手号码升序)；不可变(返回新数组)；非数组/空返回 []。
- 排序切换是本地重排，**不重新请求**；期数切换仍 load。
- 排序行复用现有 .periods/.opt chip 样式（选中红底 #e53935）。
- 前端 Vue3 JS 不引 Pinia/Vuex；无 console；命令在 `lottery_frontend/`。

---

## File Structure

- `lottery_frontend/src/utils/statsort.js`(新)：sortCells。
- `lottery_frontend/tests/statsort.test.js`(新)。
- `lottery_frontend/src/pages/draw/stats.vue`(改)：排序切换行 + sortMode + computed 排序。

---

### Task 1: 纯函数 sortCells

**Files:**
- Create: `lottery_frontend/src/utils/statsort.js`
- Test: `lottery_frontend/tests/statsort.test.js`

**Interfaces:**
- Produces: `sortCells(cells, mode) -> Array`，mode 三态，不可变。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/statsort.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { sortCells } from '../src/utils/statsort.js'

const CELLS = [
  { number: 3, count: 5, miss: 0 },
  { number: 1, count: 8, miss: 1 },
  { number: 2, count: 5, miss: 2 },
  { number: 5, count: 2, miss: 3 },
]

describe('sortCells', () => {
  it('number 按号码升序', () => {
    expect(sortCells(CELLS, 'number').map((c) => c.number)).toEqual([1, 2, 3, 5])
  })

  it('most 按 count 降序，平手按号码升序', () => {
    // count: 1->8, 2->5, 3->5, 5->2 ; 平手 2、3 按号码升序
    expect(sortCells(CELLS, 'most').map((c) => c.number)).toEqual([1, 2, 3, 5])
  })

  it('least 按 count 升序，平手按号码升序', () => {
    expect(sortCells(CELLS, 'least').map((c) => c.number)).toEqual([5, 2, 3, 1])
  })

  it('不可变(不改入参)', () => {
    const before = CELLS.map((c) => c.number)
    sortCells(CELLS, 'most')
    expect(CELLS.map((c) => c.number)).toEqual(before)
  })

  it('空/非数组返回 []', () => {
    expect(sortCells([], 'most')).toEqual([])
    expect(sortCells(null, 'most')).toEqual([])
    expect(sortCells(undefined, 'number')).toEqual([])
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（找不到 statsort.js）

- [ ] **Step 3: 写实现**

`lottery_frontend/src/utils/statsort.js`:
```js
export function sortCells(cells, mode) {
  if (!Array.isArray(cells)) return []
  const arr = [...cells]
  if (mode === 'most') {
    arr.sort((a, b) => b.count - a.count || a.number - b.number)
  } else if (mode === 'least') {
    arr.sort((a, b) => a.count - b.count || a.number - b.number)
  } else {
    arr.sort((a, b) => a.number - b.number)
  }
  return arr
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS（statsort 全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/statsort.js lottery_frontend/tests/statsort.test.js
git commit -m "feat: 统计号码排序纯函数 sortCells(号码/最多/最少)"
```

---

### Task 2: 统计页接入排序切换

**Files:**
- Modify: `lottery_frontend/src/pages/draw/stats.vue`（整体替换）

**Interfaces:**
- Consumes: `sortCells`(utils/statsort)、`getStats`、`lotteryStore`、`Heatmap`、`TopBanner`、`reportAccess`
- Produces: 统计页排序切换行（号码顺序/出现最多/出现最少），本地重排红蓝热力图。

- [ ] **Step 1: 整体替换 stats.vue**

`lottery_frontend/src/pages/draw/stats.vue`:
```vue
<template>
  <view class="page">
    <TopBanner title="号码统计" />
    <view class="periods">
      <view
        v-for="p in periodOptions" :key="p"
        class="opt" :class="{ active: p === periods }" @click="choose(p)"
      >
        <text>近{{ p }}期</text>
      </view>
    </view>
    <view class="periods">
      <view
        v-for="s in sortOptions" :key="s.key"
        class="opt" :class="{ active: s.key === sortMode }" @click="sortMode = s.key"
      >
        <text>{{ s.label }}</text>
      </view>
    </view>
    <view class="zone-title">红球</view>
    <Heatmap :cells="redSorted" />
    <view class="zone-title">蓝球</view>
    <Heatmap :cells="blueSorted" />
    <view v-if="!redCells.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import Heatmap from '../../components/Heatmap.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getStats } from '../../api/lottery.js'
import { reportAccess } from '../../utils/report.js'
import { sortCells } from '../../utils/statsort.js'

const periodOptions = [10, 30, 50, 100]
const periods = ref(30)
const sortOptions = [
  { key: 'number', label: '号码顺序' },
  { key: 'most', label: '出现最多' },
  { key: 'least', label: '出现最少' },
]
const sortMode = ref('number')
const redCells = ref([])
const blueCells = ref([])
const emptyMsg = ref('加载中…')

const redSorted = computed(() => sortCells(redCells.value, sortMode.value))
const blueSorted = computed(() => sortCells(blueCells.value, sortMode.value))

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

onShow(() => {
  reportAccess('draw/stats', { lottery_code: lotteryStore.code })
  load()
})
</script>

<style scoped>
.periods { display: flex; flex-wrap: wrap; padding: 12rpx 20rpx; }
.opt { padding: 12rpx 24rpx; margin: 6rpx 16rpx 6rpx 0; background: #fff; border-radius: 30rpx; color: #666; font-size: 30rpx; }
.opt.active { background: #e53935; color: #fff; }
.zone-title { padding: 16rpx 24rpx 0; color: #888; font-size: 30rpx; }
.empty { text-align: center; color: #999; padding: 60rpx 0; }
</style>
```

- [ ] **Step 2: build + 目测**

后端在 8123 跑（已有一年数据）。前端 `npm run build:h5`（确认通过）→ `npm run dev:h5`。
Expected:
- 统计页期数行下多一行排序：号码顺序/出现最多/出现最少。
- 选"出现最多"：红球按出现次数降序（最热排前）；"最少"升序；"号码顺序"回到 01..33 顺序。
- 切排序**不**重新请求（仅本地重排）；切期数仍请求。

- [ ] **Step 3: 全量前端测试**

Run: `npm test`
Expected: PASS（statsort + 既有全绿）

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/draw/stats.vue
git commit -m "feat: 统计页加最多/最少排序切换"
```

---

## 计划自检

**1. Spec 覆盖：**
- sortCells 三 mode + 不可变 + 空守卫 → Task 1 ✓
- 统计页排序切换行 + 本地重排 + 不重新请求 → Task 2 ✓
- 后端不动、Heatmap 不动 → 范围内 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `sortCells(cells, mode)`(Task1) 被 stats.vue 的 computed(Task2) 引用一致。
- redCells/blueCells 为 `[{number,count,miss}]`（getStats 返回结构），sortCells 按 number/count 排序与之匹配。
- 排序行复用 .periods/.opt 样式（Task2 样式含 flex-wrap 容两行）。

**4. 注意点（给执行者）：**
- 排序切换只改 sortMode（computed 自动重排），**不要**在切换里调 load/getStats。
- Heatmap 内部按 cells 最大 count 配色，排序不影响 max，无需改 Heatmap。
- 期数行与排序行共用 .periods（已加 flex-wrap）；两行 chip 样式一致。
- 目测需后端 8123 + 一年数据（已就绪）；切"最多"红球应按次数降序明显重排。
