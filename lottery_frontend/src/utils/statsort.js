export function sortCells(cells, mode) {
  if (!Array.isArray(cells)) return []
  const arr = [...cells]
  if (mode === 'most') {
    arr.sort((a, b) => b.count - a.count || a.number - b.number)
  } else if (mode === 'least') {
    arr.sort((a, b) => a.count - b.count || a.number - b.number)
  } else {
    arr.sort((a, b) => a.number - b.number)
  }
  return arr
}
