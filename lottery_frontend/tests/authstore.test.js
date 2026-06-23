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
})
