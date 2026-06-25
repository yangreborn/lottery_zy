# 开奖详情修正 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Checkbox steps.

**Goal:** 空/0 奖池不显示、快乐8 档头去红、移除分省展开。

**Architecture:** 新增 hasPool 工具；detail/latest 条件渲染奖池、不传 area；PrizeGrades 删分省块、档头改色。

**Tech Stack:** uni-app Vue3 + vitest。

## Global Constraints

- `hasPool(raw)`：去逗号转数字，`Number.isFinite && >0`。
- PrizeGrades 不再接收/渲染 `area`（分省）；`.ghead` 颜色中性 `#555`。
- 中文。

---

### Task 1: hasPool 工具

**Files:** src/utils/format.js、tests/format.test.js

- [ ] **Step 1: 写失败测试**（加到 `tests/format.test.js`；若文件不存在则新建并 import 现有 formatAmount 等不必）

```js
import { describe, it, expect } from 'vitest'
import { hasPool } from '../src/utils/format.js'

describe('hasPool', () => {
  it('空/0 为 false', () => {
    expect(hasPool('')).toBe(false)
    expect(hasPool(null)).toBe(false)
    expect(hasPool(undefined)).toBe(false)
    expect(hasPool('0')).toBe(false)
    expect(hasPool(0)).toBe(false)
  })
  it('正数为 true（含千分位）', () => {
    expect(hasPool('1234')).toBe(true)
    expect(hasPool(1234)).toBe(true)
    expect(hasPool('1,234,567')).toBe(true)
  })
})
```

- [ ] **Step 2:** `npm test -- format` 失败（hasPool 未定义）。
- [ ] **Step 3:** `src/utils/format.js` 末尾加：

```js
export function hasPool(raw) {
  if (raw === null || raw === undefined || raw === '') return false
  const n = Number(String(raw).replace(/,/g, ''))
  return Number.isFinite(n) && n > 0
}
```

- [ ] **Step 4:** `npm test -- format` 通过。
- [ ] **Step 5:** 提交 `feat(format): hasPool 判定有效奖池`。

### Task 2: PrizeGrades 去分省 + 档头改色

**Files:** src/components/PrizeGrades.vue

- [ ] **Step 1:** 模板 flat 分支去掉 clickable/分省/area，简化为：

```html
    <template v-if="!data.grouped">
      <view v-for="(g, i) in data.flat" :key="i" class="grade">
        <text class="c1">{{ g.label }}</text>
        <text class="c2">{{ g.count }}</text>
        <text class="c3">{{ formatAmount(g.amount) }}</text>
      </view>
      <view v-if="!data.flat.length" class="none">暂无奖级数据</view>
    </template>
```

- [ ] **Step 2:** 脚本删除 `area` prop、`stripAreaPrefix` 引用、`areaText`、`open1`：

```js
import { ref } from 'vue'
import { normalizePrizes } from '../utils/prize.js'
import { formatAmount } from '../utils/format.js'

const props = defineProps({
  grades: { type: Array, default: () => [] },
})
const data = computed(() => normalizePrizes(props.grades))
const open = ref([])
function toggle(pick) {
  open.value = open.value.includes(pick)
    ? open.value.filter((p) => p !== pick)
    : [...open.value, pick]
}
```

（注意保留 `computed` 的 import：`import { ref, computed } from 'vue'`。）

- [ ] **Step 3:** 样式：删 `.clickable .more` 与 `.area`；`.ghead` 颜色 `#e53935` → `#555`。

- [ ] **Step 4:** `npm test` 全绿（prize.js 逻辑未改）。
- [ ] **Step 5:** 提交 `feat(prize): 移除分省展开，快乐8 档头改中性色(note39)`。

### Task 3: detail/latest 奖池条件渲染 + 不传 area

**Files:** src/pages/draw/detail.vue、src/pages/draw/latest.vue

- [ ] **Step 1:** 两页奖池行加 v-if，PrizeGrades 去掉 :area：

```html
      <view v-if="hasPool(draw.pool_amount)" class="pool">奖池：{{ formatAmount(draw.pool_amount) }} 元</view>
      <PrizeGrades :grades="draw.prize_grades" />
```

- [ ] **Step 2:** 两页 import 加 hasPool：`import { formatAmount, hasPool } from '../../utils/format.js'`。

- [ ] **Step 3:** `npm test` 全绿。
- [ ] **Step 4:** 提交 `feat(draw): 无有效奖池不显示奖池行(note39)`。

---

## Self-Review

- 空/0 奖池→Task1+3；快乐8 档头→Task2；分省移除→Task2(+Task3 去 :area)。
- hasPool 有单测；PrizeGrades/detail/latest 为模板改动靠回归+手测。
- 一致性：detail 与 latest 同步改（两页奖池/PrizeGrades 用法一致）。
