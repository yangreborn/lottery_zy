<template>
  <view class="page">
    <TopBanner title="开奖海报" :back="true" />

    <view class="modes">
      <view class="mode" :class="{ active: mode === 'single' }" @click="switchMode('single')"><text>单彩种</text></view>
      <view class="mode" :class="{ active: mode === 'merge' }" @click="switchMode('merge')"><text>合并海报</text></view>
    </view>

    <!-- 单彩种 -->
    <template v-if="mode === 'single'">
      <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
      <scroll-view scroll-x class="issues">
        <view
          v-for="it in issues" :key="it.issue"
          class="ichip" :class="{ active: it.issue === curIssue }"
          @click="chooseIssue(it)"
        ><text>{{ it.issue }}期</text></view>
      </scroll-view>
      <view class="themes">
        <view
          v-for="t in themes" :key="t.key"
          class="tchip" :class="{ active: t.key === themeKey }"
          @click="chooseTheme(t.key)"
        ><text>{{ t.label }}</text></view>
      </view>
      <view class="cvwrap">
        <canvas canvas-id="poster" class="poster"></canvas>
      </view>
      <view v-if="!curIssue" class="hint">请先选择期次</view>
      <view class="actions">
        <button class="btn" :disabled="!curIssue" @click="save">保存到相册</button>
      </view>
    </template>

    <!-- 合并海报 -->
    <template v-else>
      <view class="themes presets">
        <view
          v-for="p in presets" :key="p.key"
          class="tchip" :class="{ active: p.key === mergePreset }"
          @click="choosePreset(p.key)"
        ><text>{{ p.label }}</text></view>
      </view>
      <view v-if="mergePreset === 'custom'" class="picklist">
        <view
          v-for="l in lotteries" :key="l.code"
          class="pitem" :class="{ on: customCodes.includes(l.code) }"
          @click="toggleCustom(l.code)"
        >
          <text class="chk">{{ customCodes.includes(l.code) ? '✓' : '○' }}</text>
          <text class="pname">{{ l.name }}</text>
        </view>
      </view>
      <view class="themes">
        <view
          v-for="t in themes" :key="t.key"
          class="tchip" :class="{ active: t.key === themeKey }"
          @click="chooseMergeTheme(t.key)"
        ><text>{{ t.label }}</text></view>
      </view>
      <view class="cvwrap">
        <canvas canvas-id="mposter" class="poster" :style="{ width: '600rpx', height: mergeH + 'rpx' }"></canvas>
      </view>
      <view v-if="mergeLoading" class="hint">海报生成中…</view>
      <view v-else-if="!hasMerge" class="hint">{{ mergeHint }}</view>
      <view class="actions">
        <button class="btn" :disabled="!hasMerge" @click="saveMerge">保存到相册</button>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getHistory, getDetail, getLatest } from '../../api/lottery.js'
import {
  POSTER_THEMES, buildPosterData, drawPoster,
  MERGE_PRESETS, presetCodes, buildMergedPosterData, measureMerged, drawMergedPoster,
} from '../../utils/poster.js'

const store = lotteryStore
const lotteries = ref([])
const themes = POSTER_THEMES
const themeKey = ref('red')
const mode = ref('single')

// 单彩种
const issues = ref([])
const curIssue = ref('')
let posterData = null

// 合并
const presets = MERGE_PRESETS
const mergePreset = ref('fc')
const customCodes = ref([])
let mergeData = null
const mergeH = ref(840)
const mergeLoading = ref(false)
const hasMerge = ref(false)

const PRESET_TITLE = { fc: '福彩开奖', tc: '体彩开奖', custom: '开奖合辑' }
const mergeHint = computed(() =>
  mergePreset.value === 'custom' && !customCodes.value.length ? '请勾选要合并的彩种' : '暂无可用开奖数据'
)

function curTheme() { return themes.find((t) => t.key === themeKey.value) || themes[0] }
function curLottery() {
  return (
    lotteries.value.find((x) => x.code === store.code) ||
    { name: store.code, category: '福彩', rule_config: { zones: [] } }
  )
}

