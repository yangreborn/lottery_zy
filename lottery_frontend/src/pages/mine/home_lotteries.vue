<template>
  <view class="page">
    <TopBanner title="首页彩种" :back="true" />
    <view class="tip">勾选要在首页展示的彩种；不选 = 显示全部。</view>
    <view class="list">
      <view v-for="l in lotteries" :key="l.code" class="row" @click="toggle(l.code)">
        <text class="name">{{ l.name }}</text>
        <text class="chk">{{ selected.includes(l.code) ? '☑' : '☐' }}</text>
      </view>
    </view>
    <view class="actions">
      <button class="btn" @click="save">保存</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { getLotteryList } from '../../api/lottery.js'
import { getProfile, setHomeLotteries, ensureLogin } from '../../api/user.js'

const lotteries = ref([])
const selected = ref([])

function toggle(code) {
  selected.value = selected.value.includes(code)
    ? selected.value.filter((c) => c !== code)
    : [...selected.value, code]
}

async function save() {
  try {
    await setHomeLotteries(selected.value)
    uni.showToast({ title: '已保存', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
}

onLoad(async () => {
  try {
    lotteries.value = await getLotteryList()
    await ensureLogin()
    const p = await getProfile()
    selected.value = p.home_lotteries || []
  } catch (e) {
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
})
</script>

<style scoped>
.tip { padding: 16rpx 28rpx; color: #999; font-size: 26rpx; }
.list { margin: 0 20rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.row { display: flex; align-items: center; justify-content: space-between; padding: 30rpx 28rpx; border-bottom: 1rpx solid #f3f3f3; }
.row:last-child { border-bottom: none; }
.name { font-size: 32rpx; color: #333; }
.chk { font-size: 40rpx; color: #e53935; }
.actions { padding: 32rpx 20rpx; }
.btn { background: #e53935; color: #fff; font-size: 32rpx; width: 100%; }
</style>
