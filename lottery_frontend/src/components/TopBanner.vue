<template>
  <view class="top-banner">
    <view class="status-bar"></view>
    <view class="bar">
      <text v-if="back" class="tb-back" @click="goBack">‹ 返回</text>
      <!-- #ifdef H5 -->
      <text v-else-if="homeBack" class="tb-back" @click="goHome">‹ 首页</text>
      <!-- #endif -->
      <text class="tb-title">{{ title }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  back: { type: Boolean, default: false },
  // homeBack: 仅 H5 渲染，给 tab 页(统计/选号)在 PC 网页上补一个返回首页入口
  homeBack: { type: Boolean, default: false },
})
function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) uni.navigateBack()
  else uni.switchTab({ url: '/pages/home/index' })
}
function goHome() {
  uni.switchTab({ url: '/pages/home/index' })
}
</script>

<style scoped>
.top-banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); }
.status-bar { height: var(--status-bar-height, 0px); }
.bar { position: relative; padding: 28rpx 0; text-align: center; }
.tb-back { position: absolute; left: 24rpx; top: 50%; transform: translateY(-50%); color: #fff; font-size: 30rpx; }
.tb-title { color: #fff; font-size: 34rpx; font-weight: 700; letter-spacing: 4rpx; }
</style>