// ---- 单彩种 ----
async function loadIssues() {
  curIssue.value = ''
  posterData = null
  try {
    const res = await getHistory(store.code, { page: 1 })
    issues.value = res.results || []
  } catch (e) {
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

async function chooseIssue(it) {
  try {
    const detail = await getDetail(store.code, it.issue)
    posterData = buildPosterData(detail, curLottery())
    curIssue.value = it.issue
    redraw()
  } catch (e) {
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function chooseTheme(k) { themeKey.value = k; redraw() }

function redraw() {
  if (!posterData) return
  const ctx = uni.createCanvasContext('poster')
  const scale = uni.upx2px(600) / 600
  drawPoster(ctx, posterData, curTheme(), scale)
}

function save() {
  if (!curIssue.value) { uni.showToast({ title: '请先选择期次', icon: 'none' }); return }
  uni.canvasToTempFilePath({
    canvasId: 'poster',
    width: uni.upx2px(600),
    height: uni.upx2px(840),
    destWidth: 1200,
    destHeight: 1680,
    success: (r) => saveToAlbum(r.tempFilePath),
    fail: () => uni.showToast({ title: '请在微信小程序中保存', icon: 'none' }),
  })
}

function onChange(code) { setCode(code); loadIssues() }

// ---- 合并海报 ----
function lotteryOf(code) {
  return lotteries.value.find((x) => x.code === code) ||
    { name: code, category: '福彩', rule_config: { zones: [] } }
}

async function loadMerge() {
  const codes = presetCodes(mergePreset.value, lotteries.value, customCodes.value)
  if (!codes.length) { mergeData = null; hasMerge.value = false; return }
  mergeLoading.value = true
  hasMerge.value = false
  try {
    const items = []
    for (const code of codes) {
      try {
        const detail = await getLatest(code)
        if (detail && detail.issue) items.push({ detail, lottery: lotteryOf(code) })
      } catch (e) { /* 某彩种暂无开奖数据则跳过 */ }
    }
    mergeData = buildMergedPosterData(items, PRESET_TITLE[mergePreset.value] || '开奖合辑')
    if (!mergeData.entries.length) { hasMerge.value = false; return }
    mergeH.value = Math.round(measureMerged(mergeData).H)
    hasMerge.value = true
    // 等画布按新高度渲染后再绘制
    setTimeout(redrawMerge, 50)
  } finally {
    mergeLoading.value = false
  }
}

function redrawMerge() {
  if (!mergeData || !mergeData.entries.length) return
  const ctx = uni.createCanvasContext('mposter')
  const scale = uni.upx2px(600) / 600
  drawMergedPoster(ctx, mergeData, curTheme(), scale)
}

function choosePreset(k) { mergePreset.value = k; loadMerge() }
function chooseMergeTheme(k) { themeKey.value = k; redrawMerge() }
function toggleCustom(code) {
  customCodes.value = customCodes.value.includes(code)
    ? customCodes.value.filter((c) => c !== code)
    : [...customCodes.value, code]
  loadMerge()
}

function saveMerge() {
  if (!hasMerge.value) { uni.showToast({ title: '暂无可保存海报', icon: 'none' }); return }
  uni.canvasToTempFilePath({
    canvasId: 'mposter',
    width: uni.upx2px(600),
    height: uni.upx2px(mergeH.value),
    destWidth: 1200,
    destHeight: Math.round(mergeH.value * 2),
    success: (r) => saveToAlbum(r.tempFilePath),
    fail: () => uni.showToast({ title: '请在微信小程序中保存', icon: 'none' }),
  })
}

// ---- 公共 ----
function saveToAlbum(filePath) {
  uni.saveImageToPhotosAlbum({
    filePath,
    success: () => uni.showToast({ title: '已保存到相册', icon: 'success' }),
    fail: () => uni.showToast({ title: '请在设置中开启相册权限', icon: 'none' }),
  })
}

function switchMode(m) {
  if (mode.value === m) return
  mode.value = m
  if (m === 'merge') loadMerge()
  else setTimeout(redraw, 50)
}

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错 */ }
  }
  if (mode.value === 'single') loadIssues()
  else loadMerge()
})
</script>

<style scoped>
.modes { display: flex; margin: 16rpx 20rpx; background: #fff; border-radius: 12rpx; overflow: hidden; }
.mode { flex: 1; text-align: center; padding: 20rpx 0; color: #666; font-size: 30rpx; }
.mode.active { background: #e53935; color: #fff; font-weight: 600; }
.issues { white-space: nowrap; padding: 16rpx 20rpx; }
.ichip { display: inline-block; padding: 10rpx 24rpx; margin-right: 14rpx; background: #fff; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.ichip.active { background: #e53935; color: #fff; }
.themes { display: flex; flex-wrap: wrap; padding: 0 20rpx 12rpx; }
.themes.presets { padding-top: 12rpx; }
.tchip { padding: 10rpx 24rpx; margin: 0 14rpx 12rpx 0; background: #fff; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.tchip.active { background: #fb8c00; color: #fff; }
.picklist { background: #fff; margin: 0 20rpx 12rpx; border-radius: 12rpx; overflow: hidden; }
.pitem { display: flex; align-items: center; padding: 22rpx 24rpx; border-bottom: 1rpx solid #f3f3f3; }
.pitem:last-child { border-bottom: none; }
.pitem .chk { font-size: 34rpx; color: #e53935; width: 48rpx; }
.pitem.on .pname { color: #e53935; }
.pname { font-size: 30rpx; color: #333; }
.cvwrap { display: flex; justify-content: center; padding: 12rpx 0; }
.poster { width: 600rpx; height: 840rpx; background: #fff; }
.hint { text-align: center; color: #999; padding: 20rpx; font-size: 28rpx; }
.actions { padding: 24rpx 20rpx; }
.btn { width: 100%; background: #e53935; color: #fff; font-size: 30rpx; }
</style>
