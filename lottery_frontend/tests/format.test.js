import { describe, it, expect } from 'vitest'
import { ballColor, formatAmount, statsTier } from '../src/utils/format.js'

describe('ballColor', () => {
  it('红蓝灰', () => {
    expect(ballColor('red')).toBe('#e53935')
    expect(ballColor('blue')).toBe('#1e88e5')
    expect(ballColor('x')).toBe('#9e9e9e')
  })
})

describe('formatAmount', () => {
  it('千分位', () => {
    expect(formatAmount('1532000000')).toBe('1,532,000,000')
    expect(formatAmount('1000')).toBe('1,000')
  })
  it('空或非法返回破折号', () => {
    expect(formatAmount('')).toBe('—')
    expect(formatAmount(null)).toBe('—')
    expect(formatAmount('abc')).toBe('—')
  })
})

describe('statsTier', () => {
  it('按占比分 0..4', () => {
    expect(statsTier(0, 10)).toBe(0)
    expect(statsTier(10, 10)).toBe(4)
    expect(statsTier(5, 10)).toBe(2)
  })
  it('max<=0 返回 0', () => {
    expect(statsTier(3, 0)).toBe(0)
  })
})
