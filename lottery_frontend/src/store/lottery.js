import { reactive } from 'vue'

export const lotteryStore = reactive({ code: 'ssq' })

export function setCode(c) {
  lotteryStore.code = c
}
