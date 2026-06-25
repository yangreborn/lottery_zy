import { describe, it, expect, beforeEach } from 'vitest'
import { HOME_MENU, goMenu } from '../src/utils/menu.js'

describe('HOME_MENU', () => {
  it('6 项且字段完整', () => {
    expect(HOME_MENU.length).toBe(8)
    for (const m of HOME_MENU) {
      expect(typeof m.key).toBe('string')
      expect(typeof m.title).toBe('string')
      expect(typeof m.icon).toBe('string')
      expect(m.path.startsWith('/pages/')).toBe(true)
      expect(['switchTab', 'navigateTo']).toContain(m.nav)
    }
  })

  it('tabBar 目标用 switchTab，非 tab 用 navigateTo', () => {
    const byKey = Object.fromEntries(HOME_MENU.map((m) => [m.key, m]))
    expect(byKey.stats.nav).toBe('switchTab')
    expect(byKey.picker.nav).toBe('switchTab')
    expect(byKey.mine.nav).toBe('switchTab')
    expect(byKey.latest.nav).toBe('navigateTo')
    expect(byKey.history.nav).toBe('navigateTo')
    expect(byKey.guide.nav).toBe('navigateTo')
    expect(byKey.feedback.nav).toBe('navigateTo')
    expect(byKey.purchase.nav).toBe('navigateTo')
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
