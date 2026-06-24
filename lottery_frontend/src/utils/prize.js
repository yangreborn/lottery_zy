const CN = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
const KENO_RE = /^x(\d+)z(\d+)$/

function isEmpty(g) {
  return g.count === '' || g.count === null || g.count === undefined
}

function flatLabel(g) {
  if (g.level_label) return g.level_label
  if (typeof g.level === 'number') return `${CN[g.level] || g.level}等奖`
  return String(g.level)
}

export function normalizePrizes(grades) {
  const rows = (grades || []).filter((g) => !isEmpty(g))
  const isKeno = rows.some((g) => KENO_RE.test(String(g.level)))
  if (!isKeno) {
    return {
      grouped: false,
      flat: rows.map((g) => ({ label: flatLabel(g), count: g.count, amount: g.amount })),
    }
  }
  const map = new Map()
  for (const g of rows) {
    const m = KENO_RE.exec(String(g.level))
    if (!m) continue
    const pick = Number(m[1])
    if (!map.has(pick)) map.set(pick, [])
    map.get(pick).push({ label: `选${pick}中${m[2]}`, count: g.count, amount: g.amount })
  }
  const groups = [...map.keys()]
    .sort((a, b) => b - a)
    .map((pick) => ({ pick, label: `选${pick}`, rows: map.get(pick) }))
  return { grouped: true, groups }
}

export function stripAreaPrefix(text) {
  if (!text) return ''
  return String(text).replace(/^[^：:]*[：:]/, '')
}
