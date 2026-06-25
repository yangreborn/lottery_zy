# 往期开奖记住彩种（持久化全局彩种）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让全局彩种 code 持久化——进入往期/开奖/统计/选号默认展示用户上次选的彩种（兜底双色球），不再每次回到双色球。

**Architecture:** 单点改造 `src/store/lottery.js`：新增 `readStoredCode()`（带 `typeof uni` 守卫 + try，模块导入时读存储初始化 `code`），`setCode` 写内存的同时持久化到 `uni.setStorageSync('lottery_code')`。其余彩种页（history/latest/stats/picker/detail）不改，自动获得「记住上次」。

**Tech Stack:** uni-app (Vue3) reactive store、uni storage、vitest（node 环境，`globalThis.uni` stub）。

## Global Constraints

- 纯前端，不动后端。
- 前端无 Pinia/Vuex；沿用现有 `reactive` store 写法。
- 存储 key 固定为 `'lottery_code'`；读不到/异常/无 `uni` 全局时兜底 `'ssq'`。
- `readStoredCode` 与 `setCode` 的存储访问必须带 `typeof uni !== 'undefined'` 守卫并 try 包裹（vitest 为 node 环境，无守卫 import 即崩）。
- 不校验彩种合法性（YAGNI）。
- 不删除既有测试。
- `lotteryStore` / `setCode(c)` 对外签名不变，消费方引用零改动。

---

### Task 1: store 持久化彩种 code

**Files:**
- Modify: `lottery_frontend/src/store/lottery.js`
- Test: `lottery_frontend/tests/lotterystore.test.js`（新建）

**Interfaces:**
- Produces:
  - `lotteryStore`（reactive，含 `code: string`）— 不变
  - `setCode(c: string): void` — 写 `lotteryStore.code` + 持久化 `uni.setStorageSync('lottery_code', c)`
  - `readStoredCode(): string` — 读 `uni.getStorageSync('lottery_code')`，兜底 `'ssq'`（新增导出）

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/lotterystore.test.js`（照 `tests/device.test.js` 的 stub 模式）：
```js
import { describe, it, expect, beforeEach } from 'vitest'
import { lotteryStore, setCode, readStoredCode } from '../src/store/lottery.js'

function stubStorage(initial = {}) {
  const store = { ...initial }
  globalThis.uni = {
    getStorageSync: (k) => store[k] || '',
    setStorageSync: (k, v) => { store[k] = v },
  }
  return store
}

describe('lottery store 持久化彩种', () => {
  beforeEach(() => { stubStorage(); setCode('ssq') })

  it('readStoredCode 存储有值时返回该值', () => {
    stubStorage({ lottery_code: 'dlt' })
    expect(readStoredCode()).toBe('dlt')
  })

  it('readStoredCode 存储为空时兜底 ssq', () => {
    stubStorage()
    expect(readStoredCode()).toBe('ssq')
  })

  it('setCode 同步内存与存储', () => {
    stubStorage()
    setCode('kl8')
    expect(lotteryStore.code).toBe('kl8')
    expect(readStoredCode()).toBe('kl8')
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- lotterystore`
Expected: FAIL（`readStoredCode` is not exported / 未定义）

- [ ] **Step 3: 改 store/lottery.js**

`lottery_frontend/src/store/lottery.js` 整体替换为：
```js
import { reactive } from 'vue'

const STORAGE_KEY = 'lottery_code'

export function readStoredCode() {
  try {
    if (typeof uni !== 'undefined') {
      return uni.getStorageSync(STORAGE_KEY) || 'ssq'
    }
  } catch (e) {
    // 读存储失败，兜底
  }
  return 'ssq'
}

export const lotteryStore = reactive({ code: readStoredCode() })

export function setCode(c) {
  lotteryStore.code = c
  try {
    if (typeof uni !== 'undefined') {
      uni.setStorageSync(STORAGE_KEY, c)
    }
  } catch (e) {
    // 写存储失败，内存态已更新，不影响本次使用
  }
}
```

- [ ] **Step 4: 跑测试确认通过 + 全量回归**

Run: `cd lottery_frontend && npm test`
Expected: 全绿（新增 3 用例 + 既有用例无回归）

- [ ] **Step 5: build 验证**

Run: `cd lottery_frontend && npm run build:h5`
Expected: `Build complete.`

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/store/lottery.js lottery_frontend/tests/lotterystore.test.js
git commit -m "feat: 持久化全局彩种code，记住用户上次选择"
```

---

## 计划自检

**1. Spec 覆盖：**
- 持久化全局彩种（读存储初始化 + 选择写存储）→ Task 1 ✓
- 兜底双色球 / typeof 守卫 + try → Task 1 readStoredCode/setCode ✓
- 不改其他页 → 计划只触 store + 新测试文件 ✓
- 测试照 device.test.js stub 模式 → Task 1 Step 1 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码与确切命令。

**3. 类型/签名一致性：** `lotteryStore.code` / `setCode(c)` / `readStoredCode()` 三处命名在 spec、Interfaces、测试、实现中一致；存储 key `'lottery_code'` 一致。
