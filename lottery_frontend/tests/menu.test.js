import { describe, it, expect, beforeEach } from 'vitest'
import { HOME_MENU, goMenu } from '../src/utils/menu.js'

describe('HOME_MENU', () => {
  it('7 项且字段完整', () => {
    expect(HOME_MENU.length).toBe(7)
    for (const m of HOME_MENU) {
      expect(typeof m.key).toBe('string')
      expect(typeof m.title).toBe('string')
      expect(typeof m.icon).toBe('string')
      expect(m.path.startsWith('/pages/')).toBe(true)
      expect(['switchTab', 'navigateTo']).toContain(m.nav)
    }
  })

  it('已移除 mine/feedback/purchase/latest，新增 notice', () => {
    const keys = HOME_MENU.map((m) => m.key)
    expect(keys).not.toContain('mine')
    expect(keys).not.toContain('feedback')
    expect(keys).not.toContain('purchase')
    expect(keys).not.toContain('latest')
    expect(keys).toContain('notice')
  })

  it('导航类型与文案正确', () => {
    const byKey = Object.fromEntries(HOME_MENU.map((m) => [m.key, m]))
    expect(byKey.stats.nav).toBe('switchTab')
    expect(byKey.picker.nav).toBe('switchTab')
    expect(byKey.history.nav).toBe('navigateTo')
    expect(byKey.guide.nav).toBe('navigateTo')
    expect(byKey.guide.title).toBe('玩法说明')
    expect(byKey.notice.nav).toBe('navigateTo')
    expect(byKey.notice.path).toBe('/pages/notice/index')
    expect(byKey.poster.nav).toBe('navigateTo')
    expect(byKey.chart.nav).toBe('navigateTo')
    expect(byKey.chart.path).toBe('/pages/chart/index')
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
