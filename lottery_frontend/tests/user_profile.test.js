import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({ request: vi.fn(() => Promise.resolve({})) }))
vi.mock('../src/utils/device.js', () => ({ getOrCreateDeviceCode: () => 'dev' }))
import { request } from '../src/api/request.js'
import { getProfile, setProfile } from '../src/api/user.js'

describe('profile api', () => {
  beforeEach(() => { request.mockClear() })

  it('getProfile 走 GET /api/user/profile', async () => {
    await getProfile()
    expect(request).toHaveBeenCalledWith('/api/user/profile')
  })

  it('setProfile 走 POST 带 nickname', async () => {
    await setProfile('小红')
    expect(request).toHaveBeenCalledWith('/api/user/profile', { method: 'POST', data: { nickname: '小红' } })
  })
})
