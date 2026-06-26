import { describe, it, expect } from 'vitest'
import { primaryZoneKey, sumSeries, missSeries, seriesRange, chartWidth, clampWindow } from '../src/utils/chart.js'

describe('primaryZoneKey', () => {
  it('取第一个带 min/max 的号码区', () => {
    const rule = { zones: [{ key: 'red', min: 1, max: 33 }, { key: 'blue', min: 1, max: 16 }] }
    expect(primaryZoneKey(rule)).toBe('red')
  })
  it('无 zones 返回空串', () => {
    expect(primaryZoneKey({})).toBe('')
    expect(primaryZoneKey(null)).toBe('')
  })
})

describe('sumSeries', () => {
  // 接口顺序：从新到旧
  const draws = [
    { issue: '003', numbers: { red: [1, 2, 3], blue: [5] } },
    { issue: '002', numbers: { red: [10, 20], blue: [1] } },
    { issue: '001', numbers: { red: [4, 4, 4], blue: [2] } },
  ]
  it('按时间从旧到新输出主区和值', () => {
    expect(sumSeries(draws, 'red')).toEqual([
      { issue: '001', value: 12 },
      { issue: '002', value: 30 },
      { issue: '003', value: 6 },
    ])
  })
  it('缺该区数字按 0 处理', () => {
    expect(sumSeries([{ issue: '1', numbers: {} }], 'red')).toEqual([{ issue: '1', value: 0 }])
  })
})

describe('missSeries', () => {
  const draws = [
    { issue: '004', numbers: { red: [9] } },
    { issue: '003', numbers: { red: [5, 9] } },
    { issue: '002', numbers: { red: [1] } },
    { issue: '001', numbers: { red: [5] } },
  ]
  it('出现当期=0，缺席逐期累加', () => {
    // 时间从旧到新: 001(含5→0) 002(无5→1) 003(含5→0) 004(无5→1)
    expect(missSeries(draws, 'red', 5)).toEqual([
      { issue: '001', value: 0 },
      { issue: '002', value: 1 },
      { issue: '003', value: 0 },
      { issue: '004', value: 1 },
    ])
  })
  it('始终不出现则持续累加', () => {
    expect(missSeries(draws, 'red', 7).map((p) => p.value)).toEqual([1, 2, 3, 4])
  })
})

describe('seriesRange', () => {
  it('返回最小最大', () => {
    expect(seriesRange([{ value: 3 }, { value: 8 }, { value: 5 }])).toEqual({ min: 3, max: 8 })
  })
  it('全相等时上下各扩 1 避免除零', () => {
    expect(seriesRange([{ value: 5 }, { value: 5 }])).toEqual({ min: 4, max: 6 })
  })
  it('空序列回退 0..1', () => {
    expect(seriesRange([])).toEqual({ min: 0, max: 1 })
  })
})

describe('chartWidth', () => {
  it('随点数与间距增长（缩放放大变宽）', () => {
    expect(chartWidth(10, 60)).toBeLessThan(chartWidth(10, 120))
    expect(chartWidth(5, 60)).toBeLessThan(chartWidth(20, 60))
  })
})

describe('clampWindow', () => {
  it('正常窗口原样返回', () => {
    expect(clampWindow(100, 10, 20)).toEqual({ start: 10, size: 20 })
  })
  it('size 超过 total 时截到 total', () => {
    expect(clampWindow(15, 0, 30)).toEqual({ start: 0, size: 15 })
  })
  it('start 越界回拉到末尾窗口', () => {
    expect(clampWindow(50, 999, 10)).toEqual({ start: 40, size: 10 })
  })
  it('start 负值回 0', () => {
    expect(clampWindow(50, -5, 10)).toEqual({ start: 0, size: 10 })
  })
  it('size 最小为 2', () => {
    expect(clampWindow(50, 0, 1)).toEqual({ start: 0, size: 2 })
  })
  it('空数据返回 0/0', () => {
    expect(clampWindow(0, 0, 10)).toEqual({ start: 0, size: 0 })
  })
})
