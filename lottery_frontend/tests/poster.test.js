import { describe, it, expect } from 'vitest'
import { POSTER_THEMES, buildPosterData } from '../src/utils/poster.js'

describe('POSTER_THEMES', () => {
  it('3 个主题，字段完整', () => {
    expect(POSTER_THEMES.length).toBe(3)
    for (const t of POSTER_THEMES) {
      expect(t.key).toBeTruthy()
      expect(t.label).toBeTruthy()
      expect(t.bg).toBeTruthy()
      expect(t.titleColor).toBeTruthy()
      expect(t.subColor).toBeTruthy()
    }
  })
})

describe('buildPosterData', () => {
  const detail = { issue: '2026073', draw_date: '2026-06-20', numbers: { red: [1, 2], blue: [7] } }
  it('整理 name/issue/date/zones', () => {
    const d = buildPosterData(detail, '双色球', '福彩')
    expect(d.name).toBe('双色球')
    expect(d.issue).toBe('2026073')
    expect(d.date).toBe('2026-06-20')
    expect(d.zones).toEqual([{ key: 'red', nums: [1, 2] }, { key: 'blue', nums: [7] }])
  })
  it('福彩 source 中国福彩网', () => {
    expect(buildPosterData(detail, '双色球', '福彩').source).toContain('中国福彩网')
  })
  it('体彩 source 中国体彩网', () => {
    expect(buildPosterData(detail, '大乐透', '体彩').source).toContain('中国体彩网')
  })
})
