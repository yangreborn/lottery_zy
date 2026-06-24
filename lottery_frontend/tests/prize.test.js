import { describe, it, expect } from 'vitest'
import { normalizePrizes } from '../src/utils/prize.js'

describe('normalizePrizes', () => {
  it('双色球：过滤空行 + 数字 level 转中文', () => {
    const grades = [
      { count: '8', level: 1, amount: '5867768' },
      { count: '2419', level: 3, amount: '3000' },
      { count: '', level: 7, amount: '' },
    ]
    const r = normalizePrizes(grades)
    expect(r.grouped).toBe(false)
    expect(r.flat.length).toBe(2)
    expect(r.flat[0].label).toBe('一等奖')
  })

  it('大乐透：字符串 level 原样保留', () => {
    const r = normalizePrizes([{ count: '8', level: '一等奖', amount: '7,110,906' }])
    expect(r.flat[0].label).toBe('一等奖')
  })

  it('快乐8：x码翻译 + 按 pick 降序分组', () => {
    const grades = [
      { count: '0', level: 'x10z10', amount: '0' },
      { count: '36', level: 'x10z9', amount: '8000' },
      { count: '1', level: 'x9z9', amount: '250000' },
    ]
    const r = normalizePrizes(grades)
    expect(r.grouped).toBe(true)
    expect(r.groups.map((g) => g.pick)).toEqual([10, 9])
    expect(r.groups[0].label).toBe('选10')
    expect(r.groups[0].rows[0].label).toBe('选10中10')
    expect(r.groups[1].rows[0].label).toBe('选9中9')
  })

  it('空数组安全', () => {
    expect(normalizePrizes([])).toEqual({ grouped: false, flat: [] })
    expect(normalizePrizes(null)).toEqual({ grouped: false, flat: [] })
  })
})
