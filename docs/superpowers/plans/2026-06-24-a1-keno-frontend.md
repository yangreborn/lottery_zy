# A1 前端 · 快乐8 + zones 渲染 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 前端按 zones 动态渲染（选号/统计/展示页），新增快乐8玩法选号，恢复 ssq/dlt 在 zones 格式下的正常显示。

**Architecture:** 新增前端 `utils/zones.js`(getZones/zoneLabel/zoneColor) 镜像后端归一化；picker/stats/3 个展示页改为按 zones 或 numbers 字典动态遍历；快乐8可变区显示"玩法"选几行。配套小后端改动：generate 接口接 picks。

**Tech Stack:** uni-app(Vue3+Vite, JS) + vitest；Django(仅 generate 接口加 picks)。

## Global Constraints

- 后端 generate 接口接受 picks（{zone_key:n} 或 None）传给 random_numbers；非 dict 时按 None。
- 前端 `getZones(ruleConfig)`：有 `zones` 数组直返；否则老 red/blue 转 [{key,label,color,...}]；空返回 []。`zoneLabel(key)`/`zoneColor(key)`：red/blue/main 映射，未知回退。
- `ballColor(zone)` 加 main→#fb8c00（red/blue/灰 不变）。
- `selectionComplete(numbers, rule, picks={})`：遍历 getZones，可变区(pick_min/pick_max)目标= picks[key]??pick_max，固定区= count；每区长度需 == 目标。
- picker：可变区显示"玩法(选几)"行；机选传 picks={可变区key:pickCount}；机选结果集与手动保存均按 zone key 字典组装。
- 展示页(latest/history/detail)按 `draw.numbers` 的 entries 动态渲染（zone=key）；stats 按返回的 zone key 动态出块。
- 不引 Pinia/Vuex；无 console。前端在 `lottery_frontend/`；后端在 `lottery_backend/`(先激活 .venv)。

---

## File Structure

- `lottery_backend/usernumber/views.py`(改)：NumberGenerateView 接 picks。
- `lottery_frontend/src/api/user.js`(改)：generateNumbers 加 picks。
- `lottery_frontend/src/utils/zones.js`(新)：getZones/zoneLabel/zoneColor。
- `lottery_frontend/src/utils/format.js`(改)：ballColor 加 main。
- `lottery_frontend/src/utils/picker.js`(改)：selectionComplete 泛化。
- `lottery_frontend/src/pages/mine/picker.vue`(改)：zones 动态 + 玩法。
- `lottery_frontend/src/pages/draw/stats.vue`(改)：zones 动态。
- `lottery_frontend/src/pages/draw/latest.vue` `history.vue` `detail.vue`(改)：numbers entries 动态。

---

### Task 1: 后端 generate 接 picks + 前端 api

**Files:**
- Modify: `lottery_backend/usernumber/views.py`、`lottery_frontend/src/api/user.js`
- Test: `lottery_backend/usernumber/tests/test_number_generate.py`（追加）

**Interfaces:**
- Produces: generate 接受 `picks`；前端 `generateNumbers(code, count, picks)`。

- [ ] **Step 1: 追加失败测试**

在 `lottery_backend/usernumber/tests/test_number_generate.py` 末尾追加（顶部若无 kl8 fixture，本测试自建 kl8 彩种）：
```python
def test_generate_keno_uses_picks(db, client):
    from lottery.models import Lottery
    Lottery.objects.create(
        code="kl8", name="快乐8", category="福彩",
        rule_config={"play_type": "keno", "zones": [
            {"key": "main", "label": "号码", "min": 1, "max": 80, "count": 20,
             "pick_min": 1, "pick_max": 10}]},
        draw_days=[1, 2, 3, 4, 5, 6, 7])
    login = client.post("/api/user/login", {"code": "gen-keno"},
                        content_type="application/json").json()
    token = login["data"]["token"]
    res = client.post("/api/user/number/generate",
                      data={"code": "kl8", "count": 2, "picks": {"main": 5}},
                      content_type="application/json",
                      HTTP_X_USER_ID=token).json()
    assert res["code"] == 0
    sets = res["data"]["sets"]
    assert len(sets) == 2
    assert all(len(s["main"]) == 5 for s in sets)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_number_generate.py::test_generate_keno_uses_picks -v`
Expected: FAIL（generate 忽略 picks，main 为 10 个）

- [ ] **Step 3: 改 NumberGenerateView**

`lottery_backend/usernumber/views.py` 的 NumberGenerateView 中：
```python
        count = max(1, min(count, 10))
        sets = [random_numbers(lottery.rule_config) for _ in range(count)]
```
改为：
```python
        count = max(1, min(count, 10))
        picks = request.data.get("picks")
        if not isinstance(picks, dict):
            picks = None
        sets = [random_numbers(lottery.rule_config, picks) for _ in range(count)]
```

