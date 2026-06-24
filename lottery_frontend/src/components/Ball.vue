<template>
  <view class="ball" :style="{ backgroundColor: color }">
    <text class="num">{{ display }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { ballColor } from '../utils/format.js'

const props = defineProps({
  value: { type: [Number, String], required: true },
  zone: { type: String, default: 'red' },
  pad: { type: Number, default: 2 },
})

const color = computed(() => ballColor(props.zone))
const display = computed(() => String(props.value).padStart(props.pad, '0'))
</script>

<style scoped>
.ball {
  width: 60rpx; height: 60rpx; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  margin: 6rpx;
}
.num { color: #fff; font-size: 32rpx; font-weight: 600; }
</style>
