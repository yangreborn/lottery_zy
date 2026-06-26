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
      <button class="zbtn" size="mini" @click="zoom(1)">－ 缩小</button>
      <button class="zbtn" size="mini" @click="zoom(-1)">＋ 放大</button>
      <text class="ztip">手指左右拖动查看更多期</text>
    </view>

    <view class="cvwrap">
      <canvas
        canvas-id="chart" class="chart"
        @touchstart="onTouchStart" @touchmove="onTouchMove"
      ></canvas>
    </view>

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
import { primaryZoneKey, sumSeries, missSeries, clampWindow, drawLineChart } from '../../utils/chart.js'

const CANVAS_W = 710 // 逻辑宽度(rpx)，固定屏宽，避免 canvas 放进 scroll-view 在小程序不显示
const CANVAS_H = 460

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

const zoneKey = ref('')
const number = ref(1)

// 可视窗口
const WINDOW_MIN = 6
const windowSize = ref(20)
const startIdx = ref(0)

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

const win = computed(() => clampWindow(series.value.length, startIdx.value, windowSize.value))
const windowed = computed(() => series.value.slice(win.value.start, win.value.start + win.value.size))

const curName = computed(() => {
  const l = lotteries.value.find((x) => x.code === store.code)
  return l ? l.name : store.code
})
const title = computed(() => {
  if (metric.value === 'sum') return `${curName.value} 和值走势（近${periods.value}期）`
  return `${curName.value} ${curZoneLabel.value}${pad(number.value)} 遗漏走势（近${periods.value}期）`
})

function redraw() {
  if (!windowed.value.length) return
  const ctx = uni.createCanvasContext('chart')
  const scale = uni.upx2px(CANVAS_W) / CANVAS_W
  drawLineChart(ctx, windowed.value, {
    width: CANVAS_W,
    height: CANVAS_H,
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
    resetWindow()
    setTimeout(redraw, 60)
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

// 默认窗口落在最新一段
function resetWindow() {
  const total = series.value.length
  windowSize.value = Math.min(total || WINDOW_MIN, 20)
  startIdx.value = Math.max(0, total - windowSize.value)
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
  resetWindow()
  setTimeout(redraw, 30)
}
function onZone(e) {
  const z = numberZones.value[Number(e.detail.value)]
  if (z) { zoneKey.value = z.key; number.value = z.min }
  resetWindow()
  setTimeout(redraw, 30)
}
function onNumber(e) {
  const z = curZone.value
  if (z) number.value = z.min + Number(e.detail.value)
  resetWindow()
  setTimeout(redraw, 30)
}
function zoom(dir) {
  // dir=-1 放大(看更少期、更稀疏)，dir=1 缩小(看更多期)
  const total = series.value.length
  let size = windowSize.value + dir * 6
  size = Math.max(WINDOW_MIN, Math.min(size, total || WINDOW_MIN))
  // 放大时尽量保持窗口右端（最新）不变
  const right = win.value.start + win.value.size
  windowSize.value = size
  startIdx.value = Math.max(0, right - size)
  setTimeout(redraw, 20)
}

// 拖动平移
let dragX = 0
let dragStart = 0
function onTouchStart(e) {
  const t = (e.touches && e.touches[0]) || (e.changedTouches && e.changedTouches[0])
  dragX = t ? t.clientX : 0
  dragStart = win.value.start
}
function onTouchMove(e) {
  const t = (e.touches && e.touches[0]) || (e.changedTouches && e.changedTouches[0])
  if (!t) return
  const dx = t.clientX - dragX
  // 每拖动一个点距(屏宽/窗口)移动一格；向右拖看更早的期
  const pxPerPoint = uni.upx2px(CANVAS_W) / Math.max(2, win.value.size)
  const shift = Math.round(-dx / pxPerPoint)
  startIdx.value = clampWindow(series.value.length, dragStart + shift, windowSize.value).start
  redraw()
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
.cvwrap { display: flex; justify-content: center; padding: 12rpx 0; }
.chart { width: 710rpx; height: 460rpx; background: #fff; border-radius: 12rpx; }
.empty { text-align: center; color: #999; padding: 60rpx 0; }
</style>
