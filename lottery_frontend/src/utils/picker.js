export function toggleBall(selected, n, max) {
  if (selected.indexOf(n) >= 0) {
    return selected.filter((x) => x !== n)
  }
  if (selected.length >= max) {
    return selected
  }
  return [...selected, n].sort((a, b) => a - b)
}

export function selectionComplete(numbers, rule) {
  for (const zone of ['red', 'blue']) {
    const r = rule[zone]
    if (!r) continue
    if ((numbers[zone] || []).length !== r.count) return false
  }
  return true
}

export function toggleIndex(set, i) {
  if (set.indexOf(i) >= 0) {
    return set.filter((x) => x !== i)
  }
  return [...set, i].sort((a, b) => a - b)
}
