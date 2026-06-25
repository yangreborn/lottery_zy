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
        <view class="rand-tip">机选号码为系统纯随机生成，不含任何预测或分析成分</view>
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
.rand-tip { padding: 0 20rpx 10rpx; color: #999; font-size: 24rpx; }
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
