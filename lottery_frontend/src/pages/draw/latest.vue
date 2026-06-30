<template>
  <view class="page" :style="themeVars">
    <TopBanner title="当期开奖" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <DrawCard v-if="draw" :draw="draw" />
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { computed as __cmp } from 'vue'
import { themeState as __ts, themeVarString as __tvs } from '../../store/theme.js'
const themeVars = __cmp(() => { void __ts.key; return __tvs() })

import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import DrawCard from '../../components/DrawCard.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getLatest } from '../../api/lottery.js'

const store = lotteryStore
const lotteries = ref([])
const draw = ref(null)
const emptyMsg = ref('加载中…')

async function load() {
  draw.value = null
  emptyMsg.value = '加载中…'
  try {
    draw.value = await getLatest(store.code)
  } catch (e) {
    emptyMsg.value = e.msg || '暂无数据'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) {
  setCode(code)
  load()
}

onMounted(async () => {
  try {
    lotteries.value = await getLotteryList()
  } catch (e) {
    uni.showToast({ title: e.msg || '彩种加载失败', icon: 'none' })
  }
})
onShow(() => { load() })
</script>

<style scoped>
.page { padding: 0 0 30rpx; }
.empty { text-align: center; color: var(--text-3); padding: 80rpx 0; }
.page { background: var(--bg); min-height: 100vh; }
</style>
