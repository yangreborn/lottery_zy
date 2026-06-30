<template>
  <scroll-view scroll-y class="wrap">
    <view class="row header">
      <view class="issue">期号</view>
      <view v-for="(l, i) in data.labels" :key="i" class="seg">{{ l }}</view>
    </view>
    <view v-for="row in data.rows" :key="row.issue" class="row">
      <view class="issue">{{ shortIssue(row.issue) }}</view>
      <view v-for="(c, i) in row.counts" :key="i" class="seg">
        <view class="bar" :style="{ width: barW(c) }"></view>
        <text class="cnt">{{ c }}</text>
      </view>
    </view>
  </scroll-view>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, default: () => ({ labels: [], rows: [] }) },
})
function shortIssue(s) { return String(s).slice(-5) }
function maxCount() {
  let m = 1
  for (const r of props.data.rows) for (const c of r.counts) if (c > m) m = c
  return m
}
function barW(c) { return Math.round((c / maxCount()) * 100) + '%' }
</script>

<style scoped>
.wrap { width: 100%; height: 70vh; background: var(--surface); }
.row { display: flex; align-items: stretch; border-bottom: 1rpx solid var(--grid-line); }
.row.header { background: var(--trend-header-bg); }
.row.header .seg { color: var(--text-3); font-weight: 600; justify-content: center; }
.issue { flex: 0 0 130rpx; display: flex; align-items: center; padding-left: 16rpx; color: var(--text-2); font-size: 24rpx; font-variant-numeric: tabular-nums; }
.seg { flex: 1; position: relative; display: flex; align-items: center; padding: 16rpx 12rpx; font-size: 24rpx; }
.bar { position: absolute; left: 0; top: 50%; transform: translateY(-50%); height: 60%; background: var(--trend-bar); border-radius: 6rpx; }
.cnt { position: relative; color: var(--trend-bar-text); font-weight: 600; font-variant-numeric: tabular-nums; }
</style>
