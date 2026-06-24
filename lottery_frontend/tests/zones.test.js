import { describe, it, expect } from 'vitest'
import { getZones, zoneLabel, zoneColor } from '../src/utils/zones.js'

describe('getZones', () => {
  it('新 zones 格式直返', () => {
    const rc = { zones: [{ key: 'main', label: '号码', min: 1, max: 80, count: 20, pick_min: 1, pick_max: 10 }] }
    expect(getZones(rc).map((z) => z.key)).toEqual(['main'])
  })
  it('老 red/blue 转换', () => {
    const rc = { red: { count: 6, min: 1, max: 33 }, blue: { count: 1, min: 1, max: 16 } }
    const z = getZones(rc)
    expect(z.map((x) => x.key)).toEqual(['red', 'blue'])
    expect(z[0].label).toBe('红球')
    expect(z[0].count).toBe(6)
  })
  it('空返回 []', () => {
    expect(getZones(null)).toEqual([])
    expect(getZones({})).toEqual([])
  })
})

describe('zoneLabel / zoneColor', () => {
  it('已知 key 映射', () => {
    expect(zoneLabel('main')).toBe('号码')
    expect(zoneColor('main')).toBe('#fb8c00')
  })
  it('未知回退', () => {
    expect(zoneLabel('xx')).toBe('xx')
    expect(zoneColor('xx')).toBe('#9e9e9e')
  })
})
