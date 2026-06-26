<template>
  <view class="page">
    <TopBanner title="走势图" :back="true" :home-back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />

    <scroll-view scroll-x class="typebar">
      <view
        v-for="t in visibleTypes" :key="t.key"
        class="ty" :class="{ active: t.key === chartType }" @click="chooseType(t.key)"
      ><text>{{ t.label }}</text></view>
    </scroll-view>

    <view class="opts">
      <view
        v-for="p in periodOptions" :key="p"
        class="opt" :class="{ active: p === periods }" @click="choosePeriod(p)"
      ><text>近{{ p }}期</text></view>
    </view>

    <view v-if="needZone || needNumber" class="pickers">
      <picker v-if="needZone && numberZones.length > 1" mode="selector" :range="zoneLabels" @change="onZone">
        <view class="pk">区域：{{ curZoneLabel }} ▾</view>
      </picker>
      <picker v-if="needNumber" mode="selector" :range="numberRange" @change="onNumber">
        <view class="pk">号码：{{ pad(number) }} ▾</view>
      </picker>
    </view>

    <!-- 矩阵：号码/遗漏走势 -->
    <TrendMatrix
      v-if="isMatrix && draws.length"
      :matrix="matrixData" :mode="chartType === 'miss' ? 'miss' : 'ball'" :color="zoneColor"
    />

    <!-- 区间走势 -->
    <IntervalTrend v-else-if="chartType === 'interval' && draws.length" :data="intervalData" />

    <!-- 折线：和值/跨度/单号遗漏 -->
    <template v-else-if="isLine">
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
    </template>

    <view v-if="!draws.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import TrendMatrix from '../../components/TrendMatrix.vue'
import IntervalTrend from '../../components/IntervalTrend.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getHistory } from '../../api/lottery.js'
import { primaryZoneKey, sumSeries, missSeries, clampWindow, drawLineChart } from '../../utils/chart.js'
import { isDigitGame, numberMatrix, intervalTrend, spanSeries } from '../../utils/trend.js'
import { ballColor } from '../../utils/format.js'

const CANVAS_W = 710
const CANVAS_H = 460

const store = lotteryStore
const lotteries = ref([])
const draws = ref([])
const rule = ref(null)
const emptyMsg = ref('加载中…')

const periodOptions = [10, 30, 50, 100]
const periods = ref(30)

const ALL_TYPES = [
  { key: 'num', label: '号码走势' },
  { key: 'miss', label: '遗漏走势' },
  { key: 'interval', label: '区间走势' },
  { key: 'sum', label: '和值走势' },
  { key: 'span', label: '跨度走势', digitOnly: true },
  { key: 'single', label: '单号遗漏' },
]
const chartType = ref('num')
const visibleTypes = computed(() => ALL_TYPES.filter((t) => !t.digitOnly || isDigitGame(rule.value)))

const isMatrix = computed(() => chartType.value === 'num' || chartType.value === 'miss')
const isLine = computed(() => ['sum', 'span', 'single'].includes(chartType.value))
const needZone = computed(() => ['num', 'miss', 'interval', 'single'].includes(chartType.value))
const needNumber = computed(() => chartType.value === 'single')

const zoneKey = ref('')
const number = ref(1)

const numberZones = computed(() => ((rule.value && rule.value.zones) || []).filter((z) => z.min !== undefined && z.max !== undefined))
const zoneLabels = computed(() => numberZones.value.map((z) => z.label || z.key))
const curZone = computed(() => numberZones.value.find((z) => z.key === zoneKey.value) || numberZones.value[0] || null)
const curZoneLabel = computed(() => (curZone.value ? curZone.value.label || curZone.value.key : ''))
const zoneColor = computed(() => (curZone.value ? curZone.value.color || ballColor(curZone.value.key) : '#e53935'))
const numberRange = computed(() => {
  const z = curZone.value
  if (!z) return []
  const arr = []
  for (let i = z.min; i <= z.max; i++) arr.push(pad(i))
  return arr
})

function pad(n) { return String(n).padStart(2, '0') }

