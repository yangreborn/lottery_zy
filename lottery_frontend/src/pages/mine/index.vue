<template>
  <view class="page">
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar">
      <button class="go" size="mini" @click="goPicker">去选号</button>
    </view>
    <view v-for="rec in items" :key="rec.id" class="card">
      <view class="top">
        <text class="tag">{{ genLabel(rec.gen_type) }}</text>
        <text v-if="rec.target_issue" class="issue">目标 {{ rec.target_issue }}</text>
      </view>
      <view class="balls">
        <Ball v-for="(n, i) in rec.numbers.red" :key="'r'+i" :value="n" zone="red" />
        <Ball v-for="(n, i) in rec.numbers.blue" :key="'b'+i" :value="n" zone="blue" />
      </view>
      <view v-if="rec.note" class="note">{{ rec.note }}</view>
      <view class="ops">
        <text v-if="rec.target_issue" class="op" @click="doCheck(rec.id)">比对</text>
        <text class="op del" @click="doDelete(rec.id)">删除</text>
      </view>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, listNumbers, deleteNumber, checkNumber } from '../../api/user.js'
import { reportAccess } from '../../utils/report.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

const GEN = { manual: '手动', random: '机选', dan_random: '定胆' }
function genLabel(g) { return GEN[g] || g }

async function load() {
  emptyMsg.value = '加载中…'
  try {
    await ensureLogin()
    items.value = await listNumbers(store.code)
    if (!items.value.length) emptyMsg.value = '还没有记录，去选号吧'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) { setCode(code); load() }
function goPicker() { uni.navigateTo({ url: '/pages/mine/picker' }) }

async function doCheck(id) {
  try {
    const r = await checkNumber(id)
    reportAccess('mine/check', { lottery_code: store.code, action: 'check_number' })
    uni.showModal({
      title: '比对结果',
      content: `命中 红${r.red_hit} 蓝${r.blue_hit}，${r.label}`,
      showCancel: false,
    })
  } catch (e) {
    uni.showToast({ title: e.msg || '比对失败', icon: 'none' })
  }
}

async function doDelete(id) {
  try {
    await deleteNumber(id)
    load()
  } catch (e) {
    uni.showToast({ title: e.msg || '删除失败', icon: 'none' })
  }
}

onShow(async () => {
  reportAccess('mine/index', { lottery_code: lotteryStore.code })
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞列表 */ }
  }
  load()
})
</script>

<style scoped>
.bar { display: flex; justify-content: flex-end; padding: 16rpx 20rpx 0; }
.go { background: #e53935; color: #fff; }
.card { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.top { display: flex; justify-content: space-between; font-size: 24rpx; color: #888; }
.tag { color: #e53935; }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.note { font-size: 24rpx; color: #999; }
.ops { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.op { margin-left: 28rpx; font-size: 26rpx; color: #1e88e5; }
.op.del { color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
