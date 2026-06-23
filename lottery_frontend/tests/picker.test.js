import { describe, it, expect } from 'vitest'
import { toggleBall, selectionComplete } from '../src/utils/picker.js'

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
