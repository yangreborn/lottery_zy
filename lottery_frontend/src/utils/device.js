const DEVICE_KEY = 'lottery_device_code'

export function getOrCreateDeviceCode() {
  let code = uni.getStorageSync(DEVICE_KEY)
  if (!code) {
    code = 'dev-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10)
    uni.setStorageSync(DEVICE_KEY, code)
  }
  return code
}
