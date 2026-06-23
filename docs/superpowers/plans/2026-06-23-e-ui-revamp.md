# E · UI/导航改版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把入口改成菜单选项首页，tabBar 重构为 首页/统计/选号/我的，并加 G4 暖色渐变底色与放大关键字号。

**Architecture:** 纯前端（uni-app Vue3）。新增菜单首页 pages/home/index.vue（读 utils/menu.js 配置，按目标分型 switchTab/navigateTo），pages.json 把 home 置首位 + tabBar 改 4 项 + globalStyle 底色，新增公共 TopBanner.vue 渐变横幅各页复用，组件与页面字号上调约 15%。不动后端、不动业务逻辑。

**Tech Stack:** uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 纯前端改动，**不动后端、不动接口/数据逻辑**，只改导航结构 + 样式 + 新增首页。
- 跳转分型（关键，混用会运行时报错）：目标是 tabBar 页（统计 pages/draw/stats、选号 pages/mine/picker、我的 pages/mine/index）→ `uni.switchTab`；非 tabBar 页（当期 pages/draw/latest、往期 pages/draw/history、玩法 pages/guide/index、详情页）→ `uni.navigateTo`。
- 配色（G4）：渐变红横幅 `linear-gradient(180deg, #e53935 0%, #ff6f61 100%)`；首页渐变身 `linear-gradient(180deg, #ffd9d4 0%, #fff0ee 35%, #fbfbfb 100%)`；全局底色 `#fff0ee`；卡片阴影 `rgba(229,57,53,.10)`。
- 字号(rpx)：号码球 28→32；页面/卡片标题 28→34；列表主文字 26→30。
- uni-app 页面级渐变写在根 view `background`（H5 + mp-weixin 均支持 linear-gradient）；globalStyle 只能纯色。
- 前端 Vue3 JS，不引 Pinia/Vuex；命令在 `lottery_frontend/`；端口前端 5199/小程序 dev:mp-weixin。

---

## File Structure

- `lottery_frontend/src/utils/menu.js`(新)：首页菜单配置 + goMenu 跳转分型。
- `lottery_frontend/src/pages/home/index.vue`(新)：菜单首页。
- `lottery_frontend/src/components/TopBanner.vue`(新)：渐变红横幅(props title)。
- `lottery_frontend/src/pages.json`(改)：home 置首位 + tabBar 4 项 + globalStyle 底色。
- `lottery_frontend/src/components/Ball.vue`、`BallSelectable.vue`(改)：号码字号 32rpx。
- `lottery_frontend/src/pages/draw/{latest,history,detail,stats}.vue`、`guide/{index,detail}.vue`、`mine/{index,picker}.vue`(改)：接入 TopBanner + 字号；mine/index 与 picker 因选号成为 tabBar 页需改跳转方式。
- `lottery_frontend/tests/menu.test.js`(新)。

---

### Task 1: 菜单配置 utils/menu.js

**Files:**
- Create: `lottery_frontend/src/utils/menu.js`
- Test: `lottery_frontend/tests/menu.test.js`

**Interfaces:**
- Produces:
  - `HOME_MENU`：6 项数组，每项 `{key, title, icon, path, nav}`，nav 为 `'switchTab'|'navigateTo'`
  - `goMenu(item)`：item.nav==='switchTab' 调 `uni.switchTab({url:item.path})`，否则 `uni.navigateTo({url:item.path})`

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/menu.test.js`:
```js
import { describe, it, expect, beforeEach } from 'vitest'
import { HOME_MENU, goMenu } from '../src/utils/menu.js'

