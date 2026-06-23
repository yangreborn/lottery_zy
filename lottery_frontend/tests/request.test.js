import { describe, it, expect, beforeEach, vi } from 'vitest'
import { request } from '../src/api/request.js'

function stubUni(handler) {
  globalThis.uni = { request: handler }
}

describe('request', () => {
  beforeEach(() => { globalThis.uni = undefined })

  it('code=0 resolve data', async () => {
    stubUni(({ success }) => success({ statusCode: 200, data: { code: 0, msg: 'ok', data: { x: 1 }, error: null } }))
    await expect(request('/api/openapi/lottery/list')).resolves.toEqual({ x: 1 })
  })

  it('code!=0 reject {code,msg}', async () => {
    stubUni(({ success }) => success({ statusCode: 200, data: { code: 1, msg: '未知彩种', data: null, error: 'x' } }))
    await expect(request('/api/openapi/draw/latest')).rejects.toMatchObject({ code: 1, msg: '未知彩种' })
  })

  it('网络失败 reject code=-1', async () => {
    stubUni(({ fail }) => fail({ errMsg: 'request:fail' }))
    await expect(request('/api/openapi/draw/latest')).rejects.toMatchObject({ code: -1 })
  })
})
