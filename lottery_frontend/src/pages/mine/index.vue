<template>
  <view class="page">
    <TopBanner title="我的" />
    <view class="authbar">
      <text class="astate">{{ auth.isWechat ? '已微信登录' : '匿名使用中' }}</text>
      <text class="abtn" @click="auth.isWechat ? doLogout() : doWechatLogin()">{{ auth.isWechat ? '退出' : '微信登录' }}</text>
    </view>
    <view class="menu">
      <view class="entry" @click="go('/pages/mine/numbers')">
        <text class="ic">⭐</text><text class="tx">我的号码</text><text class="arr">›</text>
      </view>
      <view class="entry" @click="go('/pages/purchase/index')">
        <text class="ic">🛒</text><text class="tx">购买记录</text><text class="arr">›</text>
      </view>
      <view class="entry" @click="go('/pages/feedback/index')">
        <text class="ic">💬</text><text class="tx">我要反馈</text><text class="arr">›</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { ensureLogin, wechatLogin } from '../../api/user.js'
import { authState, setToken } from '../../store/auth.js'
import { reportAccess } from '../../utils/report.js'

const auth = authState
function go(url) { uni.navigateTo({ url }) }

function doWechatLogin() {
  uni.login({
    success: async (r) => {
      if (!r.code) { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }); return }
      try {
        const res = await wechatLogin(r.code)
        setToken(res.token, true)
        uni.showToast({ title: '登录成功', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.msg || '登录失败', icon: 'none' })
      }
    },
    fail: () => { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }) },
  })
}

function doLogout() {
  setToken('', false)
  uni.showToast({ title: '已退出', icon: 'none' })
}

onShow(() => {
  reportAccess('mine/index', {})
  ensureLogin()
})
</script>

<style scoped>
.authbar { display: flex; justify-content: space-between; align-items: center; padding: 24rpx; }
.astate { font-size: 28rpx; color: #888; }
.abtn { font-size: 28rpx; color: #e53935; }
.menu { margin: 12rpx 20rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.entry { display: flex; align-items: center; padding: 32rpx 28rpx; border-bottom: 1rpx solid #f3f3f3; }
.entry:last-child { border-bottom: none; }
.ic { font-size: 40rpx; margin-right: 20rpx; }
.tx { flex: 1; font-size: 32rpx; color: #333; }
.arr { color: #ccc; font-size: 36rpx; }
</style>
