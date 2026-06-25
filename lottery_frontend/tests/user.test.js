import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({
  request: vi.fn(() => Promise.resolve({ token: 'T' })),
}))
import { request } from '../src/api/request.js'
import { login, createNumber, listNumbers, deleteNumber, checkNumber, generateNumbers, submitFeedback, batchDelete, batchGroup, purchaseCreate, purchaseList, purchaseDelete } from '../src/api/user.js'

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
  it('generateNumbers', async () => {
    await generateNumbers('ssq', 5)
    expect(request).toHaveBeenCalledWith('/api/user/number/generate', { method: 'POST', data: { code: 'ssq', count: 5 } })
  })
  it('submitFeedback', async () => {
    await submitFeedback({ content: '建议', contact: 'wx123' })
    expect(request).toHaveBeenCalledWith('/api/user/feedback', { method: 'POST', data: { content: '建议', contact: 'wx123' } })
  })
  it('batchDelete', async () => {
    await batchDelete([1, 2])
    expect(request).toHaveBeenCalledWith('/api/user/number/batch_delete', { method: 'POST', data: { ids: [1, 2] } })
  })
  it('batchGroup', async () => {
    await batchGroup([1, 2], 'A')
    expect(request).toHaveBeenCalledWith('/api/user/number/batch_group', { method: 'POST', data: { ids: [1, 2], group_name: 'A' } })
  })
  it('purchaseCreate', async () => {
    await purchaseCreate({ code: 'ssq', issue: '2026073', numbers: { red: [1] }, bet_count: 2, purchase_date: '2026-06-20' })
    expect(request).toHaveBeenCalledWith('/api/user/purchase/create', { method: 'POST', data: { code: 'ssq', issue: '2026073', numbers: { red: [1] }, bet_count: 2, purchase_date: '2026-06-20' } })
  })
  it('purchaseList 带 code', async () => {
    await purchaseList('ssq')
    expect(request).toHaveBeenCalledWith('/api/user/purchase/list', { data: { code: 'ssq' } })
  })
  it('purchaseList 无 code', async () => {
    await purchaseList('')
    expect(request).toHaveBeenCalledWith('/api/user/purchase/list', { data: {} })
  })
  it('purchaseDelete', async () => {
    await purchaseDelete(5)
    expect(request).toHaveBeenCalledWith('/api/user/purchase/5', { method: 'DELETE' })
  })
})
