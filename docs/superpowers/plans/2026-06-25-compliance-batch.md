# 合规小批 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 协议页 + 数据来源标注 + 机选纯随机声明 + 删除确认框（小程序合规 4 小改）。

**Architecture:** 纯前端。新增 legal.js 文本 + pages/legal/doc 页 + 首页 footer 入口；picker 加纯随机声明；mine 删除加确认。

**Tech Stack:** uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 纯前端，不动后端。不引 Pinia/Vuex；无 console。命令在 `lottery_frontend/`。
- 协议文本为模板（用户后续可替换正式法务文本），要点：免费查询/工具、匿名、数据来自官方网站仅供参考、不售彩不代购不投注、机选纯随机不预测、未成年勿用。
- TopBanner `:back="true"` 用于 navigateTo 进入的页（已支持 navigateBack/switchTab 兜底）。

---

## File Structure

- `lottery_frontend/src/utils/legal.js`(新)：LEGAL_DOCS + getLegalDoc。
- `lottery_frontend/tests/legal.test.js`(新)。
- `lottery_frontend/src/pages/legal/doc.vue`(新)：协议页。
- `lottery_frontend/src/pages.json`(改)：注册 legal/doc。
- `lottery_frontend/src/pages/home/index.vue`(改)：footer（数据来源 + 协议链接）。
- `lottery_frontend/src/pages/mine/picker.vue`(改)：机选纯随机声明。
- `lottery_frontend/src/pages/mine/index.vue`(改)：删除确认。

---

### Task 1: 协议页（legal.js + doc.vue + 注册）

**Files:**
- Create: `lottery_frontend/src/utils/legal.js`、`lottery_frontend/tests/legal.test.js`、`lottery_frontend/src/pages/legal/doc.vue`
- Modify: `lottery_frontend/src/pages.json`

**Interfaces:**
- Produces: `LEGAL_DOCS`、`getLegalDoc(type)`；页面 `/pages/legal/doc?type=agreement|privacy`。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/legal.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { LEGAL_DOCS, getLegalDoc } from '../src/utils/legal.js'

