import { describe, it, expect, beforeEach } from 'vitest'
import { getOrCreateDeviceCode } from '../src/utils/device.js'

function stubStorage() {
  const store = {}
  globalThis.uni = {
    getStorageSync: (k) => store[k] || '',
    setStorageSync: (k, v) => { store[k] = v },
  }
}

describe('device code', () => {
  beforeEach(stubStorage)

  it('首次生成并持久，二次返回同值', () => {
    const a = getOrCreateDeviceCode()
    expect(a).toBeTruthy()
    const b = getOrCreateDeviceCode()
    expect(b).toBe(a)
  })
})
