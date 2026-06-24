<template>
  <view class="page">
    <TopBanner title="我的号码" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar">
      <button class="go" size="mini" @click="goPicker">去选号</button>
    </view>
    <view v-for="grp in groups" :key="grp.name" class="group">
      <view class="group-title">{{ grp.name }}（{{ grp.records.length }}）</view>
      <view v-for="rec in grp.records" :key="rec.id" class="card">
        <view class="top">
          <text class="tag">{{ genLabel(rec.gen_type) }}</text>
          <text v-if="rec.target_issue" class="issue">目标 {{ rec.target_issue }}</text>
        </view>
        <view class="balls">
          <template v-for="(nums, key) in rec.numbers">
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
          </template>
        </view>
        <view v-if="rec.note" class="note">{{ rec.note }}</view>
        <view class="time">{{ formatTime(rec.created_at) }}</view>
        <view class="ops">
          <text class="op" @click="doGroup(rec)">归组</text>
          <text v-if="rec.target_issue" class="op" @click="doCheck(rec.id)">比对</text>
          <text class="op del" @click="doDelete(rec.id)">删除</text>
        </view>
      </view>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup } from '../../api/user.js'
import { reportAccess } from '../../utils/report.js'
import { formatTime, groupRecords } from '../../utils/records.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

const groups = computed(() => groupRecords(items.value))

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
function goPicker() { uni.switchTab({ url: '/pages/mine/picker' }) }

function doGroup(rec) {
  uni.showModal({
    title: '归组',
    editable: true,
    placeholderText: '输入组名(留空取消分组)',
    content: rec.group_name || '',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await setGroup(rec.id, (res.content || '').trim())
        load()
      } catch (e) {
        uni.showToast({ title: e.msg || '归组失败', icon: 'none' })
      }
    },
  })
}

async function doCheck(id) {
  try {
    const r = await checkNumber(id)
    reportAccess('mine/check', { lottery_code: store.code, action: 'check_number' })
    uni.showModal({
      title: '比对结果',
      content: `${r.desc}，${r.label}`,
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
.group-title { padding: 16rpx 24rpx 4rpx; font-size: 28rpx; color: #e53935; font-weight: bold; }
.card { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.top { display: flex; justify-content: space-between; font-size: 28rpx; color: #888; }
.tag { color: #e53935; }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.note { font-size: 28rpx; color: #999; }
.time { font-size: 24rpx; color: #bbb; margin-top: 6rpx; }
.ops { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.op { margin-left: 28rpx; font-size: 30rpx; color: #1e88e5; }
.op.del { color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
