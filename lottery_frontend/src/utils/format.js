export function ballColor(zone) {
  if (zone === 'red') return '#e53935'
  if (zone === 'blue') return '#1e88e5'
  if (zone === 'main') return '#fb8c00'
  if (zone === 'digits') return '#43a047'
  return '#9e9e9e'
}

// 立体球：径向高光渐变（中心偏左上做高光），各分区一套配色
const BALL_GRADIENTS = {
  red: 'radial-gradient(circle at 33% 28%, #f2666b, #d92b32 58%, #b3151c)',
  blue: 'radial-gradient(circle at 33% 28%, #62a0db, #2566ab 58%, #184c84)',
  main: 'radial-gradient(circle at 33% 28%, #ffb259, #fb8c00 58%, #d97600)',
  digits: 'radial-gradient(circle at 33% 28%, #7bc47f, #43a047 58%, #2f7d33)',
  default: 'radial-gradient(circle at 33% 28%, #c2bbb5, #9a928c 58%, #7c746e)',
}
// 与球色匹配的落地投影色
const BALL_SHADOWS = {
  red: 'rgba(196,30,40,.34)',
  blue: 'rgba(30,90,160,.32)',
  main: 'rgba(217,118,0,.32)',
  digits: 'rgba(47,125,51,.32)',
  default: 'rgba(124,116,110,.3)',
}

export function ballGradient(zone) {
  return BALL_GRADIENTS[zone] || BALL_GRADIENTS.default
}
export function ballShadow(zone) {
  return BALL_SHADOWS[zone] || BALL_SHADOWS.default
}

export function formatAmount(raw) {
  if (raw === null || raw === undefined || raw === '') return '—'
  const n = Number(String(raw).replace(/,/g, ''))
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString('en-US')
}

export function hasPool(raw) {
  if (raw === null || raw === undefined || raw === '') return false
  const n = Number(String(raw).replace(/,/g, ''))
  return Number.isFinite(n) && n > 0
}

export function statsTier(count, max) {
  if (!max || max <= 0) return 0
  const ratio = count / max
  if (ratio <= 0) return 0
  if (ratio >= 1) return 4
  return Math.min(4, Math.max(1, Math.ceil(ratio * 4)))
}
