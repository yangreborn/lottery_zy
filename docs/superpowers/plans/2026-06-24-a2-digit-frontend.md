# A2 前端 · 3D/排列三 位置式选号 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 前端支持 3D/排列三：选号页位置式选号、数字球单字符；并补修 mine/index 按 numbers entries 渲染（快乐8/数字彩记录显示）。

**Architecture:** Ball 加 pad prop（数字球单字符）；picker 检测 digit zone（ordered+allow_repeat）渲染 count 个位置选择器；utils/picker.js 加 digitsFilled 判完整；展示页/我的页对 digit 球传 pad=1，mine/index 改 entries 遍历。

**Tech Stack:** uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 纯前端，不动后端。不引 Pinia/Vuex；无 console。命令在 `lottery_frontend/`。
- Ball `pad` prop（默认 2），`display = String(value).padStart(pad, '0')`；digit 球传 `:pad="1"`（3D 690 显示 6 9 0）。
- picker digit zone = `zones.find(z => z.ordered && z.allow_repeat)`；该区 sel[key] 为定长 count 数组（位赋值，可重复），位置式选择器每位 0-9。
- `digitsFilled(arr)`：arr 长度>0 且每位非 null/undefined → true。
- canSaveManual：digit 区用 digitsFilled，否则 selectionComplete；saveManual 存 {...sel}（digit 为 [d1,d2,d3]）。
- 机选区/展示页/我的页：digit 区球（key==='digits'）传 pad=1；mine/index 由写死 red/blue 改 numbers entries 遍历。
- 目测需后端 8123（已 re-seed + 3d/pl3 数据）。

---

## File Structure

- `lottery_frontend/src/components/Ball.vue`(改)：pad prop。
- `lottery_frontend/src/utils/picker.js`(改)：digitsFilled。
- `lottery_frontend/tests/picker.test.js`(改)：digitsFilled 测试。
- `lottery_frontend/src/pages/mine/picker.vue`(改)：digit 位置式选号 + 机选 pad。
- `lottery_frontend/src/pages/draw/latest.vue` `history.vue` `detail.vue` `mine/index.vue`(改)：digit 球 pad（mine/index 同时改 entries）。

---

### Task 1: Ball pad prop + digitsFilled

**Files:**
- Modify: `lottery_frontend/src/components/Ball.vue`、`lottery_frontend/src/utils/picker.js`
- Test: `lottery_frontend/tests/picker.test.js`（追加）

**Interfaces:**
- Produces: Ball `pad` prop（默认 2）；`digitsFilled(arr) -> boolean`。

- [ ] **Step 1: 追加失败测试**

`lottery_frontend/tests/picker.test.js` 末尾追加（顶部 import 补 digitsFilled）：
```js
import { digitsFilled } from '../src/utils/picker.js'

describe('digitsFilled', () => {
  it('全部填满 true', () => {
    expect(digitsFilled([6, 9, 0])).toBe(true)
    expect(digitsFilled([0, 0, 0])).toBe(true)
  })
  it('含 null/undefined false', () => {
    expect(digitsFilled([6, null, 0])).toBe(false)
    expect(digitsFilled([6, undefined, 0])).toBe(false)
  })
  it('空/非数组 false', () => {
    expect(digitsFilled([])).toBe(false)
    expect(digitsFilled(null)).toBe(false)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（无 digitsFilled）

- [ ] **Step 3: 加 digitsFilled**

`lottery_frontend/src/utils/picker.js` 末尾追加：
```js
export function digitsFilled(arr) {
  return Array.isArray(arr) && arr.length > 0 && arr.every((v) => v !== null && v !== undefined)
}
```

- [ ] **Step 4: Ball.vue 加 pad prop**

`lottery_frontend/src/components/Ball.vue` 的 script 改为：
```js
import { computed } from 'vue'
import { ballColor } from '../utils/format.js'

const props = defineProps({
  value: { type: [Number, String], required: true },
  zone: { type: String, default: 'red' },
  pad: { type: Number, default: 2 },
})

const color = computed(() => ballColor(props.zone))
const display = computed(() => String(props.value).padStart(props.pad, '0'))
```

- [ ] **Step 5: 跑测试确认通过**

Run: `npm test`
Expected: PASS（digitsFilled + 既有全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/components/Ball.vue lottery_frontend/src/utils/picker.js lottery_frontend/tests/picker.test.js
git commit -m "feat: Ball pad prop(数字球单字符) + digitsFilled"
```

---

### Task 2: picker.vue 位置式选号（digit zone）

**Files:**
- Modify: `lottery_frontend/src/pages/mine/picker.vue`（整体替换）

