export function ballColor(zone) {
  if (zone === 'red') return '#e53935'
  if (zone === 'blue') return '#1e88e5'
  if (zone === 'main') return '#fb8c00'
  if (zone === 'digits') return '#43a047'
  return '#9e9e9e'
}

export function formatAmount(raw) {
  if (raw === null || raw === undefined || raw === '') return '—'
  const n = Number(String(raw).replace(/,/g, ''))
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString('en-US')
}

export function statsTier(count, max) {
  if (!max || max <= 0) return 0
  const ratio = count / max
  if (ratio <= 0) return 0
  if (ratio >= 1) return 4
  return Math.min(4, Math.max(1, Math.ceil(ratio * 4)))
}
