import { describe, it, expect } from 'vitest'
import { shortLotteryName, splitTabs, HOT_CODES } from '../src/utils/lottery.js'

describe('shortLotteryName', () => {
  it('超级大乐透缩写为大乐透', () => {
    expect(shortLotteryName({ code: 'dlt', name: '超级大乐透' })).toBe('大乐透')
  })
  it('其它彩种返回原名', () => {
    expect(shortLotteryName({ code: 'ssq', name: '双色球' })).toBe('双色球')
  })
  it('空值安全', () => {
    expect(shortLotteryName(null)).toBe('')
  })
})

describe('splitTabs', () => {
  const list = [
    { code: 'ssq', name: '双色球' },
    { code: 'dlt', name: '超级大乐透' },
    { code: 'xyz', name: '新彩种' },
  ]
  it('热门进 visible，非热门进 overflow', () => {
    const { visible, overflow } = splitTabs(list)
    expect(visible.map((x) => x.code)).toEqual(['ssq', 'dlt'])
    expect(overflow.map((x) => x.code)).toEqual(['xyz'])
  })
  it('HOT_CODES 含 5 个常驻热门彩种', () => {
    expect(HOT_CODES).toEqual(['ssq', 'dlt', '3d', 'pl3', 'kl8'])
  })
  it('空列表安全', () => {
    expect(splitTabs(null)).toEqual({ visible: [], overflow: [] })
  })
})
