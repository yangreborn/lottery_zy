import { describe, it, expect } from 'vitest'
import {
  POSTER_THEMES,
  buildPosterData,
  MERGE_PRESETS,
  presetCodes,
  buildMergedPosterData,
  measureMerged,
} from '../src/utils/poster.js'
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

describe('合并海报', () => {
  const lotteries = [
    { code: 'ssq', name: '双色球', category: '福彩' },
    { code: '3d', name: '福彩3D', category: '福彩' },
    { code: 'dlt', name: '超级大乐透', category: '体彩' },
    { code: 'pl3', name: '排列三', category: '体彩' },
  ]

  it('MERGE_PRESETS 含福彩/体彩/自定义', () => {
    expect(MERGE_PRESETS.map((p) => p.key)).toEqual(['fc', 'tc', 'custom'])
  })

  it('presetCodes 按 category 过滤彩种', () => {
    expect(presetCodes('fc', lotteries)).toEqual(['ssq', '3d'])
    expect(presetCodes('tc', lotteries)).toEqual(['dlt', 'pl3'])
  })

  it('presetCodes custom 用传入的勾选 codes', () => {
    expect(presetCodes('custom', lotteries, ['ssq', 'dlt'])).toEqual(['ssq', 'dlt'])
  })

  it('buildMergedPosterData 组装每条 entry 并过滤无效项', () => {
    const items = [
      {
        detail: { issue: '2026001', draw_date: '2026-06-01', numbers: { red: [1, 2], blue: [7] } },
        lottery: { name: '双色球', category: '福彩', rule_config: { zones: [{ key: 'red', label: '红球', color: '#e53935' }] } },
      },
      null,
      { detail: null, lottery: {} },
    ]
    const d = buildMergedPosterData(items, '福彩开奖')
    expect(d.title).toBe('福彩开奖')
    expect(d.entries.length).toBe(1)
    expect(d.entries[0].name).toBe('双色球')
    expect(d.entries[0].issue).toBe('2026001')
    expect(d.entries[0].zones[0].label).toBe('红球')
  })

  it('measureMerged 返回随 entry 数增长的总高度', () => {
    const mk = (n) => ({ title: 'x', entries: Array.from({ length: n }, () => ({
      name: '双色球', issue: '1', date: '2026-06-01',
      zones: [{ key: 'red', label: '红球', color: '#e53935', nums: [1, 2, 3, 4, 5, 6] }],
    })) })
    const one = measureMerged(mk(1))
    const three = measureMerged(mk(3))
    expect(one.W).toBe(600)
    expect(one.entries.length).toBe(1)
    expect(three.entries.length).toBe(3)
    expect(three.H).toBeGreaterThan(one.H)
    // 卡片自上而下排布，第二张在第一张之下
    expect(three.entries[1].top).toBeGreaterThan(three.entries[0].top)
  })

  it('measureMerged 空 entries 仍返回正高度', () => {
    const m = measureMerged({ title: 'x', entries: [] })
    expect(m.H).toBeGreaterThan(0)
    expect(m.entries).toEqual([])
  })
})
