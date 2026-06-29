<template>
  <view class="card">
    <view class="head">
      <text class="issue">第 {{ draw.issue }} 期</text>
      <text class="date">{{ draw.draw_date }}</text>
    </view>
    <view class="balls">
      <template v-for="(nums, key) in draw.numbers">
        <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
      </template>
    </view>
    <view v-if="hasPool(draw.pool_amount)" class="pool">奖池：{{ formatAmount(draw.pool_amount) }} 元</view>
    <PrizeGrades :grades="draw.prize_grades" />
  </view>
</template>

<script setup>
import Ball from './Ball.vue'
import PrizeGrades from './PrizeGrades.vue'
import { formatAmount, hasPool } from '../utils/format.js'

defineProps({ draw: { type: Object, required: true } })
</script>

<style scoped>
.card { background: #fff; margin: 20rpx; padding: 30rpx; border-radius: 16rpx; }
.head { display: flex; justify-content: space-between; color: #888; font-size: 30rpx; }
.balls { display: flex; flex-wrap: wrap; margin: 24rpx 0; }
.pool { color: #e53935; font-size: 34rpx; margin-bottom: 16rpx; }
</style>