- [ ] **Step 4: 前端 generateNumbers 加 picks**

`lottery_frontend/src/api/user.js` 的 generateNumbers 改为：
```js
export function generateNumbers(code, count, picks) {
  return request('/api/user/number/generate', { method: 'POST', data: { code, count, picks } })
}
```

- [ ] **Step 5: 跑测试确认通过 + 全量回归**

Run: `python -m pytest usernumber/tests/test_number_generate.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（ssq generate 不传 picks → random_numbers(rc, None) 行为不变）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_frontend/src/api/user.js lottery_backend/usernumber/tests/test_number_generate.py
git commit -m "feat: generate 接口接 picks(可变区选号个数)"
```

---

### Task 2: 前端 zones 工具 + ballColor + selectionComplete

**Files:**
- Create: `lottery_frontend/src/utils/zones.js`、`lottery_frontend/tests/zones.test.js`
- Modify: `lottery_frontend/src/utils/format.js`、`lottery_frontend/src/utils/picker.js`
- Test: `lottery_frontend/tests/picker.test.js`（追加）

**Interfaces:**
- Produces: `getZones(ruleConfig)`、`zoneLabel(key)`、`zoneColor(key)`；`selectionComplete(numbers, rule, picks={})`（泛化）。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/zones.test.js`:
```js
import { describe, it, expect } from 'vitest'
import { getZones, zoneLabel, zoneColor } from '../src/utils/zones.js'

describe('getZones', () => {
  it('新 zones 格式直返', () => {
    const rc = { zones: [{ key: 'main', label: '号码', min: 1, max: 80, count: 20, pick_min: 1, pick_max: 10 }] }
    expect(getZones(rc).map((z) => z.key)).toEqual(['main'])
  })
  it('老 red/blue 转换', () => {
    const rc = { red: { count: 6, min: 1, max: 33 }, blue: { count: 1, min: 1, max: 16 } }
    const z = getZones(rc)
    expect(z.map((x) => x.key)).toEqual(['red', 'blue'])
    expect(z[0].label).toBe('红球')
    expect(z[0].count).toBe(6)
  })
  it('空返回 []', () => {
    expect(getZones(null)).toEqual([])
    expect(getZones({})).toEqual([])
  })
})

describe('zoneLabel / zoneColor', () => {
  it('已知 key 映射', () => {
    expect(zoneLabel('main')).toBe('号码')
    expect(zoneColor('main')).toBe('#fb8c00')
  })
  it('未知回退', () => {
    expect(zoneLabel('xx')).toBe('xx')
    expect(zoneColor('xx')).toBe('#9e9e9e')
  })
})
```

在 `lottery_frontend/tests/picker.test.js` 末尾追加（顶部 import 补 selectionComplete，若已有则忽略）：
```js
import { selectionComplete } from '../src/utils/picker.js'

