import { describe, it, expect } from 'vitest'
import { isDigitGame, numberMatrix, intervalTrend, spanSeries } from '../src/utils/trend.js'

describe('isDigitGame', () => {
  it('数字玩法(可重复有序)为真', () => {
    expect(isDigitGame({ zones: [{ key: 'digits', ordered: true, allow_repeat: true }] })).toBe(true)
  })
  it('普通玩法为假', () => {
    expect(isDigitGame({ zones: [{ key: 'red', min: 1, max: 33 }] })).toBe(false)
    expect(isDigitGame(null)).toBe(false)
  })
})

describe('numberMatrix', () => {
  // 从新到旧
  const draws = [
    { issue: '003', draw_date: '2026-06-03', numbers: { red: [2, 3] } },
    { issue: '002', draw_date: '2026-06-02', numbers: { red: [1] } },
    { issue: '001', draw_date: '2026-06-01', numbers: { red: [2] } },
  ]
  const m = numberMatrix(draws, 'red', 1, 3)

  it('号码列为 lo..hi，行新在前', () => {
    expect(m.numbers).toEqual([1, 2, 3])
    expect(m.rows.map((r) => r.issue)).toEqual(['003', '002', '001'])
  })

  it('命中与遗漏计算正确', () => {
    const byIssue = Object.fromEntries(m.rows.map((r) => [r.issue, r.cells]))
    // 003: 1未中(遗漏1) 2中(0) 3中(0)
    expect(byIssue['003']).toEqual([
      { num: 1, hit: false, miss: 1 },
      { num: 2, hit: true, miss: 0 },
      { num: 3, hit: true, miss: 0 },
    ])
    // 002: 1中(0) 2未中(1) 3未中(2)
    expect(byIssue['002']).toEqual([
      { num: 1, hit: true, miss: 0 },
      { num: 2, hit: false, miss: 1 },
      { num: 3, hit: false, miss: 2 },
    ])
  })
})

describe('intervalTrend', () => {
  const draws = [
    { issue: '002', draw_date: '2026-06-02', numbers: { red: [1, 2, 9] } },
    { issue: '001', draw_date: '2026-06-01', numbers: { red: [4, 5, 6] } },
  ]
  const t = intervalTrend(draws, 'red', 1, 9, 3)

  it('均分 3 段并标注区间', () => {
    expect(t.labels).toEqual(['1-3', '4-6', '7-9'])
  })
  it('逐期统计各段个数', () => {
    const byIssue = Object.fromEntries(t.rows.map((r) => [r.issue, r.counts]))
    expect(byIssue['002']).toEqual([2, 0, 1]) // 1,2 在 1-3；9 在 7-9
    expect(byIssue['001']).toEqual([0, 3, 0]) // 4,5,6 在 4-6
  })
})

describe('spanSeries', () => {
  const draws = [
    { issue: '002', numbers: { digits: [6, 9, 0] } },
    { issue: '001', numbers: { digits: [5, 5, 5] } },
  ]
  it('每期 max-min，从旧到新', () => {
    expect(spanSeries(draws, 'digits')).toEqual([
      { issue: '001', value: 0 },
      { issue: '002', value: 9 },
    ])
  })
})
