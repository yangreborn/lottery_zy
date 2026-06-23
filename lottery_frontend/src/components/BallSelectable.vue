<template>
  <view
    class="sball"
    :style="selected ? { backgroundColor: color, color: '#fff' } : { borderColor: color, color: color }"
    @click="$emit('toggle', value)"
  >
    <text>{{ display }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { ballColor } from '../utils/format.js'

const props = defineProps({
  value: { type: Number, required: true },
  zone: { type: String, default: 'red' },
  selected: { type: Boolean, default: false },
})
defineEmits(['toggle'])

const color = computed(() => ballColor(props.zone))
const display = computed(() => String(props.value).padStart(2, '0'))
</script>

<style scoped>
.sball {
  width: 64rpx; height: 64rpx; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  margin: 8rpx; font-size: 32rpx; border: 2rpx solid transparent;
  background: #fff;
}
</style>
