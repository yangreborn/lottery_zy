import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({
  request: vi.fn(() => Promise.resolve([])),
}))
import { request } from '../src/api/request.js'
import { getGuideList, getGuideDetail, getNotices } from '../src/api/guide.js'

describe('guide api', () => {
  beforeEach(() => { request.mockClear() })

  it('list 带 code+type', async () => {
    await getGuideList('ssq', 'rule')
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/list', { data: { code: 'ssq', type: 'rule' } })
  })

  it('list 空 type 不带 type', async () => {
    await getGuideList('ssq', '')
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/list', { data: { code: 'ssq' } })
  })

  it('list 空 code 不带 code', async () => {
    await getGuideList('', '')
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/list', { data: {} })
  })

  it('detail', async () => {
    await getGuideDetail(5)
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/detail', { data: { id: 5 } })
  })

  it('getNotices 带 code', async () => {
    await getNotices('ssq')
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/list', { data: { important: 1, code: 'ssq' } })
  })

  it('getNotices 无 code', async () => {
    await getNotices('')
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/list', { data: { important: 1 } })
  })
})
