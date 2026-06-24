<template>
  <view class="page">
    <TopBanner title="历史开奖" />
    <LotteryTabs :list="lotteries" :active="lotteryStore.code" @change="onChange" />
    <scroll-view scroll-y class="list" @scrolltolower="loadMore">
      <view
        v-for="d in items"
        :key="d.issue"
        class="row"
        @click="goDetail(d.issue)"
      >
        <view class="row-top">
          <text class="issue">第 {{ d.issue }} 期</text>
          <text class="date">{{ d.draw_date }}</text>
        </view>
        <view class="balls">
          <template v-for="(nums, key) in d.numbers">
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
          </template>
        </view>
      </view>
      <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
      <view v-else-if="!hasMore" class="end">没有更多了</view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import Ball from '../../components/Ball.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getHistory, getLotteryList } from '../../api/lottery.js'
import { reportAccess } from '../../utils/report.js'

const lotteries = ref([])
const items = ref([])
const page = ref(1)
const hasMore = ref(true)
const loading = ref(false)
const emptyMsg = ref('加载中…')
let loadedCode = ''

async function fetchPage(reset) {
  if (loading.value) return
  loading.value = true
  if (reset) { page.value = 1; items.value = []; hasMore.value = true }
  else { page.value += 1 }
  try {
    const res = await getHistory(lotteryStore.code, { page: page.value })
    const list = res.results || []
    items.value = items.value.concat(list)
    hasMore.value = items.value.length < (res.total || 0)
    if (!items.value.length) emptyMsg.value = '暂无数据'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

function onChange(code) {
  setCode(code)
  loadedCode = code
  fetchPage(true)
}

function loadMore() {
  if (!hasMore.value) return
  fetchPage(false)
}

function goDetail(issue) {
  uni.navigateTo({ url: `/pages/draw/detail?code=${lotteryStore.code}&issue=${issue}` })
}

onShow(() => {
  if (!lotteries.value.length) {
    getLotteryList().then((l) => { lotteries.value = l }).catch(() => {})
  }
  reportAccess('draw/history', { lottery_code: lotteryStore.code })
  if (loadedCode !== lotteryStore.code) {
    loadedCode = lotteryStore.code
    fetchPage(true)
  }
})
</script>

<style scoped>
.page { height: 100vh; }
.list { height: 100vh; }
.row { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.row-top { display: flex; justify-content: space-between; color: #888; font-size: 30rpx; }
.balls { display: flex; flex-wrap: wrap; margin-top: 14rpx; }
.empty, .end { text-align: center; color: #999; padding: 40rpx 0; font-size: 30rpx; }
</style>
