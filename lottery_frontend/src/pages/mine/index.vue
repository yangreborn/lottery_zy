<template>
  <view class="page">
    <TopBanner title="我的" />
    <view class="authbar">
      <text class="uname" @click="editNickname">{{ nickname || '点击设置昵称' }}</text>
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
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { ensureLogin, wechatLogin, getProfile, setProfile } from '../../api/user.js'
import { authState, setToken } from '../../store/auth.js'
import { reportAccess } from '../../utils/report.js'

const auth = authState
const nickname = ref('')
function go(url) { uni.navigateTo({ url }) }

async function loadProfile() {
  try { const p = await getProfile(); nickname.value = p.nickname || '' } catch (e) { /* 容错: 资料拉取失败不阻塞 */ }
}

function editNickname() {
  uni.showModal({
    title: '设置昵称',
    editable: true,
    placeholderText: '输入昵称(≤30字)',
    content: nickname.value,
    success: async (res) => {
      if (!res.confirm) return
      try {
        const p = await setProfile((res.content || '').trim())
        nickname.value = p.nickname || ''
        uni.showToast({ title: '已保存', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
      }
    },
  })
}

function doWechatLogin() {
  // 先在点击手势内弹授权取微信昵称（非微信环境会 fail，则置空继续）
  uni.getUserProfile({
    desc: '用于完善个人资料',
    success: (p) => finishWechatLogin(p.userInfo && p.userInfo.nickName),
    fail: () => finishWechatLogin(''),
  })
}

function finishWechatLogin(nickName) {
  uni.login({
    success: async (r) => {
      if (!r.code) { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }); return }
      try {
        const res = await wechatLogin(r.code)
        setToken(res.token, true)
        if (nickName) { try { await setProfile(nickName) } catch (e) { /* 昵称写入失败不阻塞登录 */ } }
        uni.showToast({ title: '登录成功', icon: 'success' })
        loadProfile()
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
  loadProfile()
}

onShow(async () => {
  reportAccess('mine/index', {})
  await ensureLogin()
  loadProfile()
})
</script>

<style scoped>
.authbar { display: flex; justify-content: space-between; align-items: center; padding: 32rpx 24rpx; }
.uname { font-size: 34rpx; color: #333; font-weight: 600; }
.abtn { font-size: 28rpx; color: #e53935; }
.menu { margin: 12rpx 20rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.entry { display: flex; align-items: center; padding: 32rpx 28rpx; border-bottom: 1rpx solid #f3f3f3; }
.entry:last-child { border-bottom: none; }
.ic { font-size: 40rpx; margin-right: 20rpx; }
.tx { flex: 1; font-size: 32rpx; color: #333; }
.arr { color: #ccc; font-size: 36rpx; }
</style>
