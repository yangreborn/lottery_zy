<template>
  <view class="page">
    <TopBanner title="新增购买" :back="true" />
    <template v-if="zones.length">
      <view v-if="variableZone" class="play">
        <text class="pt">玩法（选几个）</text>
        <view class="play-opts">
          <view v-for="k in playOptions" :key="k" class="popt" :class="{ active: k === pickCount }" @click="setPick(k)"><text>选{{ k }}</text></view>
        </view>
      </view>
      <template v-if="digitZone">
        <view v-for="pos in digitZone.count" :key="pos" class="zone">
          <text class="zt">第 {{ pos }} 位（{{ digitAt(pos - 1) }}）</text>
          <view class="grid">
            <view v-for="d in digitRange" :key="d" class="dbtn" :class="{ active: digitAt(pos - 1) === d }" @click="setDigit(pos - 1, d)"><text>{{ d }}</text></view>
          </view>
        </view>
      </template>
      <template v-else>
        <view v-for="zone in zones" :key="zone.key" class="zone">
          <text class="zt">{{ zone.label }}（选 {{ targetOf(zone) }}）</text>
          <view class="grid">
            <BallSelectable v-for="n in rangeOf(zone)" :key="zone.key + n" :value="n" :zone="zone.key" :selected="(sel[zone.key] || []).includes(n)" @toggle="toggle(zone, $event)" />
          </view>
        </view>
      </template>
      <view class="fields">
        <input class="ipt" v-model="issue" placeholder="期号（必填）" />
        <input class="ipt" v-model.number="betCount" type="number" placeholder="注数(默认1)" />
        <picker mode="date" :value="purchaseDate" @change="onDate">
          <view class="ipt date">购买日期：{{ purchaseDate }}</view>
        </picker>
      </view>
      <view class="actions">
        <button class="btn save" :disabled="!canSave" @click="save">保存购买记录</button>
      </view>
    </template>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, purchaseCreate } from '../../api/user.js'
import { toggleBall, selectionComplete, digitsFilled } from '../../utils/picker.js'
import { getZones } from '../../utils/zones.js'
import { todayStr } from '../../utils/records.js'

const rule = ref(null)
const emptyMsg = ref('加载中…')
const code = lotteryStore.code
const issue = ref('')
const betCount = ref(1)
const purchaseDate = ref(todayStr())
const sel = reactive({})

const zones = computed(() => getZones(rule.value))
const variableZone = computed(() => zones.value.find((z) => z.pick_min !== undefined && z.pick_max !== undefined) || null)
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
const picksObj = computed(() => (variableZone.value ? { [variableZone.value.key]: pickCount.value } : {}))

function rangeOf(zone) { const arr = []; for (let i = zone.min; i <= zone.max; i++) arr.push(i); return arr }
function targetOf(zone) { if (zone.pick_min !== undefined && zone.pick_max !== undefined) return pickCount.value; return zone.count }
function toggle(zone, n) { sel[zone.key] = toggleBall(sel[zone.key] || [], n, targetOf(zone)) }
function setPick(k) { pickCount.value = k; if (variableZone.value) sel[variableZone.value.key] = [] }
function digitAt(i) { const a = digitZone.value ? sel[digitZone.value.key] : null; return a && a[i] !== null && a[i] !== undefined ? a[i] : '?' }
function setDigit(pos, d) { const key = digitZone.value.key; sel[key] = sel[key].map((v, i) => (i === pos ? d : v)) }
function onDate(e) { purchaseDate.value = e.detail.value }

const canSave = computed(() => {
  if (!rule.value || !issue.value.trim()) return false
  if (digitZone.value) return digitsFilled(sel[digitZone.value.key])
  return selectionComplete(sel, rule.value, picksObj.value)
})

async function save() {
  if (!canSave.value) return
  try {
    await ensureLogin()
    await purchaseCreate({ code, issue: issue.value.trim(), numbers: { ...sel }, bet_count: betCount.value || 1, purchase_date: purchaseDate.value })
    uni.showToast({ title: '已记录', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
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
.play { background: #fff; margin: 16rpx 20rpx 12rpx; padding: 16rpx 20rpx; border-radius: 12rpx; }
.pt { font-size: 28rpx; color: #888; }
.play-opts { display: flex; flex-wrap: wrap; margin-top: 10rpx; }
.popt { padding: 10rpx 22rpx; margin: 6rpx 14rpx 6rpx 0; background: #f5f5f5; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.popt.active { background: #fb8c00; color: #fff; }
.zone { background: #fff; margin: 16rpx 20rpx; padding: 20rpx; border-radius: 12rpx; }
.zt { font-size: 30rpx; color: #666; }
.grid { display: flex; flex-wrap: wrap; margin-top: 12rpx; }
.dbtn { width: 64rpx; height: 64rpx; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin: 8rpx; font-size: 32rpx; border: 2rpx solid #43a047; color: #43a047; }
.dbtn.active { background: #43a047; color: #fff; }
.fields { margin: 0 20rpx; }
.ipt { background: #fff; border-radius: 10rpx; padding: 18rpx; margin-top: 16rpx; font-size: 28rpx; }
.ipt.date { color: #555; }
.actions { padding: 24rpx 20rpx; }
.btn.save { width: 100%; background: #e53935; color: #fff; font-size: 30rpx; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
