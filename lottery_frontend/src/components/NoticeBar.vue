<template>
  <view v-if="notice" class="notice-bar" @click="$emit('tap')">
    <text class="ico">📢</text>
    <text class="txt">{{ notice.title }}</text>
    <text class="more">详情</text>
  </view>
</template>

<script setup>
defineProps({ notice: { type: Object, default: null } })
defineEmits(['tap'])
</script>

<style scoped>
.notice-bar { display: flex; align-items: center; background: #fff8e1; margin: 16rpx 20rpx 0; padding: 16rpx 20rpx; border-radius: 12rpx; }
.ico { font-size: 30rpx; margin-right: 12rpx; }
.txt { flex: 1; font-size: 28rpx; color: #8a6d3b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.more { font-size: 24rpx; color: #e53935; margin-left: 12rpx; }
</style>
