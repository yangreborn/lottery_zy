import { describe, it, expect } from 'vitest'
import { shortLotteryName, splitTabs, HOT_CODES, sortLotteries, filterHomeLotteries } from '../src/utils/lottery.js'

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
  it('HOT_CODES 含 5 个常驻热门彩种(规范顺序)', () => {
    expect(HOT_CODES).toEqual(['ssq', 'dlt', '3d', 'kl8', 'pl3'])
  })
  it('空列表安全', () => {
    expect(splitTabs(null)).toEqual({ visible: [], overflow: [] })
  })
})

describe('sortLotteries', () => {
  it('按 ssq,dlt,3d,kl8,pl3 规范顺序排序', () => {
    const list = [
      { code: '3d' }, { code: 'pl3' }, { code: 'ssq' }, { code: 'kl8' }, { code: 'dlt' },
    ]
    expect(sortLotteries(list).map((x) => x.code)).toEqual(['ssq', 'dlt', '3d', 'kl8', 'pl3'])
  })
  it('未知 code 依原相对序排末尾', () => {
    const list = [{ code: 'xyz' }, { code: 'dlt' }, { code: 'abc' }, { code: 'ssq' }]
    expect(sortLotteries(list).map((x) => x.code)).toEqual(['ssq', 'dlt', 'xyz', 'abc'])
  })
  it('空值安全', () => {
    expect(sortLotteries(null)).toEqual([])
  })
})

describe('filterHomeLotteries', () => {
  const list = [{ code: 'ssq' }, { code: 'dlt' }, { code: '3d' }]
  it('codes 为空返回全部', () => {
    expect(filterHomeLotteries(list, []).map((x) => x.code)).toEqual(['ssq', 'dlt', '3d'])
    expect(filterHomeLotteries(list, null).map((x) => x.code)).toEqual(['ssq', 'dlt', '3d'])
  })
  it('按 codes 过滤，顺序随入参', () => {
    expect(filterHomeLotteries(list, ['3d', 'ssq']).map((x) => x.code)).toEqual(['ssq', '3d'])
  })
  it('未知 code 安全忽略；空列表安全', () => {
    expect(filterHomeLotteries(list, ['xyz']).map((x) => x.code)).toEqual([])
    expect(filterHomeLotteries(null, ['ssq'])).toEqual([])
  })
})