describe('legal docs', () => {
  it('含 agreement/privacy 两份且各有标题+非空段落', () => {
    for (const k of ['agreement', 'privacy']) {
      expect(LEGAL_DOCS[k].title).toBeTruthy()
      expect(Array.isArray(LEGAL_DOCS[k].paragraphs)).toBe(true)
      expect(LEGAL_DOCS[k].paragraphs.length).toBeGreaterThan(0)
    }
  })
  it('getLegalDoc 按 type 取，未知兜底 agreement', () => {
    expect(getLegalDoc('privacy')).toBe(LEGAL_DOCS.privacy)
    expect(getLegalDoc('xx')).toBe(LEGAL_DOCS.agreement)
    expect(getLegalDoc(undefined)).toBe(LEGAL_DOCS.agreement)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（无 legal.js）

- [ ] **Step 3: 写 legal.js**

`lottery_frontend/src/utils/legal.js`:
```js
export const LEGAL_DOCS = {
  agreement: {
    title: '用户协议',
    paragraphs: [
      '一、本应用为免费的彩票开奖信息查询与选号工具，仅供学习娱乐与信息参考，不提供购彩、代购或任何投注交易服务。',
      '二、应用内开奖号码、中奖与统计等数据来自中国福彩网(cwl.gov.cn)、中国体彩网(sporttery.cn)等官方公开渠道，仅供参考，最终结果以官方公布为准。',
      '三、机选号码由系统纯随机生成，不含任何预测、分析或中奖建议，任何号码均不构成投注建议。',
      '四、用户可匿名使用本应用，无需注册真实身份；请自行留存备份保存的号码等数据。',
      '五、请理性对待彩票，未成年人请勿使用。如不同意本协议，请停止使用本应用。',
    ],
  },
  privacy: {
    title: '隐私协议',
    paragraphs: [
      '一、本应用以匿名方式提供服务，默认不收集可识别您真实身份的个人信息。',
      '二、为区分不同用户的选号记录，应用会生成一个匿名设备标识保存在本地，该标识不关联您的真实身份。',
      '三、应用仅在您主动保存号码、分组、比对等操作时记录相应数据，用于向您展示个人选号记录。',
      '四、应用不会出售您的数据或提供给第三方用于营销，开奖数据均来自官方公开渠道。',
      '五、您可随时删除自己的选号记录。继续使用即表示您同意本隐私协议。',
    ],
  },
}

export function getLegalDoc(type) {
  return LEGAL_DOCS[type] || LEGAL_DOCS.agreement
}
```

- [ ] **Step 4: 写 doc.vue**

`lottery_frontend/src/pages/legal/doc.vue`:
```vue
<template>
  <view class="page">
    <TopBanner :title="doc.title" :back="true" />
    <view class="body">
      <view v-for="(p, i) in doc.paragraphs" :key="i" class="para">{{ p }}</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { getLegalDoc } from '../../utils/legal.js'

const doc = ref(getLegalDoc('agreement'))
onLoad((q) => { doc.value = getLegalDoc(q && q.type) })
</script>

<style scoped>
.body { padding: 24rpx; }
.para { font-size: 28rpx; color: #555; line-height: 1.8; margin-bottom: 18rpx; }
</style>
```

- [ ] **Step 5: pages.json 注册**

`lottery_frontend/src/pages.json` 的 `"pages"` 数组里加一条（在 mine/picker 之后）：
```json
    { "path": "pages/legal/doc", "style": { "navigationBarTitleText": "协议" } }
```
（注意：在前一条 `pages/mine/picker` 行末补逗号，保持 JSON 合法。）

- [ ] **Step 6: 跑测试 + build**

Run: `npm test`（PASS）；`npm run build:h5`（Build complete）

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/utils/legal.js lottery_frontend/tests/legal.test.js lottery_frontend/src/pages/legal/doc.vue lottery_frontend/src/pages.json
git commit -m "feat: 用户协议/隐私协议页(legal doc)"
```

---

### Task 2: 首页 footer（数据来源 + 协议入口）

**Files:**
- Modify: `lottery_frontend/src/pages/home/index.vue`

**Interfaces:**
- Consumes: `/pages/legal/doc?type=`（Task1）

- [ ] **Step 1: 改 home/index.vue**

`lottery_frontend/src/pages/home/index.vue` 整体替换为：
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
    <view class="footer">
      <view class="links">
        <text class="lk" @click="openDoc('agreement')">用户协议</text>
        <text class="sep">·</text>
        <text class="lk" @click="openDoc('privacy')">隐私协议</text>
      </view>
      <text class="src">数据来源：中国福彩网 cwl.gov.cn · 中国体彩网 sporttery.cn</text>
    </view>
  </view>
</template>

<script setup>
import { HOME_MENU, goMenu } from '../../utils/menu.js'

const menu = HOME_MENU
function go(m) { goMenu(m) }
function openDoc(type) { uni.navigateTo({ url: `/pages/legal/doc?type=${type}` }) }
</script>

<style scoped>
.home { min-height: 100vh; background: linear-gradient(180deg, #ffd9d4 0%, #fff0ee 35%, #fbfbfb 100%); }
.banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: 44rpx 0; text-align: center; }
.bt { color: #fff; font-size: 42rpx; font-weight: 700; letter-spacing: 8rpx; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24rpx; padding: 28rpx; }
.mcard { background: #fff; border-radius: 20rpx; padding: 44rpx 0; text-align: center; box-shadow: 0 4rpx 16rpx rgba(229, 57, 53, 0.10); }
.ic { font-size: 56rpx; display: block; }
.tx { font-size: 32rpx; font-weight: 600; color: #333; display: block; margin-top: 14rpx; }
.footer { padding: 20rpx 28rpx 40rpx; text-align: center; }
.links { margin-bottom: 12rpx; }
.lk { color: #e53935; font-size: 26rpx; }
.sep { color: #bbb; font-size: 26rpx; margin: 0 12rpx; }
.src { color: #999; font-size: 22rpx; display: block; line-height: 1.6; }
</style>
```

- [ ] **Step 2: build + 目测 + 测试**

Run: `npm run build:h5`（Build complete）；`npm test`（全绿）
目测：首页底部出现「用户协议 · 隐私协议」可点（打开对应协议）+「数据来源：…」。

- [ ] **Step 3: 提交**

```bash
git add lottery_frontend/src/pages/home/index.vue
git commit -m "feat: 首页 footer 数据来源标注 + 协议入口"
```

---

### Task 3: 机选纯随机声明 + 删除确认

**Files:**
- Modify: `lottery_frontend/src/pages/mine/picker.vue`、`lottery_frontend/src/pages/mine/index.vue`

- [ ] **Step 1: picker 加纯随机声明**

`lottery_frontend/src/pages/mine/picker.vue` 模板中机选模式的 `<view class="gen-bar">…</view>`（含机选5注/10注/换一批）之后、`v-for="(s, i) in sets"` 之前，插入一行：
```html
        <view class="rand-tip">机选号码为系统纯随机生成，不含任何预测或分析成分</view>
```
并在 `<style scoped>` 里加：
```css
.rand-tip { padding: 0 20rpx 10rpx; color: #999; font-size: 24rpx; }
```

- [ ] **Step 2: mine/index 删除确认**

`lottery_frontend/src/pages/mine/index.vue` 的 `doDelete` 整体替换为：
```js
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
```
（原 `async function doDelete(id) {...}` 改为 `function doDelete(id) {...}`，删除逻辑移入 showModal success 的 confirm 分支。）

- [ ] **Step 3: build + 目测 + 测试**

Run: `npm run build:h5`（Build complete）；`npm test`（全绿）
目测：机选页机选按钮下有纯随机声明；我的号码点"删除"先弹确认框，确定才删、取消不删。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/mine/picker.vue lottery_frontend/src/pages/mine/index.vue
git commit -m "feat: 机选纯随机声明 + 删除前确认框"
```

---

## 计划自检

**1. Spec 覆盖：**
- 协议页 + 入口（13）→ Task 1 + Task 2 footer 链接 ✓
- 数据来源（20）→ Task 2 footer ✓
- 机选纯随机声明（21）→ Task 3 ✓
- 删除确认（24）→ Task 3 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码（含协议模板文本）。

**3. 类型/签名一致性：**
- `getLegalDoc(type)`(Task1) 被 doc.vue onLoad 用；home openDoc 跳 `/pages/legal/doc?type=`(Task2) 与页面 path(Task1 pages.json) 一致。
- doDelete 改为带 showModal confirm，deleteNumber/load 既有引用不变。

**4. 注意点（给执行者）：**
- pages.json 加 legal/doc 时注意前一行补逗号，保持 JSON 合法。
- 协议文本逐字录入（已是模板，用户后续可改）。
- picker 纯随机声明只插在机选模式区域；删除确认 confirm 才删。
