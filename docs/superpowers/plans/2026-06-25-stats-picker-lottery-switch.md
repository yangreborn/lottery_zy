# 统计/选号 彩种切换 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给「号码统计」「选号」两页加彩种切换（复用 LotteryTabs）。

**Architecture:** 两页各持有 `lotteries` ref（getLotteryList）；统计页 onChange=setCode+load；选号页把一次性捕获的 `code` 改成响应式 `store.code`，抽出 `initRule()` 在加载与切换时重置选号状态。

**Tech Stack:** uni-app Vue3 setup + vitest（仅回归，无新组件单测）。

## Global Constraints

- 复用现有 `LotteryTabs`（`:list/:active/@change`）。
- 切换不重复请求彩种列表（持有在 `lotteries` ref）。
- 选号页切换彩种时清空选号上下文（sel/sets/selected/pickCount/note/targetIssue），保留 mode。
- 中文注释；全量前端测试保持通过。

---

### Task 1: 统计页加彩种切换

**Files:**
- Modify: `lottery_frontend/src/pages/draw/stats.vue`

- [ ] **Step 1: 模板加 LotteryTabs**

在 `<TopBanner title="号码统计" :back="true" />` 下一行插入：

```html
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
```

- [ ] **Step 2: 脚本接线**

import 段改为（新增 LotteryTabs / setCode / getLotteryList）：

```js
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Heatmap from '../../components/Heatmap.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getStats, getLotteryList } from '../../api/lottery.js'
import { reportAccess } from '../../utils/report.js'
import { sortCells } from '../../utils/statsort.js'
import { zoneLabel } from '../../utils/zones.js'
```

在 `const periodOptions = [10, 30, 50, 100]` 上方加：

```js
const store = lotteryStore
const lotteries = ref([])
```

加 `onChange` 并把 `onShow` 改为先填充彩种列表（替换原 onShow 块）：

```js
function onChange(code) { setCode(code); load() }

onShow(async () => {
  reportAccess('draw/stats', { lottery_code: lotteryStore.code })
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞统计 */ }
  }
  load()
})
```

（`load()` 仍读 `lotteryStore.code`，不变。）

- [ ] **Step 3: 全量前端测试**

Run: `cd lottery_frontend && npm test`
Expected: PASS（无回归）。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/draw/stats.vue
git commit -m "feat(stats): 号码统计页支持彩种切换"
```

---

### Task 2: 选号页支持彩种切换（响应式 + initRule）

**Files:**
- Modify: `lottery_frontend/src/pages/mine/picker.vue`

- [ ] **Step 1: 模板加 LotteryTabs**

在 `<TopBanner title="选号" :back="true" />` 下一行插入：

```html
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
```

- [ ] **Step 2: 脚本改为响应式 code + initRule**

import 段加入 LotteryTabs 与 setCode：

```js
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
```

把 `const code = lotteryStore.code` 替换为：

```js
const store = lotteryStore
const lotteries = ref([])
```

把三处 `code` 用法改为 `store.code`：
- `doGenerate`：`const res = await generateNumbers(store.code, n, picksObj.value)`
- `saveOne`：`return createNumber({ code: store.code, gen_type: genType, numbers, note: note.value, target_issue: targetIssue.value })`
- `saveManual` 的 `reportAccess('mine/create', { lottery_code: store.code, action: 'save_number' })`
- `saveBatch` 的 `reportAccess('mine/create', { lottery_code: store.code, action: 'save_number' })`

- [ ] **Step 3: 新增 initRule/onChange，重写 onLoad**

把文件末尾的 `onLoad(async () => { ... })` 整块替换为：

```js
function initRule() {
  const found = lotteries.value.find((l) => l.code === store.code)
  if (!found) { rule.value = null; emptyMsg.value = '彩种不存在'; return }
  rule.value = found.rule_config
  // 切换彩种：清空旧选号上下文，按新 zones 重建
  for (const k of Object.keys(sel)) delete sel[k]
  for (const z of zones.value) {
    sel[z.key] = z.ordered && z.allow_repeat ? new Array(z.count).fill(null) : []
  }
  pickCount.value = variableZone.value ? variableZone.value.pick_min : 0
  sets.value = []
  selected.value = []
  note.value = ''
  targetIssue.value = ''
}

function onChange(c) { setCode(c); initRule() }

onLoad(async () => {
  try {
    lotteries.value = await getLotteryList()
    initRule()
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
})
```

- [ ] **Step 4: 全量前端测试**

Run: `cd lottery_frontend && npm test`
Expected: PASS（无回归；picker.js/zones.js 等底层逻辑未改）。

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/pages/mine/picker.vue
git commit -m "feat(picker): 选号页支持彩种切换(响应式 code + initRule 重置)"
```

---

## Self-Review

**Spec coverage:** note 29（统计/选号切彩种）→ Task 1 + Task 2 ✓

**Placeholder scan:** 无 TBD/TODO；代码步骤完整。

**Type consistency:** 两页都用 `LotteryTabs :list="lotteries" :active="store.code" @change="onChange"`；picker 的 `store.code` 替换 `code` 后 `generateNumbers`/`createNumber` 签名不变；`initRule` 依赖的 `sel`/`sets`/`selected`/`pickCount`/`note`/`targetIssue`/`zones`/`variableZone` 均为该文件已有定义。
