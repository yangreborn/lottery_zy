<template>
  <view class="home">
    <view class="banner"><text class="bt">彩票查询</text></view>
    <NoticeBar :notice="topNotice" @tap="goNotices" />
    <view v-if="cards.length">
      <view v-for="c in cards" :key="c.code" class="lblock">
        <view class="lname">{{ c.name }}</view>
        <DrawCard v-if="c.draw" :draw="c.draw" :collapsible="true" />
        <view v-else class="lempty">暂无开奖数据</view>
      </view>
    </view>
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
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NoticeBar from '../../components/NoticeBar.vue'
import DrawCard from '../../components/DrawCard.vue'
import LegalPopup from '../../components/LegalPopup.vue'
import { HOME_MENU, goMenu } from '../../utils/menu.js'
import { getNotices } from '../../api/guide.js'
import { getLotteryList, getLatest } from '../../api/lottery.js'
import { getProfile } from '../../api/user.js'
import { filterHomeLotteries } from '../../utils/lottery.js'
import { authState } from '../../store/auth.js'
import { lotteryStore } from '../../store/lottery.js'

const store = lotteryStore
const menu = HOME_MENU
const topNotice = ref(null)
const cards = ref([])
const emptyMsg = ref('加载中…')
const popupVisible = ref(false)
const popupType = ref('agreement')

function go(m) { goMenu(m) }
function openDoc(type) { popupType.value = type; popupVisible.value = true }
function goNotices() { uni.navigateTo({ url: '/pages/notice/index' }) }

const LATEST_TTL = 5 * 60 * 1000 // 当期开奖缓存 5 分钟（开奖一天一次，足够新）
function readLatestCache(code) {
  try {
    const c = uni.getStorageSync('latest_' + code)
    if (c && c.ts && Date.now() - c.ts < LATEST_TTL) return c.draw
  } catch (e) { /* 读缓存失败忽略 */ }
  return null
}
function writeLatestCache(code, draw) {
  try { uni.setStorageSync('latest_' + code, { ts: Date.now(), draw }) } catch (e) { /* 写缓存失败忽略 */ }
}

async function loadCards() {
  try {
    const all = await getLotteryList()
    // 仅微信登录用户读取首页彩种偏好；匿名/失败 → 显示全部
    let pref = []
    if (authState.isWechat) {
      try { const p = await getProfile(); pref = p.home_lotteries || [] } catch (e) { /* 偏好拉取失败不阻塞 */ }
    }
    const list = filterHomeLotteries(all, pref)
    // 先用缓存即时渲染；缓存新鲜(5分钟内)的彩种跳过网络请求，避免每次白屏重载
    cards.value = list.map((l) => ({ code: l.code, name: l.name, draw: readLatestCache(l.code) }))
    await Promise.all(list.map(async (l, idx) => {
      if (cards.value[idx].draw) return
      try {
        const d = await getLatest(l.code)
        cards.value[idx].draw = d
        writeLatestCache(l.code, d)
      } catch (e) {
        // 单个彩种暂无开奖不阻塞整体
      }
    }))
    cards.value = [...cards.value]
    if (!cards.value.length) emptyMsg.value = '暂无数据'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
}

onShow(async () => {
  loadCards()
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
.lblock { margin-top: 12rpx; }
.lname { padding: 8rpx 28rpx 0; color: #333; font-size: 30rpx; font-weight: 700; }
.lempty { text-align: center; color: #999; padding: 30rpx 0; font-size: 26rpx; }
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
