# 开奖海报 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 开奖海报页 —— 选彩种+选期+选配色主题，canvas 绘制开奖海报并保存到相册。

**Architecture:** `utils/poster.js` 放可测纯逻辑（POSTER_THEMES + buildPosterData）和 canvas 绘制（drawPoster）；`pages/poster/index.vue` 选期/选主题/调 drawPoster/保存。复用现有 getHistory/getDetail，无后端改动。

**Tech Stack:** uni-app Vue3 canvas（uni.createCanvasContext）；vitest。

## Global Constraints

- 纯前端，无后端改动；复用 getHistory/getDetail。
- 号码球填色用 `utils/format.js` 的 `ballColor(zone)`（red/blue/main/digits 各色）。
- source：福彩→中国福彩网、体彩→中国体彩网（默认福彩）。
- 海报不含购彩诱导（免费定位）。
- 前端无 Pinia/Vuex；不删既有测试。

---

### Task 1: poster.js 纯逻辑 + 入口

**Files:**
- Create: `lottery_frontend/src/utils/poster.js`（POSTER_THEMES + buildPosterData）
- Modify: `lottery_frontend/src/utils/menu.js`（加 poster 入口）
- Test: `lottery_frontend/tests/poster.test.js`、`lottery_frontend/tests/menu.test.js`

**Interfaces:**
- Produces: `POSTER_THEMES`（3 主题）、`buildPosterData(detail, lotteryName, category)` → `{name, issue, date, zones, source}`。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/poster.test.js`：
```js
import { describe, it, expect } from 'vitest'
import { POSTER_THEMES, buildPosterData } from '../src/utils/poster.js'

describe('POSTER_THEMES', () => {
  it('3 个主题，字段完整', () => {
    expect(POSTER_THEMES.length).toBe(3)
    for (const t of POSTER_THEMES) {
      expect(t.key).toBeTruthy()
      expect(t.label).toBeTruthy()
      expect(t.bg).toBeTruthy()
      expect(t.titleColor).toBeTruthy()
      expect(t.subColor).toBeTruthy()
    }
  })
})

describe('buildPosterData', () => {
  const detail = { issue: '2026073', draw_date: '2026-06-20', numbers: { red: [1, 2], blue: [7] } }
  it('整理 name/issue/date/zones', () => {
    const d = buildPosterData(detail, '双色球', '福彩')
    expect(d.name).toBe('双色球')
    expect(d.issue).toBe('2026073')
    expect(d.date).toBe('2026-06-20')
    expect(d.zones).toEqual([{ key: 'red', nums: [1, 2] }, { key: 'blue', nums: [7] }])
  })
  it('福彩 source 中国福彩网', () => {
    expect(buildPosterData(detail, '双色球', '福彩').source).toContain('中国福彩网')
  })
  it('体彩 source 中国体彩网', () => {
    expect(buildPosterData(detail, '大乐透', '体彩').source).toContain('中国体彩网')
  })
})
```

`lottery_frontend/tests/menu.test.js`：把 `expect(HOME_MENU.length).toBe(8)` 改为 `toBe(9)`；nav 断言处加 `expect(byKey.poster.nav).toBe('navigateTo')`。

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- poster menu`
Expected: FAIL（poster.js 不存在 / poster 项不存在）

- [ ] **Step 3: 写 poster.js**

`lottery_frontend/src/utils/poster.js`：
```js
export const POSTER_THEMES = [
  { key: 'red', label: '红色喜庆', bg: '#e53935', titleColor: '#ffffff', subColor: '#ffd9d4' },
  { key: 'gold', label: '金色尊贵', bg: '#2e2a1f', titleColor: '#f5c518', subColor: '#c8a85a' },
  { key: 'blue', label: '蓝色简约', bg: '#1e88e5', titleColor: '#ffffff', subColor: '#cfe3ff' },
]

export function buildPosterData(detail, lotteryName, category) {
  return {
    name: lotteryName,
    issue: detail.issue,
    date: detail.draw_date,
    zones: Object.entries(detail.numbers || {}).map(([key, nums]) => ({ key, nums })),
    source: category === '体彩' ? '数据来源：中国体彩网 sporttery.cn' : '数据来源：中国福彩网 cwl.gov.cn',
  }
}
```

