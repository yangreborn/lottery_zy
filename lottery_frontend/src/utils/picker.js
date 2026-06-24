import { getZones } from './zones.js'

export function toggleBall(selected, n, max) {
  if (selected.indexOf(n) >= 0) {
    return selected.filter((x) => x !== n)
  }
  if (selected.length >= max) {
    return selected
  }
  return [...selected, n].sort((a, b) => a - b)
}

export function selectionComplete(numbers, rule, picks = {}) {
  for (const zone of getZones(rule)) {
    const len = (numbers[zone.key] || []).length
    const variable = zone.pick_min !== undefined && zone.pick_max !== undefined
    const target = variable ? (picks[zone.key] ?? zone.pick_max) : zone.count
    if (len !== target) return false
  }
  return true
}

export function toggleIndex(set, i) {
  if (set.indexOf(i) >= 0) {
    return set.filter((x) => x !== i)
  }
  return [...set, i].sort((a, b) => a - b)
}
