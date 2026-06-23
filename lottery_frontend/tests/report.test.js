import { describe, it, expect, beforeEach } from 'vitest'
import { reportAccess } from '../src/utils/report.js'
import { authState } from '../src/store/auth.js'

let captured
function stubUni(ok = true) {
  globalThis.uni = {
    request: (opts) => {
      captured = opts
      if (ok) opts.success({ statusCode: 200, data: { code: 0, msg: 'ok', data: {}, error: null } })
      else opts.fail({ errMsg: 'fail' })
    },
  }
}

describe('reportAccess', () => {
  beforeEach(() => { authState.token = ''; captured = undefined })

  it('POST log 带参数', async () => {
    stubUni(true)
    await reportAccess('draw/latest', { lottery_code: 'ssq', action: 'view' })
    expect(captured.url).toContain('/api/openapi/log')
    expect(captured.method).toBe('POST')
    expect(captured.data).toEqual({ path: 'draw/latest', lottery_code: 'ssq', action: 'view' })
  })

  it('缺省 action=view、lottery_code 空', async () => {
    stubUni(true)
    await reportAccess('guide/index')
    expect(captured.data).toEqual({ path: 'guide/index', lottery_code: '', action: 'view' })
  })

  it('失败被静默吞不抛', async () => {
    stubUni(false)
    await expect(reportAccess('x')).resolves.toBeUndefined()
  })
})
