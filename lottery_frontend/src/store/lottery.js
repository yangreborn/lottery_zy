import { reactive } from 'vue'

const STORAGE_KEY = 'lottery_code'

export function readStoredCode() {
  try {
    if (typeof uni !== 'undefined') {
      return uni.getStorageSync(STORAGE_KEY) || 'ssq'
    }
  } catch (e) {
    // 读存储失败，兜底
  }
  return 'ssq'
}

export const lotteryStore = reactive({ code: readStoredCode() })

export function setCode(c) {
  lotteryStore.code = c
  try {
    if (typeof uni !== 'undefined') {
      uni.setStorageSync(STORAGE_KEY, c)
    }
  } catch (e) {
    // 写存储失败，内存态已更新，不影响本次使用
  }
}
