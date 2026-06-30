<template>
  <view class="page" :style="themeVars">
    <TopBanner title="详情" :back="true" />
    <view v-if="guide" class="card">
      <text class="title">{{ guide.title }}</text>
      <rich-text class="content" :nodes="guide.content"></rich-text>
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { computed as __cmp } from 'vue'
import { themeState as __ts, themeVarString as __tvs } from '../../store/theme.js'
const themeVars = __cmp(() => { void __ts.key; return __tvs() })

import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { getGuideDetail } from '../../api/guide.js'

const guide = ref(null)
const emptyMsg = ref('加载中…')

onLoad(async (q) => {
  try {
    guide.value = await getGuideDetail(q.id)
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
})
</script>

<style scoped>
.card { background: var(--surface); margin: 20rpx; padding: 30rpx; border-radius: 16rpx; }
.title { font-size: 34rpx; font-weight: 600; color: var(--text); display: block; margin-bottom: 20rpx; }
.content { font-size: 30rpx; color: var(--text-2); line-height: 1.6; }
.empty { text-align: center; color: var(--text-3); padding: 80rpx 0; }
.page { background: var(--bg); min-height: 100vh; }
</style>
