<template>
  <view class="card">
    <view class="head">
      <view class="head-l">
        <text class="issue">第 {{ draw.issue }} 期</text>
      </view>
      <text class="date">{{ draw.draw_date }}</text>
    </view>
    <view class="balls">
      <template v-for="(nums, key) in draw.numbers">
        <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
      </template>
    </view>
    <!-- 折叠模式（首页）：奖池滚存并入展开区，默认隐藏；非折叠（详情）：直接展示 -->
    <view v-if="collapsible && (hasPrize || hasPool(draw.pool_amount))"
          class="prize-toggle" @click="showPrize = !showPrize">
      <text>{{ showPrize ? '收起奖级' : '展开奖级' }}</text>
      <text class="caret">{{ showPrize ? '▲' : '▼' }}</text>
    </view>
    <template v-if="!collapsible || showPrize">
      <view v-if="hasPool(draw.pool_amount)" class="pool">
        <text class="pool-lb">奖池滚存</text>
        <text class="pool-val">{{ formatAmount(draw.pool_amount) }} <text class="pool-unit">元</text></text>
      </view>
      <PrizeGrades :grades="draw.prize_grades" />
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import Ball from './Ball.vue'
import PrizeGrades from './PrizeGrades.vue'
import { formatAmount, hasPool } from '../utils/format.js'
import { normalizePrizes } from '../utils/prize.js'

const props = defineProps({
  draw: { type: Object, required: true },
  collapsible: { type: Boolean, default: false },
})
const showPrize = ref(false)
// 无有效奖级数据时（如福彩3D官方未回填）整块不显示，连"展开奖级"也不出现
const hasPrize = computed(() => {
  const d = normalizePrizes(props.draw.prize_grades)
  return d.grouped ? d.groups.some((g) => g.rows.length) : d.flat.length > 0
})
</script>

<style scoped>
.card {
  background: var(--surface); margin: 20rpx 24rpx; padding: 32rpx 32rpx 20rpx;
  border-radius: 28rpx; border: 1rpx solid var(--border);
  box-shadow: var(--shadow-card);
}
.head { display: flex; justify-content: space-between; align-items: center; }
.issue {
  color: var(--text); font-size: 30rpx; font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.date { color: var(--text-3); font-size: 25rpx; font-variant-numeric: tabular-nums; }
.balls { display: flex; flex-wrap: wrap; margin: 26rpx 0 6rpx; }

.pool {
  display: flex; align-items: baseline; gap: 12rpx;
  margin: 18rpx 0 4rpx; padding-top: 22rpx;
  border-top: 1rpx solid var(--border);
}
.pool-lb { color: var(--text-3); font-size: 24rpx; }
.pool-val {
  color: var(--brand); font-size: 34rpx; font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.pool-unit { color: var(--text-2); font-size: 22rpx; font-weight: 500; }

.prize-toggle {
  display: flex; align-items: center; justify-content: center; gap: 8rpx;
  margin-top: 16rpx; padding: 16rpx 0 4rpx;
  color: var(--brand); font-size: 27rpx; font-weight: 600;
  border-top: 1rpx solid var(--border);
}
.caret { font-size: 20rpx; }
</style>
