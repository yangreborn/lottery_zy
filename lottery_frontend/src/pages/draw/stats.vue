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
    <view class="zone-title">红球</view>
    <Heatmap :cells="redSorted" />
    <view class="zone-title">蓝球</view>
    <Heatmap :cells="blueSorted" />
    <view v-if="!redCells.length" class="empty">{{ emptyMsg }}</view>
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

const periodOptions = [10, 30, 50, 100]
const periods = ref(30)
const sortOptions = [
  { key: 'number', label: '号码顺序' },
  { key: 'most', label: '出现最多' },
  { key: 'least', label: '出现最少' },
]
const sortMode = ref('number')
const redCells = ref([])
const blueCells = ref([])
const emptyMsg = ref('加载中…')

const redSorted = computed(() => sortCells(redCells.value, sortMode.value))
const blueSorted = computed(() => sortCells(blueCells.value, sortMode.value))

async function load() {
  try {
    const res = await getStats(lotteryStore.code, periods.value)
    redCells.value = res.red || []
    blueCells.value = res.blue || []
    if (!redCells.value.length) emptyMsg.value = '暂无数据'
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
