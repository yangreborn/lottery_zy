<template>
  <view class="top-banner">
    <view class="status-bar"></view>
    <view class="bar">
      <text v-if="back" class="tb-back" @click="goBack">‹ 返回</text>
      <text class="tb-title">{{ title }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  back: { type: Boolean, default: false },
})
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}
</script>

<style scoped>
.top-banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); }
.status-bar { height: var(--status-bar-height, 0px); }
.bar { position: relative; padding: 28rpx 0; text-align: center; }
.tb-back { position: absolute; left: 24rpx; top: 50%; transform: translateY(-50%); color: #fff; font-size: 30rpx; }
.tb-title { color: #fff; font-size: 34rpx; font-weight: 700; letter-spacing: 4rpx; }
</style>
