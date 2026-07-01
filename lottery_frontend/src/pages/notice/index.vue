<template>
  <view class="page" :style="themeVars">
    <TopBanner title="通知" :back="true" />

    <view v-if="top" class="feature" @click="goDetail(top.id)">
      <view class="f-tags">
        <text v-if="top.is_important" class="badge">重点</text>
        <text class="f-type">{{ top.type_label }}</text>
      </view>
      <text class="f-title">{{ top.title }}</text>
      <view class="f-foot">
        <text class="f-date">{{ fmtDate(top.publish_at) }}</text>
        <text class="f-more">查看详情 ›</text>
      </view>
    </view>

    <view v-if="rest.length" class="rest">
      <text class="rest-hd">更多通知</text>
      <view v-for="g in rest" :key="g.id" class="row" @click="goDetail(g.id)">
        <view class="row-l">
          <text v-if="g.is_important" class="badge sm">重点</text>
          <text class="title">{{ g.title }}</text>
        </view>
        <text class="date">{{ fmtDate(g.publish_at) }}</text>
      </view>
    </view>

    <view v-if="!top" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { computed as __cmp } from 'vue'
import { themeState as __ts, themeVarString as __tvs } from '../../store/theme.js'
const themeVars = __cmp(() => { void __ts.key; return __tvs() })

import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { getGuideList } from '../../api/guide.js'

const items = ref([])
const emptyMsg = ref('加载中…')

// 后端已按「重点在前 → 发布时间倒序」排序：第一条即重点/最新，其余顺延
const top = computed(() => items.value[0] || null)
const rest = computed(() => items.value.slice(1))

function fmtDate(dt) {
  if (!dt) return ''
  return String(dt).slice(0, 10)
}

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
.page { background: var(--bg); min-height: 100vh; }

/* 置顶突出卡片 */
.feature {
  background: var(--brand-soft-bg); border: 1rpx solid var(--brand-soft-border);
  margin: 20rpx; padding: 28rpx; border-radius: 20rpx;
}
.f-tags { display: flex; align-items: center; gap: 12rpx; margin-bottom: 14rpx; }
.f-type { font-size: 22rpx; color: var(--text-3); }
.f-title { font-size: 34rpx; font-weight: 700; color: var(--text); line-height: 1.4; }
.f-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 18rpx; }
.f-date { font-size: 24rpx; color: var(--text-3); }
.f-more { font-size: 26rpx; color: var(--brand); font-weight: 600; }

.badge {
  font-size: 20rpx; color: var(--brand-on); background: var(--brand);
  padding: 2rpx 12rpx; border-radius: 8rpx; flex-shrink: 0;
}
.badge.sm { font-size: 18rpx; padding: 2rpx 10rpx; }

/* 其余通知 */
.rest { margin-top: 8rpx; }
.rest-hd { display: block; padding: 12rpx 24rpx; font-size: 24rpx; color: var(--text-3); }
.row {
  background: var(--surface); margin: 12rpx 20rpx; padding: 24rpx;
  border-radius: 12rpx; display: flex; justify-content: space-between; align-items: center;
}
.row-l { display: flex; align-items: center; gap: 12rpx; flex: 1; min-width: 0; }
.title {
  font-size: 30rpx; color: var(--text);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.date { font-size: 22rpx; color: var(--text-3); margin-left: 14rpx; flex-shrink: 0; }
.empty { text-align: center; color: var(--text-3); padding: 80rpx 0; }
</style>
