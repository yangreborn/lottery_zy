<template>
  <view class="home" :style="themeVars">
    <view class="header">
      <view class="brand">
        <view class="logo">彩</view>
        <view class="brand-txt">
          <text class="brand-name">彩讯开奖</text>
          <text class="brand-sub">官方权威数据 · 实时更新</text>
        </view>
      </view>
      <view class="theme-btn" @click="themeOpen = true">
        <image class="theme-ic" :src="paletteIcon" mode="aspectFit" />
      </view>
    </view>

    <NoticeBar :notice="topNotice" @tap="goNotices" />

    <view v-if="cards.length" class="lwrap">
      <view v-for="c in cards" :key="c.code" class="lblock">
        <view class="lname">{{ c.name }}</view>
        <DrawCard v-if="c.draw" :draw="c.draw" :collapsible="true" />
        <view v-else class="lempty">暂无开奖数据</view>
      </view>
    </view>
    <view v-else class="empty">{{ emptyMsg }}</view>

    <view class="grid">
      <view v-for="m in menu" :key="m.key" class="mcard" @click="go(m)">
        <view class="ic-chip"><image class="ic" :src="menuIcon(m.icon)" mode="aspectFit" /></view>
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
    <ThemePicker :visible="themeOpen" @close="themeOpen = false" />
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NoticeBar from '../../components/NoticeBar.vue'
import DrawCard from '../../components/DrawCard.vue'
import LegalPopup from '../../components/LegalPopup.vue'
import ThemePicker from '../../components/ThemePicker.vue'
import { HOME_MENU, goMenu } from '../../utils/menu.js'
import { lineIcon } from '../../utils/icons.js'
import { getNotices } from '../../api/guide.js'
import { getLotteryList, getLatest } from '../../api/lottery.js'
import { getProfile } from '../../api/user.js'
import { filterHomeLotteries } from '../../utils/lottery.js'
import { authState } from '../../store/auth.js'
import { lotteryStore } from '../../store/lottery.js'
import { themeState, currentTheme, themeVarString } from '../../store/theme.js'

const store = lotteryStore
const menu = HOME_MENU
const topNotice = ref(null)
const cards = ref([])
const emptyMsg = ref('加载中…')
const popupVisible = ref(false)
const popupType = ref('agreement')
const themeOpen = ref(false)

// 主题：根节点下发 CSS 变量；图标按主题着色（依赖 themeState.key 触发重算）
const themeVars = computed(() => { void themeState.key; return themeVarString() })
const paletteIcon = computed(() => { void themeState.key; return lineIcon('palette', currentTheme().vars['--text-2']) })
function menuIcon(key) { void themeState.key; return lineIcon(key, currentTheme().vars['--text-2']) }

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
.home { min-height: 100vh; background: var(--bg); }

/* 头部：表面色 + 品牌标识 + 主题切换 */
.header {
  background: var(--surface);
  padding: calc(28rpx + var(--status-bar-height, 0px)) 32rpx 28rpx;
  border-bottom: 1rpx solid var(--border);
  display: flex; align-items: center; justify-content: space-between;
}
.brand { display: flex; align-items: center; }
.logo {
  width: 72rpx; height: 72rpx; border-radius: 20rpx;
  background: var(--brand); color: var(--brand-on);
  font-size: 40rpx; font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.brand-txt { display: flex; flex-direction: column; margin-left: 20rpx; }
.brand-name { font-size: 36rpx; font-weight: 700; color: var(--text); line-height: 1.2; }
.brand-sub { font-size: 23rpx; color: var(--text-3); margin-top: 4rpx; }
.theme-btn {
  width: 68rpx; height: 68rpx; border-radius: 20rpx;
  background: var(--surface-2); border: 1rpx solid var(--border);
  display: flex; align-items: center; justify-content: center;
}
.theme-ic { width: 40rpx; height: 40rpx; }

.lwrap { padding-top: 8rpx; }
.lblock { margin-top: 8rpx; }
.lname { padding: 12rpx 32rpx 0; color: var(--text); font-size: 30rpx; font-weight: 700; }
.lempty { text-align: center; color: var(--text-3); padding: 30rpx 0; font-size: 26rpx; }
.empty { text-align: center; color: var(--text-3); padding: 60rpx 0; }

/* 菜单：4 列线性图标卡片 */
.grid {
  display: grid; grid-template-columns: repeat(4, 1fr);
  gap: 20rpx 12rpx; padding: 28rpx 24rpx 12rpx;
}
.mcard { display: flex; flex-direction: column; align-items: center; }
.ic-chip {
  width: 96rpx; height: 96rpx; border-radius: 28rpx;
  background: var(--surface); border: 1rpx solid var(--border);
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--shadow-chip);
}
.ic { width: 46rpx; height: 46rpx; }
.tx { font-size: 25rpx; color: var(--text-2); margin-top: 14rpx; }

.footer { padding: 28rpx 28rpx 48rpx; text-align: center; }
.links { margin-bottom: 12rpx; }
.lk { color: var(--text-3); font-size: 26rpx; }
.sep { color: var(--text-3); font-size: 26rpx; margin: 0 14rpx; }
.src { color: var(--text-3); font-size: 22rpx; display: block; line-height: 1.6; }
</style>
