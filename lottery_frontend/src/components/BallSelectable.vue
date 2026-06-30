<template>
  <view
    class="sball"
    :style="style"
    @click="$emit('toggle', value)"
  >
    <text>{{ display }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: { type: Number, required: true },
  zone: { type: String, default: 'red' },
  selected: { type: Boolean, default: false },
})
defineEmits(['toggle'])

// 颜色取自主题（--pick-red / --pick-blue），其它分区回退到红
const colorVar = computed(() => (props.zone === 'blue' ? 'var(--pick-blue)' : 'var(--pick-red)'))
const style = computed(() =>
  props.selected
    ? { background: colorVar.value, color: '#fff', borderColor: colorVar.value }
    : { background: 'var(--surface)', color: colorVar.value, borderColor: colorVar.value }
)
const display = computed(() => String(props.value).padStart(2, '0'))
</script>

<style scoped>
.sball {
  width: 64rpx; height: 64rpx; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  margin: 8rpx; font-size: 32rpx; font-weight: 700;
  font-variant-numeric: tabular-nums;
  border: 2rpx solid transparent;
}
</style>
