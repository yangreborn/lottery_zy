import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({
  request: vi.fn(() => Promise.resolve('OK')),
}))
import { request } from '../src/api/request.js'
import { getLatest, getHistory, getStats } from '../src/api/lottery.js'

describe('lottery api', () => {
  beforeEach(() => { request.mockClear() })

  it('getLatest 带 code', async () => {
    await getLatest('ssq')
    expect(request).toHaveBeenCalledWith('/api/openapi/draw/latest', { data: { code: 'ssq' } })
  })

  it('getHistory 合并参数', async () => {
    await getHistory('dlt', { page: 2, date_from: '2026-06-01' })
    expect(request).toHaveBeenCalledWith('/api/openapi/draw/history',
      { data: { code: 'dlt', page: 2, date_from: '2026-06-01' } })
  })

  it('getStats 带 periods', async () => {
    await getStats('ssq', 30)
    expect(request).toHaveBeenCalledWith('/api/openapi/draw/stats', { data: { code: 'ssq', periods: 30 } })
  })
})
