<template>
  <view class="grid">
    <view
      v-for="c in cells"
      :key="c.number"
      class="cell"
      :style="{ backgroundColor: tierColor(c.count) }"
    >
      <text class="n">{{ String(c.number).padStart(2, '0') }}</text>
      <text class="meta">{{ c.count }}次</text>
      <text class="meta">遗漏{{ c.miss }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { statsTier } from '../utils/format.js'

const props = defineProps({
  cells: { type: Array, default: () => [] },
})

const max = computed(() => props.cells.reduce((m, c) => Math.max(m, c.count), 0))

const TIER_COLORS = ['#eeeeee', '#ffe0b2', '#ffb74d', '#fb8c00', '#e65100']
function tierColor(count) {
  return TIER_COLORS[statsTier(count, max.value)]
}
</script>

<style scoped>
.grid { display: flex; flex-wrap: wrap; padding: 16rpx; }
.cell {
  width: 96rpx; height: 96rpx; margin: 8rpx; border-radius: 10rpx;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.n { font-size: 26rpx; font-weight: 600; color: #333; }
.meta { font-size: 18rpx; color: #555; }
</style>
