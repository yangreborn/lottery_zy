<template>
  <view v-if="notice" class="notice-bar" @click="$emit('tap')">
    <image class="ico" :src="bellIcon" mode="aspectFit" />
    <text class="txt">{{ notice.title }}</text>
    <text class="more">详情 ›</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { lineIcon } from '../utils/icons.js'
import { themeState, currentTheme } from '../store/theme.js'

defineProps({ notice: { type: Object, default: null } })
defineEmits(['tap'])

// 跟随主题品牌色
const bellIcon = computed(() => {
  void themeState.key
  return lineIcon('bell', currentTheme().vars['--brand'])
})
</script>

<style scoped>
.notice-bar {
  display: flex; align-items: center;
  background: var(--brand-soft-bg); border: 1rpx solid var(--brand-soft-border);
  margin: 20rpx 24rpx 0; padding: 18rpx 22rpx; border-radius: 18rpx;
}
.ico { width: 32rpx; height: 32rpx; margin-right: 14rpx; flex-shrink: 0; }
.txt {
  flex: 1; font-size: 27rpx; color: var(--brand-soft-text); font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.more { font-size: 24rpx; color: var(--brand); margin-left: 14rpx; flex-shrink: 0; }
</style>
