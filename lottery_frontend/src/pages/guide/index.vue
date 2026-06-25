<template>
  <view class="page">
    <TopBanner title="玩法说明" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
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
import LotteryTabs from '../../components/LotteryTabs.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { getGuideList } from '../../api/guide.js'
import { reportAccess } from '../../utils/report.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

async function load() {
  emptyMsg.value = '加载中…'
  try {
    items.value = await getGuideList(store.code, 'rule')
    if (!items.value.length) emptyMsg.value = '暂无内容'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) { setCode(code); load() }
function goDetail(id) { uni.navigateTo({ url: `/pages/guide/detail?id=${id}` }) }

onShow(async () => {
  reportAccess('guide/index', { lottery_code: lotteryStore.code })
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞列表 */ }
  }
  load()
})
</script>

<style scoped>
.row { background: #fff; margin: 12rpx 20rpx; padding: 24rpx; border-radius: 12rpx; display: flex; justify-content: space-between; align-items: center; }
.title { font-size: 34rpx; color: #333; }
.tag { font-size: 22rpx; color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
