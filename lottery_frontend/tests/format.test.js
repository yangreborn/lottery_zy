import { describe, it, expect } from 'vitest'
import { ballColor, formatAmount, statsTier, hasPool } from '../src/utils/format.js'

describe('ballColor', () => {
  it('红蓝灰', () => {
    expect(ballColor('red')).toBe('#e53935')
    expect(ballColor('blue')).toBe('#1e88e5')
    expect(ballColor('x')).toBe('#9e9e9e')
  })
  it('digits 绿', () => {
    expect(ballColor('digits')).toBe('#43a047')
  })
})

describe('formatAmount 千分位', () => {
  it('带逗号正确解析', () => {
    expect(formatAmount('7,110,906')).toBe('7,110,906')
    expect(formatAmount('757,966,457.83')).toBe('757,966,457.83')
  })
  it('无逗号不变', () => {
    expect(formatAmount('398183968')).toBe('398,183,968')
  })
  it('空/非法返回 —', () => {
    expect(formatAmount('')).toBe('—')
    expect(formatAmount(null)).toBe('—')
    expect(formatAmount('abc')).toBe('—')
  })
})

describe('hasPool', () => {
  it('空/0 为 false', () => {
    expect(hasPool('')).toBe(false)
    expect(hasPool(null)).toBe(false)
    expect(hasPool(undefined)).toBe(false)
    expect(hasPool('0')).toBe(false)
    expect(hasPool(0)).toBe(false)
  })
  it('正数为 true（含千分位）', () => {
    expect(hasPool('1234')).toBe(true)
    expect(hasPool(1234)).toBe(true)
    expect(hasPool('1,234,567')).toBe(true)
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
