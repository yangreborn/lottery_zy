<template>
  <view class="page" :style="themeVars">
    <TopBanner title="通知" :back="true" />
    <view v-for="g in items" :key="g.id" class="row" @click="goDetail(g.id)">
      <text class="title">{{ g.title }}</text>
      <text class="tag">{{ g.type_label }}</text>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { computed as __cmp } from 'vue'
import { themeState as __ts, themeVarString as __tvs } from '../../store/theme.js'
const themeVars = __cmp(() => { void __ts.key; return __tvs() })

import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { getGuideList } from '../../api/guide.js'

const items = ref([])
const emptyMsg = ref('加载中…')

async function load() {
  emptyMsg.value = '加载中…'
  try {
    items.value = await getGuideList('', 'activity,notice')
    if (!items.value.length) emptyMsg.value = '暂无内容'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function goDetail(id) { uni.navigateTo({ url: `/pages/guide/detail?id=${id}` }) }

onShow(() => {
  load()
})
</script>

<style scoped>
.row { background: var(--surface); margin: 12rpx 20rpx; padding: 24rpx; border-radius: 12rpx; display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 34rpx; color: var(--text); }
.tag { font-size: 22rpx; color: var(--text-3); }
.empty { text-align: center; color: var(--text-3); padding: 80rpx 0; }
.page { background: var(--bg); min-height: 100vh; }
</style>
