<template>
  <view class="page" :style="themeVars">
    <TopBanner title="购买记录" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar"><button class="go" size="mini" @click="goCreate">新增购买</button></view>
    <view v-for="rec in items" :key="rec.id" class="card">
      <view class="top">
        <text class="issue">第 {{ rec.issue }} 期</text>
        <text class="date">{{ rec.purchase_date }}</text>
      </view>
      <view class="balls">
        <template v-for="(nums, key) in rec.numbers">
          <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
        </template>
      </view>
      <view class="meta">
        <text class="bet">{{ rec.bet_count }} 注</text>
        <text class="op del" @click="doDelete(rec.id)">删除</text>
      </view>
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
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, purchaseList, purchaseDelete } from '../../api/user.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

async function load() {
  emptyMsg.value = '加载中…'
  try {
    await ensureLogin()
    items.value = await purchaseList(store.code)
    if (!items.value.length) emptyMsg.value = '还没有购买记录'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
}

function onChange(code) { setCode(code); load() }
function goCreate() { uni.navigateTo({ url: '/pages/purchase/create' }) }

function doDelete(id) {
  uni.showModal({
    title: '确认删除',
    content: '删除后不可恢复，确定删除这条购买记录？',
    success: async (res) => {
      if (!res.confirm) return
      try { await purchaseDelete(id); load() }
      catch (e) { uni.showToast({ title: e.msg || '删除失败', icon: 'none' }) }
    },
  })
}

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞 */ }
  }
  load()
})
</script>

<style scoped>
.bar { display: flex; justify-content: flex-end; padding: 16rpx 20rpx 0; }
.go { background: var(--brand); color: var(--surface); }
.card { background: var(--surface); margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.top { display: flex; justify-content: space-between; font-size: 30rpx; color: var(--text-2); }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.meta { display: flex; justify-content: space-between; align-items: center; }
.bet { font-size: 28rpx; color: var(--accent); }
.op.del { font-size: 30rpx; color: var(--text-3); }
.empty { text-align: center; color: var(--text-3); padding: 80rpx 0; }
.page { background: var(--bg); min-height: 100vh; }
</style>
