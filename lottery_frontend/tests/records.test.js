import { describe, it, expect } from 'vitest'
import { formatTime, groupRecords, todayStr } from '../src/utils/records.js'

describe('formatTime', () => {
  it('格式化为 YYYY-MM-DD HH:mm', () => {
    expect(formatTime('2026-06-23T10:05:00')).toBe('2026-06-23 10:05')
  })

  it('空/非法返回空串', () => {
    expect(formatTime('')).toBe('')
    expect(formatTime(null)).toBe('')
    expect(formatTime('not-a-date')).toBe('')
  })
})

describe('todayStr', () => {
  it('返回 YYYY-MM-DD 格式', () => {
    expect(todayStr()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})

describe('groupRecords', () => {
  const items = [
    { id: 1, group_name: 'B组' },
    { id: 2, group_name: '' },
    { id: 3, group_name: 'A组' },
    { id: 4, group_name: 'A组' },
    { id: 5 },
  ]

  it('按组分块，命名组升序在前，未分组殿后', () => {
    const g = groupRecords(items)
    expect(g.map((x) => x.name)).toEqual(['A组', 'B组', '未分组'])
    expect(g[0].records.map((r) => r.id)).toEqual([3, 4])
    expect(g[2].records.map((r) => r.id)).toEqual([2, 5])
  })

  it('空/非数组返回 []', () => {
    expect(groupRecords([])).toEqual([])
    expect(groupRecords(null)).toEqual([])
  })

  it('不改入参', () => {
    const before = items.map((x) => x.id)
    groupRecords(items)
    expect(items.map((x) => x.id)).toEqual(before)
  })
})
