import { describe, it, expect } from 'vitest'
import { toggleBall, selectionComplete, toggleIndex } from '../src/utils/picker.js'

describe('toggleBall', () => {
  it('未选则加入并升序', () => {
    expect(toggleBall([3, 1], 2, 6)).toEqual([1, 2, 3])
  })
  it('已选则移除', () => {
    expect(toggleBall([1, 2, 3], 2, 6)).toEqual([1, 3])
  })
  it('达上限不再加入', () => {
    expect(toggleBall([1, 2], 3, 2)).toEqual([1, 2])
  })
})

describe('selectionComplete', () => {
  const rule = { red: { count: 6, min: 1, max: 33 }, blue: { count: 1, min: 1, max: 16 } }
  it('两区都满才 true', () => {
    expect(selectionComplete({ red: [1, 2, 3, 4, 5, 6], blue: [7] }, rule)).toBe(true)
  })
  it('红区不满 false', () => {
    expect(selectionComplete({ red: [1, 2, 3], blue: [7] }, rule)).toBe(false)
  })
  it('蓝区缺 false', () => {
    expect(selectionComplete({ red: [1, 2, 3, 4, 5, 6], blue: [] }, rule)).toBe(false)
  })
})

describe('toggleIndex', () => {
  it('未选则加入并升序', () => {
    expect(toggleIndex([2, 0], 1)).toEqual([0, 1, 2])
  })
  it('已选则移除', () => {
    expect(toggleIndex([0, 1, 2], 1)).toEqual([0, 2])
  })
})

describe('selectionComplete zones', () => {
  const ssqRule = { red: { count: 6, min: 1, max: 33 }, blue: { count: 1, min: 1, max: 16 } }
  const kenoRule = { zones: [{ key: 'main', min: 1, max: 80, count: 20, pick_min: 1, pick_max: 10 }] }

  it('ssq 红6蓝1 完整', () => {
    expect(selectionComplete({ red: [1, 2, 3, 4, 5, 6], blue: [7] }, ssqRule)).toBe(true)
    expect(selectionComplete({ red: [1, 2, 3], blue: [7] }, ssqRule)).toBe(false)
  })
  it('keno 按 picks 目标个数', () => {
    expect(selectionComplete({ main: [1, 2, 3, 4, 5] }, kenoRule, { main: 5 })).toBe(true)
    expect(selectionComplete({ main: [1, 2, 3] }, kenoRule, { main: 5 })).toBe(false)
  })
})