- [ ] **Step 4: menu 加入口**

`lottery_frontend/src/utils/menu.js`：在 `purchase` 行之后、数组 `]` 之前加：
```js
  { key: 'poster', title: '开奖海报', icon: '🖼️', path: '/pages/poster/index', nav: 'navigateTo' },
```

- [ ] **Step 5: 跑测试确认通过**

Run: `cd lottery_frontend && npm test`
Expected: 全绿（poster 4 用例 + menu 更新）。

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/utils/poster.js lottery_frontend/src/utils/menu.js lottery_frontend/tests/poster.test.js lottery_frontend/tests/menu.test.js
git commit -m "feat: 海报主题与数据整理poster.js+首页入口"
```

---

### Task 2: 海报页 canvas 绘制 + 保存

**Files:**
- Modify: `lottery_frontend/src/utils/poster.js`（加 drawPoster）
- Create: `lottery_frontend/src/pages/poster/index.vue`
- Modify: `lottery_frontend/src/pages.json`（注册 poster/index）

**Interfaces:**
- Consumes: `POSTER_THEMES`/`buildPosterData`（Task 1）、`ballColor`（format.js）、`getHistory`/`getDetail`（api/lottery.js）。
- Produces: `drawPoster(ctx, data, theme)`（canvas 绘制）。

- [ ] **Step 1: poster.js 加 drawPoster**

`lottery_frontend/src/utils/poster.js` 顶部加 `import { ballColor } from './format.js'`，末尾追加：
```js
export function drawPoster(ctx, data, theme) {
  const W = 600, H = 840
  ctx.setFillStyle(theme.bg)
  ctx.fillRect(0, 0, W, H)

  ctx.setTextAlign('center')
  ctx.setFillStyle(theme.titleColor)
  ctx.setFontSize(48)
  ctx.fillText(data.name, W / 2, 130)

  ctx.setFillStyle(theme.subColor)
  ctx.setFontSize(28)
  ctx.fillText(`第 ${data.issue} 期 · ${data.date}`, W / 2, 190)

  let y = 340
  const r = 38
  for (const zone of data.zones) {
    const nums = zone.nums || []
    const gap = 92
    let x = (W - nums.length * gap) / 2 + gap / 2
    for (const num of nums) {
      ctx.beginPath()
      ctx.arc(x, y, r, 0, 2 * Math.PI)
      ctx.setFillStyle(ballColor(zone.key))
      ctx.fill()
      ctx.setFillStyle('#ffffff')
      ctx.setFontSize(34)
      const pad = zone.key === 'digits' ? 1 : 2
      ctx.fillText(String(num).padStart(pad, '0'), x, y + 12)
      x += gap
    }
    y += 116
  }

  ctx.setFillStyle(theme.subColor)
  ctx.setFontSize(22)
  ctx.fillText(data.source, W / 2, H - 60)
  ctx.draw()
}
```

- [ ] **Step 2: 海报页**

`lottery_frontend/src/pages/poster/index.vue`：
```vue
<template>
  <view class="page">
    <TopBanner title="开奖海报" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <scroll-view scroll-x class="issues">
      <view
        v-for="it in issues" :key="it.issue"
        class="ichip" :class="{ active: it.issue === curIssue }"
        @click="chooseIssue(it)"
      ><text>{{ it.issue }}期</text></view>
    </scroll-view>
    <view class="themes">
      <view
        v-for="t in themes" :key="t.key"
        class="tchip" :class="{ active: t.key === themeKey }"
        @click="chooseTheme(t.key)"
      ><text>{{ t.label }}</text></view>
    </view>
    <view class="cvwrap">
      <canvas canvas-id="poster" class="poster"></canvas>
    </view>
    <view v-if="!curIssue" class="hint">请先选择期次</view>
    <view class="actions">
      <button class="btn" :disabled="!curIssue" @click="save">保存到相册</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getHistory, getDetail } from '../../api/lottery.js'
import { POSTER_THEMES, buildPosterData, drawPoster } from '../../utils/poster.js'

const store = lotteryStore
const lotteries = ref([])
const issues = ref([])
const curIssue = ref('')
const themes = POSTER_THEMES
const themeKey = ref('red')
let posterData = null

