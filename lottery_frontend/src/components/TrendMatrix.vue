<template>
  <scroll-view scroll-x scroll-y class="matrix">
    <view class="inner">
      <view class="mrow header">
        <view class="mcell issue">期号</view>
        <view v-for="n in matrix.numbers" :key="n" class="mcell hcell">{{ pad(n) }}</view>
      </view>
      <view v-for="row in matrix.rows" :key="row.issue" class="mrow">
        <view class="mcell issue">{{ shortIssue(row.issue) }}</view>
        <view v-for="cell in row.cells" :key="cell.num" class="mcell">
          <view v-if="cell.hit" class="ball" :style="{ background: color }">{{ pad(cell.num) }}</view>
          <text v-else class="miss">{{ mode === 'miss' ? cell.miss : '' }}</text>
        </view>
      </view>
    </view>
  </scroll-view>
</template>

<script setup>
defineProps({
  matrix: { type: Object, default: () => ({ numbers: [], rows: [] }) },
  // ball: 命中显示球、缺失留白；miss: 缺失格显示遗漏期数
  mode: { type: String, default: 'ball' },
  color: { type: String, default: '#e53935' },
})
function pad(n) { return String(n).padStart(2, '0') }
function shortIssue(s) { return String(s).slice(-5) }
</script>

<style scoped>
.matrix { width: 100%; height: 70vh; background: #fff; white-space: nowrap; }
.inner { display: inline-block; }
.mrow { display: flex; }
.mrow.header { position: sticky; top: 0; background: #fafafa; z-index: 1; }
.mcell {
  width: 56rpx; height: 56rpx; flex: 0 0 56rpx;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; color: #bbb; border-bottom: 1rpx solid #f2f2f2;
}
.mcell.issue { width: 120rpx; flex: 0 0 120rpx; color: #666; font-size: 22rpx; }
.mcell.hcell { color: #888; font-weight: 600; }
.ball {
  width: 44rpx; height: 44rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 22rpx;
}
.miss { color: #ccc; font-size: 22rpx; }
</style>
