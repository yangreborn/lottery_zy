import { describe, it, expect, beforeEach } from 'vitest'
import { HOME_MENU, goMenu } from '../src/utils/menu.js'

describe('HOME_MENU', () => {
  it('4 项且字段完整', () => {
    expect(HOME_MENU.length).toBe(4)
    for (const m of HOME_MENU) {
      expect(typeof m.key).toBe('string')
      expect(typeof m.title).toBe('string')
      expect(typeof m.icon).toBe('string')
      expect(m.path.startsWith('/pages/')).toBe(true)
      expect(['switchTab', 'navigateTo']).toContain(m.nav)
    }
  })

  it('已移除 guide/picker/chart（走势图选号进底边栏），保留 notice', () => {
    const keys = HOME_MENU.map((m) => m.key)
    expect(keys).not.toContain('mine')
    expect(keys).not.toContain('feedback')
    expect(keys).not.toContain('purchase')
    expect(keys).not.toContain('latest')
    expect(keys).not.toContain('guide')
    expect(keys).not.toContain('picker')
    expect(keys).not.toContain('chart')
    expect(keys).toContain('notice')
  })

  it('导航类型与文案正确', () => {
    const byKey = Object.fromEntries(HOME_MENU.map((m) => [m.key, m]))
    // 统计不再是 tab 页，改为 navigateTo
    expect(byKey.stats.nav).toBe('navigateTo')
    expect(byKey.stats.path).toBe('/pages/draw/stats')
    expect(byKey.history.nav).toBe('navigateTo')
    expect(byKey.guide).toBeUndefined()
    expect(byKey.picker).toBeUndefined()
    expect(byKey.chart).toBeUndefined()
    expect(byKey.notice.nav).toBe('navigateTo')
    expect(byKey.notice.path).toBe('/pages/notice/index')
    expect(byKey.poster.nav).toBe('navigateTo')
  })
})

describe('goMenu', () => {
  let calls
  beforeEach(() => {
    calls = []
    globalThis.uni = {
      switchTab: (o) => calls.push(['switchTab', o.url]),
      navigateTo: (o) => calls.push(['navigateTo', o.url]),
    }
  })

  it('switchTab 项', () => {
    goMenu({ nav: 'switchTab', path: '/pages/draw/stats' })
    expect(calls).toEqual([['switchTab', '/pages/draw/stats']])
  })

  it('navigateTo 项', () => {
    goMenu({ nav: 'navigateTo', path: '/pages/draw/latest' })
    expect(calls).toEqual([['navigateTo', '/pages/draw/latest']])
  })
})
