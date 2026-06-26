<template>
  <view class="page">
    <TopBanner title="走势折线图" :back="true" :home-back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />

    <view class="opts">
      <view
        v-for="p in periodOptions" :key="p"
        class="opt" :class="{ active: p === periods }" @click="choosePeriod(p)"
      ><text>近{{ p }}期</text></view>
    </view>

    <view class="opts">
      <view
        v-for="m in metricOptions" :key="m.key"
        class="opt" :class="{ active: m.key === metric }" @click="chooseMetric(m.key)"
      ><text>{{ m.label }}</text></view>
    </view>

    <view v-if="metric === 'miss'" class="pickers">
      <picker v-if="numberZones.length > 1" mode="selector" :range="zoneLabels" @change="onZone">
        <view class="pk">区域：{{ curZoneLabel }} ▾</view>
      </picker>
      <picker mode="selector" :range="numberRange" @change="onNumber">
        <view class="pk">号码：{{ pad(number) }} ▾</view>
      </picker>
    </view>

    <view class="zoom">
      <button class="zbtn" size="mini" @click="zoom(-1)">－ 缩小</button>
      <button class="zbtn" size="mini" @click="zoom(1)">＋ 放大</button>
      <text class="ztip">左右滑动查看</text>
    </view>

    <scroll-view scroll-x class="cvscroll">
      <canvas canvas-id="chart" class="chart" :style="{ width: canvasW + 'rpx' }"></canvas>
    </scroll-view>

    <view v-if="!series.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getHistory } from '../../api/lottery.js'
import { primaryZoneKey, sumSeries, missSeries, chartWidth, drawLineChart } from '../../utils/chart.js'

const store = lotteryStore
const lotteries = ref([])
const draws = ref([])
const rule = ref(null)
const emptyMsg = ref('加载中…')

const periodOptions = [10, 30, 50, 100]
const periods = ref(30)
const metricOptions = [
  { key: 'sum', label: '和值走势' },
  { key: 'miss', label: '单号遗漏' },
]
const metric = ref('sum')

const SPACING_MIN = 28
const SPACING_MAX = 160
const spacing = ref(60)

const zoneKey = ref('')
const number = ref(1)

const numberZones = computed(() => ((rule.value && rule.value.zones) || []).filter((z) => z.min !== undefined && z.max !== undefined))
const zoneLabels = computed(() => numberZones.value.map((z) => z.label || z.key))
const curZone = computed(() => numberZones.value.find((z) => z.key === zoneKey.value) || numberZones.value[0] || null)
const curZoneLabel = computed(() => (curZone.value ? curZone.value.label || curZone.value.key : ''))
const numberRange = computed(() => {
  const z = curZone.value
  if (!z) return []
  const arr = []
  for (let i = z.min; i <= z.max; i++) arr.push(pad(i))
  return arr
})

function pad(n) { return String(n).padStart(2, '0') }

const series = computed(() => {
  if (!draws.value.length) return []
  if (metric.value === 'sum') return sumSeries(draws.value, primaryZoneKey(rule.value))
  if (!zoneKey.value) return []
  return missSeries(draws.value, zoneKey.value, number.value)
})

const canvasW = computed(() => Math.round(chartWidth(series.value.length, spacing.value)))

const curName = computed(() => {
  const l = lotteries.value.find((x) => x.code === store.code)
  return l ? l.name : store.code
})
const title = computed(() => {
  if (metric.value === 'sum') return `${curName.value} 和值走势（近${periods.value}期）`
  return `${curName.value} ${curZoneLabel.value}${pad(number.value)} 遗漏走势（近${periods.value}期）`
})

function redraw() {
  if (!series.value.length) return
  const ctx = uni.createCanvasContext('chart')
  const scale = uni.upx2px(100) / 100
  drawLineChart(ctx, series.value, {
    height: 460,
    spacing: spacing.value,
    color: metric.value === 'sum' ? '#e53935' : '#1e88e5',
    title: title.value,
  }, scale)
}

async function load() {
  emptyMsg.value = '加载中…'
  try {
    const found = lotteries.value.find((l) => l.code === store.code)
    rule.value = found ? found.rule_config : null
    if (metric.value === 'miss') ensureNumberDefault()
    const res = await getHistory(store.code, { page: 1, page_size: periods.value })
    draws.value = res.results || []
    if (!draws.value.length) emptyMsg.value = '暂无数据'
    setTimeout(redraw, 50)
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function ensureNumberDefault() {
  if (!numberZones.value.length) return
  if (!curZone.value) zoneKey.value = numberZones.value[0].key
  const z = curZone.value
  if (z && (number.value < z.min || number.value > z.max)) number.value = z.min
}

function choosePeriod(p) { periods.value = p; load() }
function chooseMetric(k) {
  metric.value = k
  if (k === 'miss') ensureNumberDefault()
  setTimeout(redraw, 30)
}
function onZone(e) {
  const z = numberZones.value[Number(e.detail.value)]
  if (z) { zoneKey.value = z.key; number.value = z.min }
  setTimeout(redraw, 30)
}
function onNumber(e) {
  const z = curZone.value
  if (z) number.value = z.min + Number(e.detail.value)
  setTimeout(redraw, 30)
}
function zoom(dir) {
  const next = spacing.value + dir * 24
  spacing.value = Math.max(SPACING_MIN, Math.min(SPACING_MAX, next))
  setTimeout(redraw, 30)
}

function onChange(code) { setCode(code); load() }

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错 */ }
  }
  load()
})
</script>

<style scoped>
.opts { display: flex; flex-wrap: wrap; padding: 10rpx 20rpx 0; }
.opt { padding: 12rpx 24rpx; margin: 6rpx 16rpx 6rpx 0; background: #fff; border-radius: 30rpx; color: #666; font-size: 30rpx; }
.opt.active { background: #e53935; color: #fff; }
.pickers { display: flex; padding: 12rpx 20rpx 0; }
.pk { background: #fff; border-radius: 30rpx; padding: 12rpx 24rpx; margin-right: 16rpx; color: #333; font-size: 28rpx; }
.zoom { display: flex; align-items: center; padding: 16rpx 20rpx; }
.zbtn { background: #fff; color: #1e88e5; border: 1rpx solid #1e88e5; margin-right: 16rpx; }
.ztip { color: #999; font-size: 24rpx; }
.cvscroll { white-space: nowrap; width: 100%; }
.chart { height: 460rpx; background: #fff; display: inline-block; }
.empty { text-align: center; color: #999; padding: 60rpx 0; }
</style>