describe('HOME_MENU', () => {
  it('6 项且字段完整', () => {
    expect(HOME_MENU.length).toBe(6)
    for (const m of HOME_MENU) {
      expect(typeof m.key).toBe('string')
      expect(typeof m.title).toBe('string')
      expect(typeof m.icon).toBe('string')
      expect(m.path.startsWith('/pages/')).toBe(true)
      expect(['switchTab', 'navigateTo']).toContain(m.nav)
    }
  })

  it('tabBar 目标用 switchTab，非 tab 用 navigateTo', () => {
    const byKey = Object.fromEntries(HOME_MENU.map((m) => [m.key, m]))
    expect(byKey.stats.nav).toBe('switchTab')
    expect(byKey.picker.nav).toBe('switchTab')
    expect(byKey.mine.nav).toBe('switchTab')
    expect(byKey.latest.nav).toBe('navigateTo')
    expect(byKey.history.nav).toBe('navigateTo')
    expect(byKey.guide.nav).toBe('navigateTo')
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

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（找不到 menu.js）

- [ ] **Step 3: 写实现**

`lottery_frontend/src/utils/menu.js`:
```js
export const HOME_MENU = [
  { key: 'latest', title: '当期中奖', icon: '🎯', path: '/pages/draw/latest', nav: 'navigateTo' },
  { key: 'history', title: '往期开奖', icon: '📅', path: '/pages/draw/history', nav: 'navigateTo' },
  { key: 'stats', title: '号码统计', icon: '📊', path: '/pages/draw/stats', nav: 'switchTab' },
  { key: 'picker', title: '选号记录', icon: '✏️', path: '/pages/mine/picker', nav: 'switchTab' },
  { key: 'guide', title: '玩法介绍', icon: '📖', path: '/pages/guide/index', nav: 'navigateTo' },
  { key: 'mine', title: '我的号码', icon: '⭐', path: '/pages/mine/index', nav: 'switchTab' },
]

export function goMenu(item) {
  if (item.nav === 'switchTab') {
    uni.switchTab({ url: item.path })
  } else {
    uni.navigateTo({ url: item.path })
  }
}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `npm test`
Expected: PASS（menu 全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/menu.js lottery_frontend/tests/menu.test.js
git commit -m "feat: 首页菜单配置 menu.js(跳转分型)"
```

---

### Task 2: 菜单首页 + pages.json 导航重构

**Files:**
- Create: `lottery_frontend/src/pages/home/index.vue`
- Modify: `lottery_frontend/src/pages.json`
- Modify: `lottery_frontend/src/pages/mine/index.vue`（goPicker 改 switchTab）
- Modify: `lottery_frontend/src/pages/mine/picker.vue`（保存成功改 switchTab 回我的）

**Interfaces:**
- Consumes: `HOME_MENU`/`goMenu`(utils/menu)
- Produces: 菜单首页 pages/home/index（tabBar 第 1 项）；tabBar 4 项；选号成为 tabBar 页后相关跳转改为 switchTab。

- [ ] **Step 1: 写菜单首页**

`lottery_frontend/src/pages/home/index.vue`:
```vue
<template>
  <view class="home">
    <view class="banner"><text class="bt">彩票查询</text></view>
    <view class="grid">
      <view v-for="m in menu" :key="m.key" class="mcard" @click="go(m)">
        <text class="ic">{{ m.icon }}</text>
        <text class="tx">{{ m.title }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { HOME_MENU, goMenu } from '../../utils/menu.js'

const menu = HOME_MENU
function go(m) { goMenu(m) }
</script>

<style scoped>
.home { min-height: 100vh; background: linear-gradient(180deg, #ffd9d4 0%, #fff0ee 35%, #fbfbfb 100%); }
.banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: 44rpx 0; text-align: center; }
.bt { color: #fff; font-size: 42rpx; font-weight: 700; letter-spacing: 8rpx; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24rpx; padding: 28rpx; }
.mcard { background: #fff; border-radius: 20rpx; padding: 44rpx 0; text-align: center; box-shadow: 0 4rpx 16rpx rgba(229, 57, 53, 0.10); }
.ic { font-size: 56rpx; display: block; }
.tx { font-size: 32rpx; font-weight: 600; color: #333; display: block; margin-top: 14rpx; }
</style>
```

- [ ] **Step 2: 改 pages.json（home 置首 + tabBar 4 项 + 底色）**

`lottery_frontend/src/pages.json` 整体替换为：
```json
{
  "pages": [
    { "path": "pages/home/index", "style": { "navigationBarTitleText": "彩票查询" } },
    { "path": "pages/draw/latest", "style": { "navigationBarTitleText": "当期开奖" } },
    { "path": "pages/draw/history", "style": { "navigationBarTitleText": "历史开奖" } },
    { "path": "pages/draw/detail", "style": { "navigationBarTitleText": "开奖详情" } },
    { "path": "pages/draw/stats", "style": { "navigationBarTitleText": "号码统计" } },
    { "path": "pages/guide/index", "style": { "navigationBarTitleText": "玩法介绍" } },
    { "path": "pages/guide/detail", "style": { "navigationBarTitleText": "详情" } },
    { "path": "pages/mine/index", "style": { "navigationBarTitleText": "我的号码" } },
    { "path": "pages/mine/picker", "style": { "navigationBarTitleText": "选号" } }
  ],
  "tabBar": {
    "color": "#666",
    "selectedColor": "#e53935",
    "list": [
      { "pagePath": "pages/home/index", "text": "首页" },
      { "pagePath": "pages/draw/stats", "text": "统计" },
      { "pagePath": "pages/mine/picker", "text": "选号" },
      { "pagePath": "pages/mine/index", "text": "我的" }
    ]
  },
  "globalStyle": {
    "navigationBarTextStyle": "white",
    "navigationBarTitleText": "彩票查询",
    "navigationBarBackgroundColor": "#e53935",
    "backgroundColor": "#fff0ee"
  }
}
```

- [ ] **Step 3: 修因「选号」成为 tabBar 页引发的跳转**

`pages/mine/index.vue` 的 `goPicker` 改为 switchTab（navigateTo 跳 tabBar 页会报错）：
```js
function goPicker() { uni.switchTab({ url: '/pages/mine/picker' }) }
```

`pages/mine/picker.vue` 的 `save(payload)` 里保存成功后，把 `uni.navigateBack()` 改为切到「我的」（picker 现在是 tab 页，navigateBack 无可靠返回栈）：
```js
    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.switchTab({ url: '/pages/mine/index' }), 600)
```

- [ ] **Step 4: build + 目测**

Run: `npm run build:h5`
Expected: Build complete 无报错（9 页含 home）。
浏览器 `npm run dev:h5`：进入即菜单首页（渐变红横幅 + 6 卡片 + 浅红渐变身）；点「当期/往期/玩法」navigateTo 进、「统计/选号/我的」切 tab；底部 tabBar 4 项；「我的」页「去选号」与 picker 保存后切 tab 正常。

- [ ] **Step 5: 全量前端测试**

Run: `npm test`
Expected: PASS（既有单测 + menu 全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/pages/home/index.vue lottery_frontend/src/pages.json lottery_frontend/src/pages/mine/index.vue lottery_frontend/src/pages/mine/picker.vue
git commit -m "feat: 菜单选项首页 + tabBar 重构(首页/统计/选号/我的) + 全局暖底色"
```

---

### Task 3: 公共渐变横幅 TopBanner + 组件字号

**Files:**
- Create: `lottery_frontend/src/components/TopBanner.vue`
- Modify: `lottery_frontend/src/components/Ball.vue`
- Modify: `lottery_frontend/src/components/BallSelectable.vue`

**Interfaces:**
- Produces: `TopBanner.vue`（props `title:String`，渐变红横幅 + 白字）；Ball/BallSelectable 号码字号 32rpx。

- [ ] **Step 1: 写 TopBanner**

`lottery_frontend/src/components/TopBanner.vue`:
```vue
<template>
  <view class="top-banner"><text class="tb-title">{{ title }}</text></view>
</template>

<script setup>
defineProps({ title: { type: String, default: '' } })
</script>

<style scoped>
.top-banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: 28rpx 0; text-align: center; }
.tb-title { color: #fff; font-size: 34rpx; font-weight: 700; letter-spacing: 4rpx; }
</style>
```

- [ ] **Step 2: 放大 Ball 字号**

`lottery_frontend/src/components/Ball.vue` — 把 `.num` 的 `font-size: 28rpx;` 改为 `font-size: 32rpx;`（其余不动，保留原注释/结构）。

- [ ] **Step 3: 放大 BallSelectable 字号**

`lottery_frontend/src/components/BallSelectable.vue` — 把 `.sball` 的 `font-size: 26rpx;` 改为 `font-size: 32rpx;`（其余不动）。

- [ ] **Step 4: build 验证**

Run: `npm run build:h5`
Expected: Build complete 无报错。

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/components/TopBanner.vue lottery_frontend/src/components/Ball.vue lottery_frontend/src/components/BallSelectable.vue
git commit -m "feat: 公共渐变横幅 TopBanner + 号码球字号放大"
```

---

### Task 4: 各业务页接入 TopBanner + 字号放大

**Files:**
- Modify: `lottery_frontend/src/pages/draw/latest.vue`、`history.vue`、`detail.vue`、`stats.vue`
- Modify: `lottery_frontend/src/pages/guide/index.vue`、`detail.vue`
- Modify: `lottery_frontend/src/pages/mine/index.vue`、`picker.vue`

**Interfaces:**
- Consumes: `TopBanner`(components)
- Produces: 8 个业务页顶部加渐变红横幅 + 关键字号放大，整体风格与首页统一。

每个页面统一操作：① `import TopBanner from '../../components/TopBanner.vue'`（页面在 `src/pages/<dir>/` 下，相对路径 `../../components/TopBanner.vue`）；② 在根 `<view class="page">`（或等价根 view）最顶部插入 `<TopBanner title="<页名>" />`；③ 按下表放大字号。先 Read 每个页面确认根 view 与现有 class 名再改。

- [ ] **Step 1: draw 四页接入 + 字号**

各页根 view 顶部加 TopBanner，title 分别：latest「当期开奖」、history「历史开奖」、detail「开奖详情」、stats「号码统计」。字号：
- latest.vue：`.issue` 等期号标题、`.grade` 文字相关，把页内主标题类(若有 28rpx)调 34rpx、列表/奖级文字 26rpx→30rpx。
- history.vue：`.issue` 行 26→30rpx。
- detail.vue：`.title`(若有)与奖级表文字调大；`.head .issue` 26→30rpx。
- stats.vue：`.zone-title` 26→30rpx、`.opt` 26→30rpx。
（具体类名以 Read 到的为准；只调字号，不动布局逻辑。）

- [ ] **Step 2: guide 两页接入 + 字号**

guide/index.vue 顶部加 `<TopBanner title="玩法介绍" />`；`.title` 28→34rpx、`.type` 26→30rpx。
guide/detail.vue 顶部加 `<TopBanner title="详情" />`；`.title` 32→34rpx（已较大，微调）、`.content` 28→30rpx。

- [ ] **Step 3: mine 两页接入 + 字号**

mine/index.vue 顶部加 `<TopBanner title="我的号码" />`；`.tag`/`.op` 等关键文字适当调大（24→28rpx、26→30rpx）。
mine/picker.vue 顶部加 `<TopBanner title="选号" />`；`.zt`(区标题) 26→30rpx、`.btn` 26→30rpx。

- [ ] **Step 4: build + 端到端目测**

Run: `npm run build:h5`
Expected: Build complete 无报错（全部页面编译通过）。
浏览器 `npm run dev:h5`（后端在 8123 跑、有 seed 数据）：每页顶部都有渐变红横幅，字更大，暖色底不发白；首页 → 各页跳转正常；tabBar 4 项正常。

- [ ] **Step 5: 全量前端测试**

Run: `npm test`
Expected: PASS（页面改动不影响既有单测，全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/pages
git commit -m "feat: 各业务页接入渐变横幅 + 关键字号放大"
```

---

## 计划自检

**1. Spec 覆盖：**
- 菜单选项首页（6 卡片 + 跳转分型）→ Task 1（配置）+ Task 2（页面）✓
- tabBar 重构 首页/统计/选号/我的 → Task 2 ✓
- G4 渐变底色（横幅 + 渐变身 + 全局底色）→ Task 2（首页+全局）+ Task 3（TopBanner）+ Task 4（各页横幅）✓
- 字号放大 → Task 3（球）+ Task 4（各页）✓
- 不动后端/业务 → 全为前端样式/导航/新增页 ✓

**2. Placeholder 扫描：** 代码步骤含完整代码；Task 4 的字号调整给了具体类名与数值方向，要求执行者先 Read 页面对齐实际类名（样式微调，非占位）。

**3. 类型/签名一致性：**
- `HOME_MENU`/`goMenu`(Task1) 被首页(Task2)引用一致。
- `TopBanner` props title(Task3) 被各页(Task4)引用一致。
- pages.json tabBar 4 项与「选号=picker 是 tab 页」一致；Task2 同步把 mine/index goPicker 与 picker 保存跳转改 switchTab（避免 navigateTo/navigateBack 对 tab 页失效）。
- 配色/字号数值全计划一致（横幅 #e53935→#ff6f61、底色 #fff0ee、球 32rpx、标题 34rpx、列表 30rpx）。

**4. 注意点（给执行者）：**
- 跳转分型是硬约束：tab 页（统计/选号/我的）switchTab，非 tab（当期/往期/玩法/详情）navigateTo，写反会运行时报错。
- picker 成为 tabBar 页后：mine/index「去选号」用 switchTab；picker 保存成功用 switchTab 回我的（不能 navigateBack）。
- 页面级渐变写根 view background，不放 globalStyle；globalStyle 仅纯色底 #fff0ee。
- Task 4 改样式前先 Read 每页确认真实 class 名，只调字号不动布局。
- mp-weixin 与 H5 都支持 linear-gradient；改完可顺手 `npm run dev:mp-weixin` 在开发者工具看小程序端效果。
