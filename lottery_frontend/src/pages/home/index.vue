<template>
  <view class="home">
    <view class="banner"><text class="bt">彩票查询</text></view>
    <NoticeBar :notice="topNotice" @tap="goNotices" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <DrawCard v-if="draw" :draw="draw" />
    <view v-else class="empty">{{ emptyMsg }}</view>
    <view class="grid">
      <view v-for="m in menu" :key="m.key" class="mcard" @click="go(m)">
        <text class="ic">{{ m.icon }}</text>
        <text class="tx">{{ m.title }}</text>
      </view>
    </view>
    <view class="footer">
      <view class="links">
        <text class="lk" @click="openDoc('agreement')">用户协议</text>
        <text class="sep">·</text>
        <text class="lk" @click="openDoc('privacy')">隐私协议</text>
      </view>
      <text class="src">数据来源：cwl.gov.cn · sporttery.cn</text>
    </view>
    <LegalPopup :visible="popupVisible" :type="popupType" @close="popupVisible = false" />
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NoticeBar from '../../components/NoticeBar.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import DrawCard from '../../components/DrawCard.vue'
import LegalPopup from '../../components/LegalPopup.vue'
import { HOME_MENU, goMenu } from '../../utils/menu.js'
import { getNotices } from '../../api/guide.js'
import { getLotteryList, getLatest } from '../../api/lottery.js'
import { lotteryStore, setCode } from '../../store/lottery.js'

const store = lotteryStore
const menu = HOME_MENU
const topNotice = ref(null)
const lotteries = ref([])
const draw = ref(null)
const emptyMsg = ref('加载中…')
const popupVisible = ref(false)
const popupType = ref('agreement')

function go(m) { goMenu(m) }
function openDoc(type) { popupType.value = type; popupVisible.value = true }
function goNotices() { uni.navigateTo({ url: '/pages/notice/index' }) }

async function loadDraw() {
  draw.value = null
  emptyMsg.value = '加载中…'
  try {
    draw.value = await getLatest(store.code)
  } catch (e) {
    emptyMsg.value = e.msg || '暂无数据'
  }
}
function onChange(code) {
  setCode(code)
  loadDraw()
}

onMounted(async () => {
  try {
    lotteries.value = await getLotteryList()
  } catch (e) {
    // 彩种列表失败不阻塞首页
  }
})
onShow(async () => {
  loadDraw()
  try {
    const list = await getNotices(store.code)
    topNotice.value = (list && list.length) ? list[0] : null
  } catch (e) {
    topNotice.value = null
  }
})
</script>

<style scoped>
.home { min-height: 100vh; background: linear-gradient(180deg, #ffd9d4 0%, #fff0ee 35%, #fbfbfb 100%); }
.banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: calc(44rpx + var(--status-bar-height, 0px)) 0 44rpx; text-align: center; }
.bt { color: #fff; font-size: 42rpx; font-weight: 700; letter-spacing: 8rpx; }
.empty { text-align: center; color: #999; padding: 60rpx 0; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24rpx; padding: 28rpx; }
.mcard { background: #fff; border-radius: 20rpx; padding: 44rpx 0; text-align: center; box-shadow: 0 4rpx 16rpx rgba(229, 57, 53, 0.10); }
.ic { font-size: 56rpx; display: block; }
.tx { font-size: 32rpx; font-weight: 600; color: #333; display: block; margin-top: 14rpx; }
.footer { padding: 20rpx 28rpx 40rpx; text-align: center; }
.links { margin-bottom: 12rpx; }
.lk { color: #bbb; font-size: 26rpx; }
.sep { color: #bbb; font-size: 26rpx; margin: 0 12rpx; }
.src { color: #999; font-size: 22rpx; display: block; line-height: 1.6; }
</style>
