<template>
  <view class="page">
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
        <view class="grade head-row">
          <text>奖级</text><text>中奖注数</text><text>单注奖金</text>
        </view>
        <view v-for="(g, i) in draw.prize_grades" :key="i" class="grade">
          <text>{{ g.level_label || g.level }}</text>
          <text>{{ g.count }}</text>
          <text>{{ formatAmount(g.amount) }}</text>
        </view>
      </view>
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import Ball from '../../components/Ball.vue'
import { getDetail } from '../../api/lottery.js'
import { formatAmount } from '../../utils/format.js'
import { reportAccess } from '../../utils/report.js'

const draw = ref(null)
const emptyMsg = ref('加载中…')

onLoad(async (q) => {
  reportAccess('draw/detail', { lottery_code: q.code })
  try {
    draw.value = await getDetail(q.code, q.issue)
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
})
</script>

<style scoped>
.card { background: #fff; margin: 20rpx; padding: 30rpx; border-radius: 16rpx; }
.head { display: flex; justify-content: space-between; color: #888; font-size: 26rpx; }
.balls { display: flex; flex-wrap: wrap; margin: 24rpx 0; }
.pool { color: #e53935; font-size: 28rpx; margin-bottom: 16rpx; }
.grades { border-top: 1px solid #f0f0f0; padding-top: 16rpx; }
.grade { display: flex; justify-content: space-between; padding: 10rpx 0; font-size: 26rpx; color: #555; }
.head-row { color: #999; font-weight: 600; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
