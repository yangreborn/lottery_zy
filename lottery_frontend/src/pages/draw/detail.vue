<template>
  <view class="page">
    <TopBanner title="开奖详情" />
    <view v-if="draw" class="card">
      <view class="head">
        <text class="issue">第 {{ draw.issue }} 期</text>
        <text class="date">{{ draw.draw_date }}</text>
      </view>
      <view class="balls">
        <template v-for="(nums, key) in draw.numbers">
          <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
        </template>
      </view>
      <view class="pool">奖池：{{ formatAmount(draw.pool_amount) }} 元</view>
      <PrizeGrades :grades="draw.prize_grades" :area="draw.prize_area" />
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import Ball from '../../components/Ball.vue'
import PrizeGrades from '../../components/PrizeGrades.vue'
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
.head { display: flex; justify-content: space-between; color: #888; font-size: 30rpx; }
.balls { display: flex; flex-wrap: wrap; margin: 24rpx 0; }
.pool { color: #e53935; font-size: 34rpx; margin-bottom: 16rpx; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
