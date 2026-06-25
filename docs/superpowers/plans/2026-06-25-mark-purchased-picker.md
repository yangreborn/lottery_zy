# 标为已购选择列表 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Checkbox steps.

**Goal:** 标为已购改为从期次列表选择，不手输。

**Architecture:** records.js 加 issueLabel；numbers.vue 拉 issues，用 picker 选期次后创建购买。

**Tech Stack:** uni-app Vue3 + vitest。

## Global Constraints

- 期次来源 `getHistory(code,{page:1}).results`；picker 选中创建 purchase(numbers=rec.numbers, bet_count=1, purchase_date=todayStr())。
- 中文。

---

### Task 1: issueLabel 工具

**Files:** src/utils/records.js、tests/records.test.js

- [ ] **Step 1: 写失败测试**（加入 tests/records.test.js）

```js
import { issueLabel } from '../src/utils/records.js'

describe('issueLabel', () => {
  it('拼期号+日期', () => {
    expect(issueLabel({ issue: '2026073', draw_date: '2026-06-20' })).toBe('2026073期 2026-06-20')
  })
  it('缺日期只显期号', () => {
    expect(issueLabel({ issue: '2026073' })).toBe('2026073期')
  })
})
```

- [ ] **Step 2:** `npm test -- records` 失败。
- [ ] **Step 3:** `src/utils/records.js` 加：

```js
export function issueLabel(item) {
  if (!item) return ''
  return item.draw_date ? `${item.issue}期 ${item.draw_date}` : `${item.issue}期`
}
```

- [ ] **Step 4:** `npm test -- records` 通过。
- [ ] **Step 5:** 提交 `feat(records): issueLabel 期次标签`。

### Task 2: numbers.vue 用 picker 标为已购

**Files:** src/pages/mine/numbers.vue

- [ ] **Step 1:** 引入 getHistory 与 issueLabel：

```js
import { getLotteryList, getHistory } from '../../api/lottery.js'
import { formatTime, groupRecords, todayStr, issueLabel } from '../../utils/records.js'
```

- [ ] **Step 2:** 加 issues ref 与标签 computed、加载函数：

```js
const issues = ref([])
const issueLabels = computed(() => issues.value.map(issueLabel))

async function loadIssues() {
  try { const res = await getHistory(store.code, { page: 1 }); issues.value = res.results || [] }
  catch (e) { issues.value = [] }
}
```

在 `load()` 末尾与 `onChange` 调 `loadIssues()`；onShow 也调一次（与彩种列表一起）。最简：在 `load()` 内 `await ensureLogin()` 后调用 `loadIssues()`（不阻塞主列表用 try）。具体：`load()` 成功拉 items 后 `loadIssues()`；`onChange` 已调 `load()`，无需额外。

- [ ] **Step 3:** 模板把「标为已购」改为 picker：

```html
        <view v-if="!manageMode" class="ops">
          <picker mode="selector" :range="issueLabels" :disabled="!issues.length" @change="onPickPurchase(rec, $event)">
            <text class="op">标为已购</text>
          </picker>
          <text class="op" @click="doGroup(rec)">归组</text>
          <text v-if="rec.target_issue" class="op" @click="doCheck(rec.id)">比对</text>
          <text class="op del" @click="doDelete(rec.id)">删除</text>
        </view>
```

- [ ] **Step 4:** 脚本替换 `doMarkPurchased` 为 `onPickPurchase`：

```js
async function onPickPurchase(rec, e) {
  const idx = Number(e.detail.value)
  const sel = issues.value[idx]
  if (!sel) { uni.showToast({ title: '暂无可选期次', icon: 'none' }); return }
  try {
    await purchaseCreate({ code: store.code, issue: sel.issue, numbers: rec.numbers, bet_count: 1, purchase_date: todayStr() })
    uni.showToast({ title: '已记录购买', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.msg || '记录失败', icon: 'none' })
  }
}
```

- [ ] **Step 5:** `load()` 内加载期次（成功分支后）：

```js
    items.value = await listNumbers(store.code)
    if (!items.value.length) emptyMsg.value = '还没有记录，去选号吧'
    loadIssues()
```

- [ ] **Step 6:** `npm test` 全绿；提交 `feat(purchase): 标为已购改期次 picker 选择(note41)`。

---

## Self-Review

- note41→Task1+2；issueLabel 有单测；picker 接线靠回归+手测。
- numbers.vue 已 import computed？是（顶部 `import { ref, computed } from 'vue'`），issueLabels computed 可用。