describe('selectionComplete zones', () => {
  const ssqRule = { red: { count: 6, min: 1, max: 33 }, blue: { count: 1, min: 1, max: 16 } }
  const kenoRule = { zones: [{ key: 'main', min: 1, max: 80, count: 20, pick_min: 1, pick_max: 10 }] }

  it('ssq 红6蓝1 完整', () => {
    expect(selectionComplete({ red: [1, 2, 3, 4, 5, 6], blue: [7] }, ssqRule)).toBe(true)
    expect(selectionComplete({ red: [1, 2, 3], blue: [7] }, ssqRule)).toBe(false)
  })
  it('keno 按 picks 目标个数', () => {
    expect(selectionComplete({ main: [1, 2, 3, 4, 5] }, kenoRule, { main: 5 })).toBe(true)
    expect(selectionComplete({ main: [1, 2, 3] }, kenoRule, { main: 5 })).toBe(false)
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（无 zones.js / selectionComplete 不接受 picks）

- [ ] **Step 3: 写 zones.js**

`lottery_frontend/src/utils/zones.js`:
```js
const KEY_LABELS = { red: '红球', blue: '蓝球', main: '号码' }
const KEY_COLORS = { red: '#e53935', blue: '#1e88e5', main: '#fb8c00' }

export function getZones(ruleConfig) {
  if (!ruleConfig) return []
  if (Array.isArray(ruleConfig.zones)) return ruleConfig.zones
  const zones = []
  for (const key of ['red', 'blue']) {
    const r = ruleConfig[key]
    if (!r) continue
    zones.push({ key, label: KEY_LABELS[key], color: KEY_COLORS[key], ...r })
  }
  return zones
}

export function zoneLabel(key) {
  return KEY_LABELS[key] || key
}

export function zoneColor(key) {
  return KEY_COLORS[key] || '#9e9e9e'
}
```

- [ ] **Step 4: 改 format.js ballColor**

`lottery_frontend/src/utils/format.js` 的 ballColor 改为：
```js
export function ballColor(zone) {
  if (zone === 'red') return '#e53935'
  if (zone === 'blue') return '#1e88e5'
  if (zone === 'main') return '#fb8c00'
  return '#9e9e9e'
}
```

- [ ] **Step 5: 改 picker.js selectionComplete**

`lottery_frontend/src/utils/picker.js` 顶部加 `import { getZones } from './zones.js'`，并把 selectionComplete 改为：
```js
export function selectionComplete(numbers, rule, picks = {}) {
  for (const zone of getZones(rule)) {
    const len = (numbers[zone.key] || []).length
    const variable = zone.pick_min !== undefined && zone.pick_max !== undefined
    const target = variable ? (picks[zone.key] ?? zone.pick_max) : zone.count
    if (len !== target) return false
  }
  return true
}
```
（toggleBall / toggleIndex 不动。）

- [ ] **Step 6: 跑测试确认通过**

Run: `npm test`
Expected: PASS（zones + selectionComplete + 既有全绿）

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/utils/zones.js lottery_frontend/tests/zones.test.js lottery_frontend/src/utils/format.js lottery_frontend/src/utils/picker.js lottery_frontend/tests/picker.test.js
git commit -m "feat: 前端 zones 工具 + ballColor main + selectionComplete 泛化"
```

---

### Task 3: picker.vue 按 zones 动态 + 快乐8玩法

**Files:**
- Modify: `lottery_frontend/src/pages/mine/picker.vue`（整体替换）

**Interfaces:**
- Consumes: `getZones`(utils/zones)、`selectionComplete`/`toggleBall`/`toggleIndex`(utils/picker)、`generateNumbers(code,count,picks)`、组件 Ball/BallSelectable
- Produces: 选号页按 zones 动态出区；可变区显示玩法行；机选传 picks。

- [ ] **Step 1: 整体替换 picker.vue**

`lottery_frontend/src/pages/mine/picker.vue`:
```vue
<template>
  <view class="page">
    <TopBanner title="选号" />
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
              <Ball v-for="(n, bi) in nums" :key="key + bi" :value="n" :zone="key" />
            </template>
          </view>
        </view>
        <view v-if="!sets.length" class="hint">点上面"机选5注/10注"先生成，再勾选要保存的。</view>
      </view>

      <view v-else>
        <view v-for="zone in zones" :key="zone.key" class="zone">
          <text class="zt">{{ zone.label }}（选 {{ targetOf(zone) }}）</text>
          <view class="grid">
            <BallSelectable
              v-for="n in rangeOf(zone)" :key="zone.key + n" :value="n" :zone="zone.key"
              :selected="(sel[zone.key] || []).includes(n)" @toggle="toggle(zone, $event)"
            />
          </view>
        </view>
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
import { toggleBall, selectionComplete, toggleIndex } from '../../utils/picker.js'
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

const canSaveManual = computed(() => rule.value && selectionComplete(sel, rule.value, picksObj.value || {}))

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
      for (const z of zones.value) sel[z.key] = []
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

后端 8123 跑（已 re-seed + kl8 数据）。前端 `npm run build:h5` 通过 → `npm run dev:h5`。
Expected:
- ssq/dlt 选号页：红球/蓝球两区正常（zones 渲染），机选/手动/保存照旧。
- 快乐8选号页：出现"玩法（选几个）"行（选1…选10）；选"选5"后手动只能选 5 个、机选每注 5 个；保存成功。

- [ ] **Step 3: 全量前端测试**

Run: `npm test`
Expected: PASS（既有全绿）

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/mine/picker.vue
git commit -m "feat: 选号页按 zones 动态渲染 + 快乐8玩法选号"
```

---

### Task 4: stats.vue 按 zones 动态

**Files:**
- Modify: `lottery_frontend/src/pages/draw/stats.vue`（整体替换）

**Interfaces:**
- Consumes: `getStats`、`sortCells`(utils/statsort)、`zoneLabel`(utils/zones)、Heatmap
- Produces: 统计页按返回的 zone key 动态出块（红/蓝 或 快乐8单区）。

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
    <view v-for="z in zoneKeys" :key="z" class="zone-block">
      <view class="zone-title">{{ zoneLabel(z) }}</view>
      <Heatmap :cells="sortedOf(z)" />
    </view>
    <view v-if="!zoneKeys.length" class="empty">{{ emptyMsg }}</view>
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
import { zoneLabel } from '../../utils/zones.js'

const periodOptions = [10, 30, 50, 100]
const periods = ref(30)
const sortOptions = [
  { key: 'number', label: '号码顺序' },
  { key: 'most', label: '出现最多' },
  { key: 'least', label: '出现最少' },
]
const sortMode = ref('number')
const statsData = ref({})
const emptyMsg = ref('加载中…')

const zoneKeys = computed(() => Object.keys(statsData.value).filter((k) => k !== 'periods'))
function sortedOf(z) {
  return sortCells(statsData.value[z] || [], sortMode.value)
}

async function load() {
  try {
    const res = await getStats(lotteryStore.code, periods.value)
    statsData.value = res || {}
    if (!zoneKeys.value.length) emptyMsg.value = '暂无数据'
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

`npm run build:h5` 通过 → dev:h5。
Expected：ssq/dlt 统计页红球+蓝球两块照旧（排序切换正常）；快乐8统计页单块"号码"1-80 出现/遗漏。

- [ ] **Step 3: 全量前端测试**

Run: `npm test`
Expected: PASS

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/draw/stats.vue
git commit -m "feat: 统计页按 zones 动态出块"
```

---

### Task 5: 展示页 latest/history/detail 按 numbers entries 动态

**Files:**
- Modify: `lottery_frontend/src/pages/draw/latest.vue`、`history.vue`、`detail.vue`

**Interfaces:**
- Consumes: `draw.numbers`（按 zone key 字典）、Ball（zone=key，颜色由 ballColor 处理 red/blue/main）
- Produces: 三展示页按 numbers 的 entries 动态渲染球。

- [ ] **Step 1: 改 latest.vue 球区**

`lottery_frontend/src/pages/draw/latest.vue` 模板中的：
```html
      <view class="balls">
        <Ball v-for="(n, i) in draw.numbers.red" :key="'r'+i" :value="n" zone="red" />
        <Ball v-for="(n, i) in draw.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
      </view>
```
改为：
```html
      <view class="balls">
        <template v-for="(nums, key) in draw.numbers">
          <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" />
        </template>
      </view>
```

- [ ] **Step 2: 改 history.vue 球区**

`lottery_frontend/src/pages/draw/history.vue` 模板中的：
```html
        <view class="balls">
          <Ball v-for="(n, i) in d.numbers.red" :key="'r'+i" :value="n" zone="red" />
          <Ball v-for="(n, i) in d.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
        </view>
```
改为：
```html
        <view class="balls">
          <template v-for="(nums, key) in d.numbers">
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" />
          </template>
        </view>
```

- [ ] **Step 3: 改 detail.vue 球区**

`lottery_frontend/src/pages/draw/detail.vue` 模板中的：
```html
      <view class="balls">
        <Ball v-for="(n, i) in draw.numbers.red" :key="'r'+i" :value="n" zone="red" />
        <Ball v-for="(n, i) in draw.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
      </view>
```
改为：
```html
      <view class="balls">
        <template v-for="(nums, key) in draw.numbers">
          <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" />
        </template>
      </view>
```

- [ ] **Step 4: build + 目测**

`npm run build:h5` 通过 → dev:h5。
Expected：ssq/dlt 当期/历史/详情红蓝球照旧；快乐8当期/历史/详情显示 20 个橙色号码球。

- [ ] **Step 5: 全量前端测试 + 提交**

Run: `npm test`
Expected: PASS（无单测覆盖模板，但确保既有不破）
```bash
git add lottery_frontend/src/pages/draw/latest.vue lottery_frontend/src/pages/draw/history.vue lottery_frontend/src/pages/draw/detail.vue
git commit -m "feat: 开奖展示页按 numbers entries 动态渲染"
```

---

## 计划自检

**1. Spec 覆盖（前端部分）：**
- generate 接 picks → Task 1 ✓
- 前端 zones 工具 + ballColor + selectionComplete → Task 2 ✓
- picker zones 动态 + 玩法 → Task 3 ✓
- stats zones 动态 → Task 4 ✓
- 展示页 zones 动态 → Task 5 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `getZones(ruleConfig)`(Task2) 被 picker/selectionComplete(Task2/3) 一致用；`zoneLabel`(Task2) 被 stats(Task4) 用。
- `generateNumbers(code,count,picks)`(Task1) 被 picker doGenerate 传 picksObj(Task3)；后端 generate 读 picks(Task1)。
- `selectionComplete(numbers,rule,picks)`(Task2) 被 picker canSaveManual 传 picksObj(Task3)。
- 机选 set 与手动 sel 均按 zone key 字典；展示页/picker 机选区按 numbers entries 遍历 zone=key；ballColor 认 main(Task2)。

**4. 注意点（给执行者）：**
- 目测需后端 8123（已 re-seed zones + kl8 100 期数据）。
- picker：可变区(kl8)显示玩法行，pickCount 默认 pick_min；切玩法重置该区已选与机选结果。
- 展示页 v-for over object（draw.numbers）：键顺序即插入顺序(red,blue 或 main)，无需 rule_config。
- ssq/dlt 经 getZones(老格式或新 zones 均可)渲染；本里程碑后前端恢复正常。
