import { describe, it, expect } from 'vitest'
import { sortCells } from '../src/utils/statsort.js'

const CELLS = [
  { number: 3, count: 5, miss: 0 },
  { number: 1, count: 8, miss: 1 },
  { number: 2, count: 5, miss: 2 },
  { number: 5, count: 2, miss: 3 },
]

describe('sortCells', () => {
  it('number 按号码升序', () => {
    expect(sortCells(CELLS, 'number').map((c) => c.number)).toEqual([1, 2, 3, 5])
  })

  it('most 按 count 降序，平手按号码升序', () => {
    // count: 1->8, 2->5, 3->5, 5->2 ; 平手 2、3 按号码升序
    expect(sortCells(CELLS, 'most').map((c) => c.number)).toEqual([1, 2, 3, 5])
  })

  it('least 按 count 升序，平手按号码升序', () => {
    expect(sortCells(CELLS, 'least').map((c) => c.number)).toEqual([5, 2, 3, 1])
  })

  it('不可变(不改入参)', () => {
    const before = CELLS.map((c) => c.number)
    sortCells(CELLS, 'most')
    expect(CELLS.map((c) => c.number)).toEqual(before)
  })

  it('空/非数组返回 []', () => {
    expect(sortCells([], 'most')).toEqual([])
    expect(sortCells(null, 'most')).toEqual([])
    expect(sortCells(undefined, 'number')).toEqual([])
  })
})
