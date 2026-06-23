import { describe, it, expect, beforeEach } from 'vitest'
import { request } from '../src/api/request.js'
import { authState } from '../src/store/auth.js'

let captured
function stubUni() {
  globalThis.uni = {
    request: (opts) => { captured = opts; opts.success({ statusCode: 200, data: { code: 0, msg: 'ok', data: {}, error: null } }) },
  }
}

describe('request token header', () => {
  beforeEach(() => { stubUni(); authState.token = '' })

  it('有 token 带 X-User-Id 头', async () => {
    authState.token = 'TOK9'
    await request('/api/user/number/list')
    expect(captured.header['X-User-Id']).toBe('TOK9')
  })

  it('无 token 不带该头', async () => {
    await request('/api/openapi/lottery/list')
    expect(captured.header && captured.header['X-User-Id']).toBeFalsy()
  })
})
