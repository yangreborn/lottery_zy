import { describe, it, expect } from 'vitest'
import { formatAmount } from '../src/utils/format.js'

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
