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

// 颜色取自主题 --heat-0..4，切换主题自动跟随
function tierColor(count) {
  return `var(--heat-${statsTier(count, max.value)})`
}
</script>

<style scoped>
.grid { display: flex; flex-wrap: wrap; padding: 16rpx; }
.cell {
  width: 96rpx; height: 96rpx; margin: 8rpx; border-radius: 14rpx;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.n { font-size: 26rpx; font-weight: 700; color: var(--heat-text); font-variant-numeric: tabular-nums; }
.meta { font-size: 18rpx; color: var(--heat-meta); }
</style>
