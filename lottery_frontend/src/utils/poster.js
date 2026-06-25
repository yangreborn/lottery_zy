import { ballColor } from './format.js'

export const POSTER_THEMES = [
  { key: 'red', label: '红色喜庆', bg: '#e53935', titleColor: '#ffffff', subColor: '#ffd9d4' },
  { key: 'gold', label: '金色尊贵', bg: '#2e2a1f', titleColor: '#f5c518', subColor: '#c8a85a' },
  { key: 'blue', label: '蓝色简约', bg: '#1e88e5', titleColor: '#ffffff', subColor: '#cfe3ff' },
]

export function buildPosterData(detail, lotteryName, category) {
  return {
    name: lotteryName,
    issue: detail.issue,
    date: detail.draw_date,
    zones: Object.entries(detail.numbers || {}).map(([key, nums]) => ({ key, nums })),
    source: category === '体彩' ? '数据来源：中国体彩网 sporttery.cn' : '数据来源：中国福彩网 cwl.gov.cn',
  }
}

export function drawPoster(ctx, data, theme) {
  const W = 600, H = 840
  ctx.setFillStyle(theme.bg)
  ctx.fillRect(0, 0, W, H)

  ctx.setTextAlign('center')
  ctx.setFillStyle(theme.titleColor)
  ctx.setFontSize(48)
  ctx.fillText(data.name, W / 2, 130)

  ctx.setFillStyle(theme.subColor)
  ctx.setFontSize(28)
  ctx.fillText(`第 ${data.issue} 期 · ${data.date}`, W / 2, 190)

  let y = 340
  const r = 38
  const gap = 92
  const perRow = Math.max(1, Math.floor(W / gap))
  for (const zone of data.zones) {
    const nums = zone.nums || []
    const pad = zone.key === 'digits' ? 1 : 2
    for (let i = 0; i < nums.length; i += perRow) {
      const rowNums = nums.slice(i, i + perRow)
      let x = (W - rowNums.length * gap) / 2 + gap / 2
      for (const num of rowNums) {
        ctx.beginPath()
        ctx.arc(x, y, r, 0, 2 * Math.PI)
        ctx.setFillStyle(ballColor(zone.key))
        ctx.fill()
        ctx.setFillStyle('#ffffff')
        ctx.setFontSize(34)
        ctx.fillText(String(num).padStart(pad, '0'), x, y + 12)
        x += gap
      }
      y += 100
    }
    y += 16
  }

  ctx.setFillStyle(theme.subColor)
  ctx.setFontSize(22)
  ctx.fillText(data.source, W / 2, H - 60)
  ctx.draw()
}
