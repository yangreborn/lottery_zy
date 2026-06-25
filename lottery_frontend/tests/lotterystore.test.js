import { describe, it, expect, beforeEach } from 'vitest'
import { lotteryStore, setCode, readStoredCode } from '../src/store/lottery.js'

function stubStorage(initial = {}) {
  const store = { ...initial }
  globalThis.uni = {
    getStorageSync: (k) => store[k] || '',
    setStorageSync: (k, v) => { store[k] = v },
  }
  return store
}

describe('lottery store 持久化彩种', () => {
  beforeEach(() => { stubStorage(); setCode('ssq') })

  it('readStoredCode 存储有值时返回该值', () => {
    stubStorage({ lottery_code: 'dlt' })
    expect(readStoredCode()).toBe('dlt')
  })

  it('readStoredCode 存储为空时兜底 ssq', () => {
    stubStorage()
    expect(readStoredCode()).toBe('ssq')
  })

  it('setCode 同步内存与存储', () => {
    stubStorage()
    setCode('kl8')
    expect(lotteryStore.code).toBe('kl8')
    expect(readStoredCode()).toBe('kl8')
  })
})
