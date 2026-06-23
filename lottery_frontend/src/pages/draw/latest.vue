<template>
  <view class="page">
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view v-if="draw" class="card">
      <view class="head">
        <text class="issue">第 {{ draw.issue }} 期</text>
        <text class="date">{{ draw.draw_date }}</text>
      </view>
      <view class="balls">
        <Ball v-for="(n, i) in draw.numbers.red" :key="'r'+i" :value="n" zone="red" />
        <Ball v-for="(n, i) in draw.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
      </view>
      <view class="pool">奖池：{{ formatAmount(draw.pool_amount) }} 元</view>
      <view class="grades">
        <view v-for="(g, i) in draw.prize_grades" :key="i" class="grade">
          <text>{{ g.level_label || g.level }}</text>
          <text>{{ g.count }} 注</text>
          <text>{{ formatAmount(g.amount) }} 元</text>
        </view>
      </view>
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getLatest } from '../../api/lottery.js'
import { formatAmount } from '../../utils/format.js'
import { reportAccess } from '../../utils/report.js'

const store = lotteryStore
const lotteries = ref([])
const draw = ref(null)
const emptyMsg = ref('加载中…')

async function load() {
  draw.value = null
  emptyMsg.value = '加载中…'
  try {
    draw.value = await getLatest(store.code)
  } catch (e) {
    emptyMsg.value = e.msg || '暂无数据'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) {
  setCode(code)
  load()
}

onMounted(async () => {
  try {
    lotteries.value = await getLotteryList()
  } catch (e) {
    uni.showToast({ title: e.msg || '彩种加载失败', icon: 'none' })
  }
})
onShow(() => { reportAccess('draw/latest', { lottery_code: lotteryStore.code }); load() })
</script>

<style scoped>
.page { padding: 0 0 30rpx; }
.card { background: #fff; margin: 20rpx; padding: 30rpx; border-radius: 16rpx; }
.head { display: flex; justify-content: space-between; color: #888; font-size: 26rpx; }
.balls { display: flex; flex-wrap: wrap; margin: 24rpx 0; }
.pool { color: #e53935; font-size: 28rpx; margin-bottom: 16rpx; }
.grades { border-top: 1px solid #f0f0f0; padding-top: 16rpx; }
.grade { display: flex; justify-content: space-between; padding: 10rpx 0; font-size: 26rpx; color: #555; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
