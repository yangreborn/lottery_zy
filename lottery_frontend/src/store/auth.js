import { reactive } from 'vue'

const TOKEN_KEY = 'lottery_token'

export const authState = reactive({ token: '' })

export function loadToken() {
  const t = uni.getStorageSync(TOKEN_KEY)
  if (t) authState.token = t
  return authState.token
}

export function setToken(t) {
  authState.token = t || ''
  if (t) uni.setStorageSync(TOKEN_KEY, t)
  else uni.removeStorageSync(TOKEN_KEY)
}
