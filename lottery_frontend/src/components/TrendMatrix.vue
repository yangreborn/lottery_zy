<template>
  <scroll-view scroll-x scroll-y class="matrix">
    <view class="inner" :style="innerStyle">
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
import { computed } from 'vue'

const props = defineProps({
  matrix: { type: Object, default: () => ({ numbers: [], rows: [] }) },
  // ball: 命中显示球、缺失留白；miss: 缺失格显示遗漏期数
  mode: { type: String, default: 'ball' },
  // 传入主题色变量，如 'var(--ball-red)' / 'var(--ball-blue)'
  color: { type: String, default: 'var(--ball-red)' },
})
// 显式指定内容宽度：期号列 120rpx + 号码列数 × 56rpx（与 .mcell 宽度一致）。
// 否则小程序 scroll-view 测不出 inline-block 内 flex 行的真实宽度，横向滚动被截断
// （如快乐8 80 列只能滚到约 35 列）。
const CELL = 56
const ISSUE = 120
const innerStyle = computed(() => ({ width: ISSUE + (props.matrix.numbers || []).length * CELL + 'rpx' }))
function pad(n) { return String(n).padStart(2, '0') }
function shortIssue(s) { return String(s).slice(-5) }
</script>

<style scoped>
.matrix { width: 100%; height: 70vh; background: var(--surface); white-space: nowrap; }
.inner { display: inline-block; }
.mrow { display: flex; }
.mrow.header { position: sticky; top: 0; background: var(--trend-header-bg); z-index: 1; }
.mcell {
  width: 56rpx; height: 56rpx; flex: 0 0 56rpx;
  display: flex; align-items: center; justify-content: center;
  font-size: 22rpx; color: var(--text-3); border-bottom: 1rpx solid var(--grid-line);
}
.mcell.issue { width: 120rpx; flex: 0 0 120rpx; color: var(--text-2); font-size: 22rpx; font-variant-numeric: tabular-nums; }
.mcell.hcell { color: var(--text-3); font-weight: 600; }
.ball {
  width: 44rpx; height: 44rpx; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 22rpx; font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.miss { color: var(--matrix-miss); font-size: 22rpx; }
</style>
