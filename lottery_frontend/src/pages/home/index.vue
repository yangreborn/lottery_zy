<template>
  <view class="home">
    <view class="banner"><text class="bt">彩票查询</text></view>
    <view class="grid">
      <view v-for="m in menu" :key="m.key" class="mcard" @click="go(m)">
        <text class="ic">{{ m.icon }}</text>
        <text class="tx">{{ m.title }}</text>
      </view>
    </view>
    <view class="footer">
      <view class="links">
        <text class="lk" @click="openDoc('agreement')">用户协议</text>
        <text class="sep">·</text>
        <text class="lk" @click="openDoc('privacy')">隐私协议</text>
      </view>
      <text class="src">数据来源：中国福彩网 cwl.gov.cn · 中国体彩网 sporttery.cn</text>
    </view>
  </view>
</template>

<script setup>
import { HOME_MENU, goMenu } from '../../utils/menu.js'

const menu = HOME_MENU
function go(m) { goMenu(m) }
function openDoc(type) { uni.navigateTo({ url: `/pages/legal/doc?type=${type}` }) }
</script>

<style scoped>
.home { min-height: 100vh; background: linear-gradient(180deg, #ffd9d4 0%, #fff0ee 35%, #fbfbfb 100%); }
.banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: 44rpx 0; text-align: center; }
.bt { color: #fff; font-size: 42rpx; font-weight: 700; letter-spacing: 8rpx; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24rpx; padding: 28rpx; }
.mcard { background: #fff; border-radius: 20rpx; padding: 44rpx 0; text-align: center; box-shadow: 0 4rpx 16rpx rgba(229, 57, 53, 0.10); }
.ic { font-size: 56rpx; display: block; }
.tx { font-size: 32rpx; font-weight: 600; color: #333; display: block; margin-top: 14rpx; }
.footer { padding: 20rpx 28rpx 40rpx; text-align: center; }
.links { margin-bottom: 12rpx; }
.lk { color: #e53935; font-size: 26rpx; }
.sep { color: #bbb; font-size: 26rpx; margin: 0 12rpx; }
.src { color: #999; font-size: 22rpx; display: block; line-height: 1.6; }
</style>
