// 走势图数据工具。draws 约定「从新到旧」(接口 history 顺序)。

// 是否数字玩法(3D/排列三)：主号码区可重复且有序。
export function isDigitGame(rule) {
  const zones = (rule && rule.zones) || []
  return zones.some((z) => z.ordered && z.allow_repeat)
}

// 号码/遗漏矩阵：行=期(新在前)，列=号码 lo..hi。
// 每格 { num, hit, miss }：hit=该期是否中出；miss=截至该期的连续遗漏(中出当期=0)。
export function numberMatrix(draws, zoneKey, lo, hi) {
  const numbers = []
  for (let n = lo; n <= hi; n++) numbers.push(n)
  const ordered = [...(draws || [])].reverse() // 从旧到新算遗漏
  const miss = {}
  numbers.forEach((n) => { miss[n] = 0 })
  const rowsOldToNew = ordered.map((d) => {
    const nums = (d.numbers && d.numbers[zoneKey]) || []
    const hitSet = new Set(nums)
    const cells = numbers.map((n) => {
      const hit = hitSet.has(n)
      miss[n] = hit ? 0 : miss[n] + 1
      return { num: n, hit, miss: miss[n] }
    })
    return { issue: d.issue, date: d.draw_date, cells }
  })
  return { numbers, rows: rowsOldToNew.reverse() } // 新在前
}

// 区间走势：把 [lo,hi] 均分 segments 段，统计每期号码落在各段的个数。
// 行=期(新在前)，counts 对应各段。
export function intervalTrend(draws, zoneKey, lo, hi, segments = 3) {
  const span = hi - lo + 1
  const size = Math.ceil(span / segments)
  const labels = []
  for (let i = 0; i < segments; i++) {
    const a = lo + i * size
    const b = Math.min(hi, a + size - 1)
    if (a > hi) break
    labels.push(`${a}-${b}`)
  }
  const segOf = (n) => Math.min(labels.length - 1, Math.floor((n - lo) / size))
  const rows = (draws || []).map((d) => {
    const nums = (d.numbers && d.numbers[zoneKey]) || []
    const counts = labels.map(() => 0)
    for (const n of nums) {
      if (n < lo || n > hi) continue
      counts[segOf(n)] += 1
    }
    return { issue: d.issue, date: d.draw_date, counts }
  })
  return { labels, rows }
}

// 跨度走势：每期 max-min（数字玩法用），从旧到新，供折线图。
export function spanSeries(draws, zoneKey) {
  const ordered = [...(draws || [])].reverse()
  return ordered.map((d) => {
    const nums = (d.numbers && d.numbers[zoneKey]) || []
    const value = nums.length ? Math.max(...nums) - Math.min(...nums) : 0
    return { issue: d.issue, value }
  })
}