**Interfaces:**
- Consumes: `getZones`、`digitsFilled`/`selectionComplete`/`toggleBall`/`toggleIndex`(utils/picker)、`generateNumbers`、Ball/BallSelectable
- Produces: digit 彩种位置式选号；机选数字球 pad=1。

- [ ] **Step 1: 整体替换 picker.vue**

`lottery_frontend/src/pages/mine/picker.vue`:
```vue
<template>
  <view class="page">
    <TopBanner title="选号" :back="true" />
    <template v-if="zones.length">
      <view class="modes">
        <view class="mode" :class="{ active: mode === 'jixuan' }" @click="mode = 'jixuan'"><text>机选</text></view>
        <view class="mode" :class="{ active: mode === 'manual' }" @click="mode = 'manual'"><text>手动</text></view>
      </view>

      <view v-if="variableZone" class="play">
        <text class="pt">玩法（选几个）</text>
        <view class="play-opts">
          <view
            v-for="k in playOptions" :key="k"
            class="popt" :class="{ active: k === pickCount }" @click="setPick(k)"
          ><text>选{{ k }}</text></view>
        </view>
      </view>

      <view v-if="mode === 'jixuan'">
        <view class="gen-bar">
          <button class="btn" size="mini" @click="doGenerate(5)">机选5注</button>
          <button class="btn" size="mini" @click="doGenerate(10)">机选10注</button>
          <button class="btn alt" size="mini" :disabled="!sets.length" @click="reroll">换一批</button>
        </view>
        <view
          v-for="(s, i) in sets" :key="i"
          class="setrow" :class="{ sel: selected.includes(i) }" @click="toggleSel(i)"
        >
          <text class="chk">{{ selected.includes(i) ? '✓' : '○' }}</text>
          <view class="balls">
            <template v-for="(nums, key) in s">
              <Ball v-for="(n, bi) in nums" :key="key + bi" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
            </template>
          </view>
        </view>
        <view v-if="!sets.length" class="hint">点上面"机选5注/10注"先生成，再勾选要保存的。</view>
      </view>

      <view v-else>
        <template v-if="digitZone">
          <view v-for="pos in digitZone.count" :key="pos" class="zone">
            <text class="zt">第 {{ pos }} 位（{{ digitAt(pos - 1) }}）</text>
            <view class="grid">
              <view
                v-for="d in digitRange" :key="d"
                class="dbtn" :class="{ active: digitAt(pos - 1) === d }" @click="setDigit(pos - 1, d)"
              ><text>{{ d }}</text></view>
            </view>
          </view>
        </template>
        <template v-else>
          <view v-for="zone in zones" :key="zone.key" class="zone">
            <text class="zt">{{ zone.label }}（选 {{ targetOf(zone) }}）</text>
            <view class="grid">
              <BallSelectable
                v-for="n in rangeOf(zone)" :key="zone.key + n" :value="n" :zone="zone.key"
                :selected="(sel[zone.key] || []).includes(n)" @toggle="toggle(zone, $event)"
              />
            </view>
          </view>
        </template>
      </view>

      <view class="fields">
        <input class="ipt" v-model="note" placeholder="备注（可空）" />
        <input class="ipt" v-model="targetIssue" placeholder="目标期号（可空，用于比对）" />
      </view>
      <view class="actions">
        <button v-if="mode === 'jixuan'" class="btn save" :disabled="!selected.length" @click="saveBatch">
          保存选中({{ selected.length }})
        </button>
        <button v-else class="btn save" :disabled="!canSaveManual" @click="saveManual">保存手选</button>
      </view>
    </template>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import Ball from '../../components/Ball.vue'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, createNumber, generateNumbers } from '../../api/user.js'
import { toggleBall, selectionComplete, toggleIndex, digitsFilled } from '../../utils/picker.js'
import { getZones } from '../../utils/zones.js'
import { reportAccess } from '../../utils/report.js'

const rule = ref(null)
const emptyMsg = ref('加载中…')
const mode = ref('jixuan')
const code = lotteryStore.code

const zones = computed(() => getZones(rule.value))
const variableZone = computed(
  () => zones.value.find((z) => z.pick_min !== undefined && z.pick_max !== undefined) || null
)
const digitZone = computed(() => zones.value.find((z) => z.ordered && z.allow_repeat) || null)
const digitRange = computed(() => (digitZone.value ? rangeOf(digitZone.value) : []))
const playOptions = computed(() => {
  const z = variableZone.value
  if (!z) return []
  const arr = []
  for (let k = z.pick_min; k <= z.pick_max; k++) arr.push(k)
  return arr
})
const pickCount = ref(0)
const picksObj = computed(() => (variableZone.value ? { [variableZone.value.key]: pickCount.value } : undefined))

const sel = reactive({})

function rangeOf(zone) {
  const arr = []
  for (let i = zone.min; i <= zone.max; i++) arr.push(i)
  return arr
}
function targetOf(zone) {
  if (zone.pick_min !== undefined && zone.pick_max !== undefined) return pickCount.value
  return zone.count
}
function toggle(zone, n) {
  sel[zone.key] = toggleBall(sel[zone.key] || [], n, targetOf(zone))
}
function setPick(k) {
  pickCount.value = k
  if (variableZone.value) sel[variableZone.value.key] = []
  sets.value = []
  selected.value = []
}
function digitAt(i) {
  const a = digitZone.value ? sel[digitZone.value.key] : null
  return a && a[i] !== null && a[i] !== undefined ? a[i] : '?'
}
function setDigit(pos, d) {
  const key = digitZone.value.key
  sel[key] = sel[key].map((v, i) => (i === pos ? d : v))
}

const canSaveManual = computed(() => {
  if (!rule.value) return false
  if (digitZone.value) return digitsFilled(sel[digitZone.value.key])
  return selectionComplete(sel, rule.value, picksObj.value || {})
})

const sets = ref([])
const selected = ref([])
const lastCount = ref(5)

async function doGenerate(n) {
  lastCount.value = n
  try {
    await ensureLogin()
    const res = await generateNumbers(code, n, picksObj.value)
    sets.value = res.sets || []
    selected.value = sets.value.map((_, i) => i)
  } catch (e) {
    uni.showToast({ title: e.msg || '生成失败', icon: 'none' })
  }
}
function reroll() { doGenerate(lastCount.value) }
function toggleSel(i) { selected.value = toggleIndex(selected.value, i) }

const note = ref('')
const targetIssue = ref('')

async function saveOne(numbers, genType) {
  await ensureLogin()
  return createNumber({ code, gen_type: genType, numbers, note: note.value, target_issue: targetIssue.value })
}

async function saveManual() {
  if (!canSaveManual.value) return
  try {
    await saveOne({ ...sel }, 'manual')
    uni.showToast({ title: '已保存', icon: 'success' })
    reportAccess('mine/create', { lottery_code: code, action: 'save_number' })
    setTimeout(() => uni.switchTab({ url: '/pages/mine/index' }), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
}

async function saveBatch() {
  if (!selected.value.length) {
    uni.showToast({ title: '请先勾选', icon: 'none' })
    return
  }
  let ok = 0
  let fail = 0
  for (const i of selected.value) {
    try { await saveOne(sets.value[i], 'random'); ok += 1 } catch (e) { fail += 1 }
  }
  uni.showToast({ title: fail ? `成功${ok}注 失败${fail}注` : `已保存${ok}注`, icon: fail ? 'none' : 'success' })
  if (ok > 0) reportAccess('mine/create', { lottery_code: code, action: 'save_number' })
  if (ok && !fail) setTimeout(() => uni.switchTab({ url: '/pages/mine/index' }), 700)
}

onLoad(async () => {
  try {
    const list = await getLotteryList()
    const found = list.find((l) => l.code === code)
    if (found) {
      rule.value = found.rule_config
      for (const z of zones.value) {
        sel[z.key] = z.ordered && z.allow_repeat ? new Array(z.count).fill(null) : []
      }
      if (variableZone.value) pickCount.value = variableZone.value.pick_min
    } else {
      emptyMsg.value = '彩种不存在'
    }
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
})
</script>

<style scoped>
.modes { display: flex; margin: 16rpx 20rpx; background: #fff; border-radius: 12rpx; overflow: hidden; }
.mode { flex: 1; text-align: center; padding: 20rpx 0; color: #666; font-size: 30rpx; }
.mode.active { background: #e53935; color: #fff; font-weight: 600; }
.play { background: #fff; margin: 0 20rpx 12rpx; padding: 16rpx 20rpx; border-radius: 12rpx; }
.pt { font-size: 28rpx; color: #888; }
.play-opts { display: flex; flex-wrap: wrap; margin-top: 10rpx; }
.popt { padding: 10rpx 22rpx; margin: 6rpx 14rpx 6rpx 0; background: #f5f5f5; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.popt.active { background: #fb8c00; color: #fff; }
.gen-bar { display: flex; flex-wrap: wrap; padding: 12rpx 20rpx; }
.setrow { display: flex; align-items: center; background: #fff; margin: 12rpx 20rpx; padding: 18rpx; border-radius: 12rpx; border: 2rpx solid transparent; }
.setrow.sel { border-color: #e53935; }
.chk { font-size: 34rpx; color: #e53935; width: 48rpx; }
.balls { display: flex; flex-wrap: wrap; flex: 1; }
.hint { text-align: center; color: #999; padding: 40rpx 20rpx; font-size: 26rpx; }
.zone { background: #fff; margin: 16rpx 20rpx; padding: 20rpx; border-radius: 12rpx; }
.zt { font-size: 30rpx; color: #666; }
.grid { display: flex; flex-wrap: wrap; margin-top: 12rpx; }
.dbtn { width: 64rpx; height: 64rpx; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin: 8rpx; font-size: 32rpx; border: 2rpx solid #43a047; color: #43a047; }
.dbtn.active { background: #43a047; color: #fff; }
.fields { margin: 0 20rpx; }
.ipt { background: #fff; border-radius: 10rpx; padding: 18rpx; margin-top: 16rpx; font-size: 28rpx; }
.actions { padding: 24rpx 20rpx; }
.btn { background: #e53935; color: #fff; font-size: 30rpx; margin: 8rpx; }
.btn.alt { background: #1e88e5; }
.btn.save { width: 100%; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 2: build + 目测**

后端 8123 跑（已 3d/pl3 数据）。`npm run build:h5`（Build complete）→ `npm run dev:h5`。
Expected：
- ssq/dlt/kl8 选号页照旧（红蓝/玩法）。
- 3D/排列三选号页：手动模式出现"第1位/第2位/第3位"，每位 0-9 可点（可重复），3 位选满才能保存；机选每注 3 个数字（单字符，可重复）。

- [ ] **Step 3: 全量前端测试**

Run: `npm test`
Expected: PASS（既有全绿）

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/mine/picker.vue
git commit -m "feat: 选号页位置式选号(3D/排列三) + 机选数字球单字符"
```

