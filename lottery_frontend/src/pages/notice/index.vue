<template>
  <view class="page">
    <TopBanner title="通知活动" :back="true" />
    <view class="types">
      <view
        v-for="t in types" :key="t.key"
        class="type" :class="{ active: t.key === curType }"
        @click="chooseType(t.key)"
      >
        <text>{{ t.label }}</text>
      </view>
    </view>
    <view v-for="g in items" :key="g.id" class="row" @click="goDetail(g.id)">
      <text class="title">{{ g.title }}</text>
      <text class="tag">{{ g.type_label }}</text>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { getGuideList } from '../../api/guide.js'
import { reportAccess } from '../../utils/report.js'

const items = ref([])
const emptyMsg = ref('加载中…')
const types = [
  { key: 'activity,notice', label: '全部' },
  { key: 'activity', label: '活动' },
  { key: 'notice', label: '通知' },
]
const curType = ref('activity,notice')

async function load() {
  emptyMsg.value = '加载中…'
  try {
    items.value = await getGuideList('', curType.value)
    if (!items.value.length) emptyMsg.value = '暂无内容'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function chooseType(k) { curType.value = k; load() }
function goDetail(id) { uni.navigateTo({ url: `/pages/guide/detail?id=${id}` }) }

onShow(() => {
  reportAccess('notice/index', {})
  load()
})
</script>

<style scoped>
.types { display: flex; padding: 16rpx 20rpx; }
.type { padding: 10rpx 24rpx; margin-right: 14rpx; background: #fff; border-radius: 30rpx; color: #666; font-size: 30rpx; }
.type.active { background: #e53935; color: #fff; }
.row { background: #fff; margin: 12rpx 20rpx; padding: 24rpx; border-radius: 12rpx; display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 34rpx; color: #333; }
.tag { font-size: 22rpx; color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
