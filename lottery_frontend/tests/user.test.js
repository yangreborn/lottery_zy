import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({
  request: vi.fn(() => Promise.resolve({ token: 'T' })),
}))
import { request } from '../src/api/request.js'
import { login, createNumber, listNumbers, deleteNumber, checkNumber } from '../src/api/user.js'

describe('user api', () => {
  beforeEach(() => { request.mockClear() })

  it('login', async () => {
    await login('dev-x')
    expect(request).toHaveBeenCalledWith('/api/user/login', { method: 'POST', data: { code: 'dev-x' } })
  })
  it('createNumber', async () => {
    await createNumber({ code: 'ssq', gen_type: 'random' })
    expect(request).toHaveBeenCalledWith('/api/user/number/create', { method: 'POST', data: { code: 'ssq', gen_type: 'random' } })
  })
  it('listNumbers 带 code', async () => {
    await listNumbers('ssq')
    expect(request).toHaveBeenCalledWith('/api/user/number/list', { data: { code: 'ssq' } })
  })
  it('listNumbers 无 code', async () => {
    await listNumbers('')
    expect(request).toHaveBeenCalledWith('/api/user/number/list', { data: {} })
  })
  it('deleteNumber', async () => {
    await deleteNumber(5)
    expect(request).toHaveBeenCalledWith('/api/user/number/5', { method: 'DELETE' })
  })
  it('checkNumber', async () => {
    await checkNumber(5)
    expect(request).toHaveBeenCalledWith('/api/user/number/check', { data: { id: 5 } })
  })
})
