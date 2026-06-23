<template>
  <view class="page">
    <view v-if="guide" class="card">
      <text class="title">{{ guide.title }}</text>
      <rich-text class="content" :nodes="guide.content"></rich-text>
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getGuideDetail } from '../../api/guide.js'
import { reportAccess } from '../../utils/report.js'

const guide = ref(null)
const emptyMsg = ref('加载中…')

onLoad(async (q) => {
  reportAccess('guide/detail')
  try {
    guide.value = await getGuideDetail(q.id)
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
})
</script>

<style scoped>
.card { background: #fff; margin: 20rpx; padding: 30rpx; border-radius: 16rpx; }
.title { font-size: 32rpx; font-weight: 600; color: #333; display: block; margin-bottom: 20rpx; }
.content { font-size: 28rpx; color: #555; line-height: 1.6; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
