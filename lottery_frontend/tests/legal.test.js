import { describe, it, expect } from 'vitest'
import { LEGAL_DOCS, getLegalDoc } from '../src/utils/legal.js'

describe('legal docs', () => {
  it('含 agreement/privacy 两份且各有标题+非空段落', () => {
    for (const k of ['agreement', 'privacy']) {
      expect(LEGAL_DOCS[k].title).toBeTruthy()
      expect(Array.isArray(LEGAL_DOCS[k].paragraphs)).toBe(true)
      expect(LEGAL_DOCS[k].paragraphs.length).toBeGreaterThan(0)
    }
  })
  it('getLegalDoc 按 type 取，未知兜底 agreement', () => {
    expect(getLegalDoc('privacy')).toBe(LEGAL_DOCS.privacy)
    expect(getLegalDoc('xx')).toBe(LEGAL_DOCS.agreement)
    expect(getLegalDoc(undefined)).toBe(LEGAL_DOCS.agreement)
  })
})
