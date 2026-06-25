import { describe, it, expect } from 'vitest'
import { POSTER_THEMES, buildPosterData } from '../src/utils/poster.js'
import { ballColor } from '../src/utils/format.js'

describe('POSTER_THEMES', () => {
  it('3 套主题，含渐变/卡片/强调字段', () => {
    expect(POSTER_THEMES.length).toBe(3)
    for (const t of POSTER_THEMES) {
      expect(t.key).toBeTruthy()
      expect(t.label).toBeTruthy()
      expect(t.bg).toBeTruthy()
      expect(t.bg2).toBeTruthy()
      expect(t.card).toBeTruthy()
      expect(t.titleColor).toBeTruthy()
      expect(t.subColor).toBeTruthy()
      expect(t.accent).toBeTruthy()
    }
  })
})

describe('buildPosterData', () => {
  const lottery = {
    name: '双色球', category: '福彩',
    rule_config: { zones: [
      { key: 'red', label: '红球', color: '#e53935' },
      { key: 'blue', label: '蓝球', color: '#1e88e5' },
    ] },
  }
  const detail = { issue: '2026073', draw_date: '2026-06-20', numbers: { red: [1, 2], blue: [7] } }

  it('整理 name/issue/date 与带 label/color 的 zones', () => {
    const d = buildPosterData(detail, lottery)
    expect(d.name).toBe('双色球')
    expect(d.issue).toBe('2026073')
    expect(d.date).toBe('2026-06-20')
    expect(d.zones).toEqual([
      { key: 'red', nums: [1, 2], label: '红球', color: '#e53935' },
      { key: 'blue', nums: [7], label: '蓝球', color: '#1e88e5' },
    ])
  })

  it('rule_config 缺该 zone 时 label 回退 key、color 回退 ballColor', () => {
    const bare = { name: '双色球', category: '福彩', rule_config: { zones: [] } }
    const d = buildPosterData(detail, bare)
    expect(d.zones[0]).toEqual({ key: 'red', nums: [1, 2], label: 'red', color: ballColor('red') })
  })

  it('福彩 source 为 cwl.gov.cn 且不含「数据来源」', () => {
    const d = buildPosterData(detail, lottery)
    expect(d.source).toBe('cwl.gov.cn')
    expect(d.source).not.toContain('数据来源')
  })

  it('体彩 source 为 sporttery.cn', () => {
    const dlt = { name: '超级大乐透', category: '体彩', rule_config: { zones: [] } }
    expect(buildPosterData(detail, dlt).source).toBe('sporttery.cn')
  })
})