function curTheme() { return themes.find((t) => t.key === themeKey.value) || themes[0] }
function curCategory() {
  const l = lotteries.value.find((x) => x.code === store.code)
  return l ? l.category : '福彩'
}
function curName() {
  const l = lotteries.value.find((x) => x.code === store.code)
  return l ? l.name : store.code
}

async function loadIssues() {
  curIssue.value = ''
  posterData = null
  try {
    const res = await getHistory(store.code, { page: 1 })
    issues.value = res.results || []
  } catch (e) {
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

async function chooseIssue(it) {
  try {
    const detail = await getDetail(store.code, it.issue)
    posterData = buildPosterData(detail, curName(), curCategory())
    curIssue.value = it.issue
    redraw()
  } catch (e) {
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function chooseTheme(k) { themeKey.value = k; redraw() }

function redraw() {
  if (!posterData) return
  const ctx = uni.createCanvasContext('poster')
  drawPoster(ctx, posterData, curTheme())
}

function save() {
  if (!curIssue.value) { uni.showToast({ title: '请先选择期次', icon: 'none' }); return }
  uni.canvasToTempFilePath({
    canvasId: 'poster',
    success: (r) => {
      uni.saveImageToPhotosAlbum({
        filePath: r.tempFilePath,
        success: () => uni.showToast({ title: '已保存到相册', icon: 'success' }),
        fail: () => uni.showToast({ title: '请在设置中开启相册权限', icon: 'none' }),
      })
    },
    fail: () => uni.showToast({ title: '请在微信小程序中保存', icon: 'none' }),
  })
}

function onChange(code) { setCode(code); loadIssues() }

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错 */ }
  }
  loadIssues()
})
</script>

<style scoped>
.issues { white-space: nowrap; padding: 16rpx 20rpx; }
.ichip { display: inline-block; padding: 10rpx 24rpx; margin-right: 14rpx; background: #fff; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.ichip.active { background: #e53935; color: #fff; }
.themes { display: flex; padding: 0 20rpx 12rpx; }
.tchip { padding: 10rpx 24rpx; margin-right: 14rpx; background: #fff; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.tchip.active { background: #fb8c00; color: #fff; }
.cvwrap { display: flex; justify-content: center; padding: 12rpx 0; }
.poster { width: 600rpx; height: 840rpx; background: #fff; }
.hint { text-align: center; color: #999; padding: 20rpx; font-size: 28rpx; }
.actions { padding: 24rpx 20rpx; }
.btn { width: 100%; background: #e53935; color: #fff; font-size: 30rpx; }
</style>
```

- [ ] **Step 3: pages.json 注册**

`lottery_frontend/src/pages.json` 的 `pages` 数组里，在 `pages/purchase/create` 行后加（给 create 行末补逗号）：
```json
    { "path": "pages/poster/index", "style": { "navigationBarTitleText": "开奖海报" } }
```

- [ ] **Step 4: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/poster.js lottery_frontend/src/pages/poster/index.vue lottery_frontend/src/pages.json
git commit -m "feat: 开奖海报页canvas绘制+保存到相册"
```

---

## 计划自检

**1. Spec 覆盖：**
- POSTER_THEMES 3 主题（spec §2.1）→ Task 1 Step 3 ✓
- buildPosterData（spec §2.2）→ Task 1 Step 3 ✓
- drawPoster canvas（spec §2.3）→ Task 2 Step 1 ✓
- 海报页 选彩种/选期/选主题/保存（spec §1）→ Task 2 Step 2 ✓
- 入口（spec §3）→ Task 1 Step 4 ✓
- 错误处理/平台（spec §4）→ Task 2 save fail/未选期 hint ✓
- 测试（spec §5）→ Task 1（poster + menu 用例）✓；canvas/保存目测

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码与确切命令。

**3. 类型/签名一致性：** `buildPosterData(detail,name,category)`/`drawPoster(ctx,data,theme)`/`POSTER_THEMES` 在 poster.js、测试、页面一致；`ballColor` 来自 format.js（现有）；getHistory 返回 `res.results`（与 history 页一致）；HOME_MENU 加 poster 后 length=9 与 menu.test 一致。
