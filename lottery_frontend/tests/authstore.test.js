import { describe, it, expect, beforeEach } from 'vitest'
import { authState, loadToken, setToken } from '../src/store/auth.js'

function stubStorage() {
  const store = {}
  globalThis.uni = {
    getStorageSync: (k) => store[k] || '',
    setStorageSync: (k, v) => { store[k] = v },
    removeStorageSync: (k) => { delete store[k] },
  }
}

describe('auth store', () => {
  beforeEach(() => { stubStorage(); setToken('') })

  it('setToken 写入 state 与 storage，loadToken 读回', () => {
    setToken('TOK123')
    expect(authState.token).toBe('TOK123')
    authState.token = ''
    expect(loadToken()).toBe('TOK123')
    expect(authState.token).toBe('TOK123')
  })

  it('setToken 假值清除', () => {
    setToken('X'); setToken('')
    expect(authState.token).toBe('')
    expect(loadToken()).toBe('')
  })

  it('setToken 带 isWechat 标记并持久化', () => {
    setToken('WXTOK', true)
    expect(authState.isWechat).toBe(true)
    authState.isWechat = false
    loadToken()
    expect(authState.isWechat).toBe(true)
  })

  it('退出清除 isWechat', () => {
    setToken('WXTOK', true)
    setToken('')
    expect(authState.isWechat).toBe(false)
    expect(loadToken()).toBe('')
  })
})
