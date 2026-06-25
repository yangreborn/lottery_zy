import { reactive } from 'vue'

const TOKEN_KEY = 'lottery_token'
const WECHAT_KEY = 'lottery_is_wechat'

export const authState = reactive({ token: '', isWechat: false })

export function loadToken() {
  const t = uni.getStorageSync(TOKEN_KEY)
  if (t) authState.token = t
  authState.isWechat = !!uni.getStorageSync(WECHAT_KEY)
  return authState.token
}

export function setToken(t, isWechat = false) {
  authState.token = t || ''
  authState.isWechat = !!t && isWechat
  if (t) uni.setStorageSync(TOKEN_KEY, t)
  else uni.removeStorageSync(TOKEN_KEY)
  if (t && isWechat) uni.setStorageSync(WECHAT_KEY, '1')
  else uni.removeStorageSync(WECHAT_KEY)
}