// 矩阵 / 区间数据
const matrixData = computed(() => {
  const z = curZone.value
  if (!z) return { numbers: [], rows: [] }
  return numberMatrix(draws.value, z.key, z.min, z.max)
})
const intervalData = computed(() => {
  const z = curZone.value
  if (!z) return { labels: [], rows: [] }
  return intervalTrend(draws.value, z.key, z.min, z.max, 3)
})

// 折线数据
const lineSeries = computed(() => {
  if (!draws.value.length) return []
  if (chartType.value === 'sum') return sumSeries(draws.value, primaryZoneKey(rule.value))
  if (chartType.value === 'span') return spanSeries(draws.value, primaryZoneKey(rule.value))
  if (chartType.value === 'single' && zoneKey.value) return missSeries(draws.value, zoneKey.value, number.value)
  return []
})

// 折线可视窗口
const WINDOW_MIN = 6
const windowSize = ref(20)
const startIdx = ref(0)
const win = computed(() => clampWindow(lineSeries.value.length, startIdx.value, windowSize.value))
const windowed = computed(() => lineSeries.value.slice(win.value.start, win.value.start + win.value.size))

const curName = computed(() => {
  const l = lotteries.value.find((x) => x.code === store.code)
  return l ? l.name : store.code
})
const lineTitle = computed(() => {
  if (chartType.value === 'sum') return `${curName.value} 和值走势（近${periods.value}期）`
  if (chartType.value === 'span') return `${curName.value} 跨度走势（近${periods.value}期）`
  return `${curName.value} ${curZoneLabel.value}${pad(number.value)} 遗漏走势（近${periods.value}期）`
})

function redraw() {
  if (!isLine.value || !windowed.value.length) return
  const ctx = uni.createCanvasContext('chart')
  const scale = uni.upx2px(CANVAS_W) / CANVAS_W
  drawLineChart(ctx, windowed.value, {
    width: CANVAS_W,
    height: CANVAS_H,
    color: chartType.value === 'single' ? '#1e88e5' : '#e53935',
    title: lineTitle.value,
  }, scale)
}

async function load() {
  emptyMsg.value = '加载中…'
  try {
    const found = lotteries.value.find((l) => l.code === store.code)
    rule.value = found ? found.rule_config : null
    ensureZoneDefault()
    if (needNumber.value) ensureNumberDefault()
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

function ensureZoneDefault() {
  if (!numberZones.value.length) { zoneKey.value = ''; return }
  if (!numberZones.value.some((z) => z.key === zoneKey.value)) zoneKey.value = numberZones.value[0].key
}
function ensureNumberDefault() {
  const z = curZone.value
  if (z && (number.value < z.min || number.value > z.max)) number.value = z.min
}
function resetWindow() {
  const total = lineSeries.value.length
  windowSize.value = Math.min(total || WINDOW_MIN, 20)
  startIdx.value = Math.max(0, total - windowSize.value)
}

function chooseType(k) {
  chartType.value = k
  if (needNumber.value) ensureNumberDefault()
  resetWindow()
  setTimeout(redraw, 40)
}
function choosePeriod(p) { periods.value = p; load() }
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
  const total = lineSeries.value.length
  let size = windowSize.value + dir * 6
  size = Math.max(WINDOW_MIN, Math.min(size, total || WINDOW_MIN))
  const right = win.value.start + win.value.size
  windowSize.value = size
  startIdx.value = Math.max(0, right - size)
  setTimeout(redraw, 20)
}

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
  const pxPerPoint = uni.upx2px(CANVAS_W) / Math.max(2, win.value.size)
  const shift = Math.round(-dx / pxPerPoint)
  startIdx.value = clampWindow(lineSeries.value.length, dragStart + shift, windowSize.value).start
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
.typebar { white-space: nowrap; padding: 12rpx 20rpx 0; }
.ty { display: inline-block; padding: 12rpx 26rpx; margin-right: 14rpx; background: #fff; border-radius: 30rpx; color: #666; font-size: 28rpx; }
.ty.active { background: #e53935; color: #fff; }
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