---

### Task 3: 展示页/我的页数字球 pad + mine/index entries

**Files:**
- Modify: `lottery_frontend/src/pages/draw/latest.vue`、`history.vue`、`detail.vue`、`lottery_frontend/src/pages/mine/index.vue`

**Interfaces:**
- Consumes: Ball `pad` prop（Task1）

- [ ] **Step 1: latest/history/detail 数字球 pad**

三个文件中现有的：
```html
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" />
```
改为：
```html
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
```
（latest.vue / detail.vue 缩进为 10 空格、history.vue 为 12 空格，按各文件原缩进改。）

- [ ] **Step 2: mine/index.vue 改 entries + pad**

`lottery_frontend/src/pages/mine/index.vue` 模板中的：
```html
        <view class="balls">
          <Ball v-for="(n, i) in rec.numbers.red" :key="'r'+i" :value="n" zone="red" />
          <Ball v-for="(n, i) in rec.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
        </view>
```
替换为：
```html
        <view class="balls">
          <template v-for="(nums, key) in rec.numbers">
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
          </template>
        </view>
```

- [ ] **Step 3: build + 目测 + 测试**

Run: `npm run build:h5`（Build complete）；`npm test`（全绿）
目测：3D/排列三 当期/历史/详情显示 3 个绿色单字符数字球；我的号码页快乐8/数字彩记录正常显示号码球（不再因写死 red/blue 而空白）。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/draw/latest.vue lottery_frontend/src/pages/draw/history.vue lottery_frontend/src/pages/draw/detail.vue lottery_frontend/src/pages/mine/index.vue
git commit -m "fix: 数字球 pad=1 + 我的号码页按 numbers entries 渲染"
```

---

## 计划自检

**1. Spec 覆盖（前端部分）：**
- 位置式选号（digit zone count 个位置选择器，可重复）→ Task 2 ✓
- 数字球单字符（Ball pad）→ Task 1 + 接入 Task 2/3 ✓
- 展示/统计复用 zones entries → 已在 A1；本期补 digit pad → Task 3 ✓
- mine/index 遗漏修复（entries）→ Task 3 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- Ball `pad`(Task1) 被 picker 机选区/展示页/我的页(Task2/3) 传 `key==='digits'?1:2` 一致。
- `digitsFilled`(Task1) 被 picker canSaveManual(Task2) 用。
- digitZone=zones.find(ordered&&allow_repeat)(Task2) 与后端 seed digits zone flag 一致；sel[key] 定长 count 数组、setDigit 位赋值、saveManual {...sel} 贯通到 create digits。

**4. 注意点（给执行者）：**
- 目测需后端 8123（已 re-seed + 3d/pl3 各 100 期）。
- digit zone 无 pick_*，variableZone 为 null，不显示玩法行；机选走 generator(后端已 choices/不排序)。
- setDigit 用 map 返回新数组赋值确保响应式；digitAt 未选显示 '?'。
- mine/index 改 entries 后，ssq/dlt 记录(red/blue)、快乐8(main)、数字彩(digits)都能渲染；pad 仅 digits=1。
