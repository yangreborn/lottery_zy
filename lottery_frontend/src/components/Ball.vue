<template>
  <view class="ball" :style="ballStyle">
    <text class="num">{{ display }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: [Number, String], required: true },
  zone: { type: String, default: 'red' },
  pad: { type: Number, default: 2 },
})

// 颜色取自当前主题的 CSS 变量（--ball-<zone> / --ball-glow-<zone>），
// 未知分区回退到 default，切换主题时球自动跟着变。
const ballStyle = computed(() => {
  const z = props.zone || 'default'
  return {
    background: `var(--ball-${z}, var(--ball-default))`,
    boxShadow: `var(--ball-glow-${z}, var(--ball-glow-default)), inset 0 -4rpx 6rpx rgba(0,0,0,0.22), inset 0 3rpx 5rpx rgba(255,255,255,0.4)`,
  }
})
const display = computed(() => String(props.value).padStart(props.pad, '0'))
</script>

<style scoped>
.ball {
  width: 64rpx; height: 64rpx; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  margin: 6rpx;
}
.num {
  color: #fff; font-size: 30rpx; font-weight: 700;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 1rpx 2rpx rgba(0, 0, 0, 0.25);
}
</style>
