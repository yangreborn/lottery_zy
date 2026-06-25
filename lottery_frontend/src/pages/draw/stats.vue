<template>
  <view class="page">
    <TopBanner title="号码统计" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
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
import LotteryTabs from '../../components/LotteryTabs.vue'
import Heatmap from '../../components/Heatmap.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getStats, getLotteryList } from '../../api/lottery.js'
import { sortCells } from '../../utils/statsort.js'
import { zoneLabel } from '../../utils/zones.js'

const store = lotteryStore
const lotteries = ref([])
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
    const res = await getStats(store.code, periods.value)
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

function onChange(code) { setCode(code); load() }

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞统计 */ }
  }
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
