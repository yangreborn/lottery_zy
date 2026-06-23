<template>
  <view class="top-banner"><text class="tb-title">{{ title }}</text></view>
</template>

<script setup>
defineProps({ title: { type: String, default: '' } })
</script>

<style scoped>
.top-banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: 28rpx 0; text-align: center; }
.tb-title { color: #fff; font-size: 34rpx; font-weight: 700; letter-spacing: 4rpx; }
</style>
