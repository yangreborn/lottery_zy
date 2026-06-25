<template>
  <view class="page">
    <TopBanner title="开奖海报" :back="true" />
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
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getHistory, getDetail } from '../../api/lottery.js'
import { POSTER_THEMES, buildPosterData, drawPoster } from '../../utils/poster.js'

const store = lotteryStore
const lotteries = ref([])
const issues = ref([])
const curIssue = ref('')
const themes = POSTER_THEMES
const themeKey = ref('red')
let posterData = null

function curTheme() { return themes.find((t) => t.key === themeKey.value) || themes[0] }
function curCategory() {
  const l = lotteries.value.find((x) => x.code === store.code)
  return l ? l.category : '福彩'
}
function curName() {
  const l = lotteries.value.find((x) => x.code === store.code)
  return l ? l.name : store.code
}

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
    posterData = buildPosterData(detail, curName(), curCategory())
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
  drawPoster(ctx, posterData, curTheme())
}

function save() {
  if (!curIssue.value) { uni.showToast({ title: '请先选择期次', icon: 'none' }); return }
  uni.canvasToTempFilePath({
    canvasId: 'poster',
    success: (r) => {
      uni.saveImageToPhotosAlbum({
        filePath: r.tempFilePath,
        success: () => uni.showToast({ title: '已保存到相册', icon: 'success' }),
        fail: () => uni.showToast({ title: '请在设置中开启相册权限', icon: 'none' }),
      })
    },
    fail: () => uni.showToast({ title: '请在微信小程序中保存', icon: 'none' }),
  })
}

function onChange(code) { setCode(code); loadIssues() }

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错 */ }
  }
  loadIssues()
})
</script>

<style scoped>
.issues { white-space: nowrap; padding: 16rpx 20rpx; }
.ichip { display: inline-block; padding: 10rpx 24rpx; margin-right: 14rpx; background: #fff; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.ichip.active { background: #e53935; color: #fff; }
.themes { display: flex; padding: 0 20rpx 12rpx; }
.tchip { padding: 10rpx 24rpx; margin-right: 14rpx; background: #fff; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.tchip.active { background: #fb8c00; color: #fff; }
.cvwrap { display: flex; justify-content: center; padding: 12rpx 0; }
.poster { width: 600rpx; height: 840rpx; background: #fff; }
.hint { text-align: center; color: #999; padding: 20rpx; font-size: 28rpx; }
.actions { padding: 24rpx 20rpx; }
.btn { width: 100%; background: #e53935; color: #fff; font-size: 30rpx; }
</style>
