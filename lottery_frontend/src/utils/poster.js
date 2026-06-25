import { ballColor } from './format.js'

export const POSTER_THEMES = [
  { key: 'red', label: '红色喜庆', bg: '#c62828', bg2: '#7a0e12', card: 'rgba(255,255,255,0.10)', titleColor: '#ffffff', subColor: '#ffd9d4', accent: '#ffd54f' },
  { key: 'gold', label: '金色尊贵', bg: '#3a3322', bg2: '#1b1810', card: 'rgba(245,197,24,0.12)', titleColor: '#f5c518', subColor: '#d8c082', accent: '#f5c518' },
  { key: 'blue', label: '蓝色简约', bg: '#1565c0', bg2: '#0a2c57', card: 'rgba(255,255,255,0.12)', titleColor: '#ffffff', subColor: '#cfe3ff', accent: '#80d8ff' },
]

export function buildPosterData(detail, lottery) {
  const zoneMeta = {}
  const zones = (lottery && lottery.rule_config && lottery.rule_config.zones) || []
  for (const z of zones) zoneMeta[z.key] = z
  return {
    name: lottery ? lottery.name : '',
    issue: detail.issue,
    date: detail.draw_date,
    zones: Object.entries(detail.numbers || {}).map(([key, nums]) => {
      const m = zoneMeta[key] || {}
      return { key, nums, label: m.label || key, color: m.color || ballColor(key) }
    }),
    source: lottery && lottery.category === '体彩' ? 'sporttery.cn' : 'cwl.gov.cn',
  }
}

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.arc(x + w - r, y + r, r, -Math.PI / 2, 0)
  ctx.lineTo(x + w, y + h - r)
  ctx.arc(x + w - r, y + h - r, r, 0, Math.PI / 2)
  ctx.lineTo(x + r, y + h)
  ctx.arc(x + r, y + h - r, r, Math.PI / 2, Math.PI)
  ctx.lineTo(x, y + r)
  ctx.arc(x + r, y + r, r, Math.PI, Math.PI * 1.5)
  ctx.closePath()
}

export function drawPoster(ctx, data, theme, scale = 1) {
  const W = 600, H = 840
  ctx.scale(scale, scale)

  // 背景渐变
  const grad = ctx.createLinearGradient(0, 0, 0, H)
  grad.addColorStop(0, theme.bg)
  grad.addColorStop(1, theme.bg2)
  ctx.setFillStyle(grad)
  ctx.fillRect(0, 0, W, H)

  ctx.setTextAlign('center')

  // 顶部小标签
  ctx.setFillStyle(theme.accent)
  ctx.setFontSize(24)
  ctx.fillText('开 奖 公 告', W / 2, 86)

  // 彩种名
  ctx.setFillStyle(theme.titleColor)
  ctx.setFontSize(56)
  ctx.fillText(data.name, W / 2, 150)

  // 期号·日期 胶囊
  const pillW = 380, pillH = 52, pillX = (W - pillW) / 2, pillY = 178
  roundRect(ctx, pillX, pillY, pillW, pillH, pillH / 2)
  ctx.setFillStyle('rgba(0,0,0,0.20)')
  ctx.fill()
  ctx.setFillStyle(theme.subColor)
  ctx.setFontSize(26)
  ctx.fillText(`第 ${data.issue} 期  ·  ${data.date}`, W / 2, pillY + 35)

  // 号码卡片
  const cardX = 40, cardY = 262, cardW = W - 80, cardH = H - cardY - 116
  roundRect(ctx, cardX, cardY, cardW, cardH, 28)
  ctx.setFillStyle(theme.card)
  ctx.fill()

  // 号码分区
  const r = 34, gap = 84
  const innerW = cardW - 60
  const perRow = Math.max(1, Math.floor(innerW / gap))
  let y = cardY + 78
  for (const zone of data.zones) {
    const nums = zone.nums || []
    const pad = zone.key === 'digits' ? 1 : 2

    // 区名（左对齐）
    ctx.setTextAlign('left')
    ctx.setFillStyle(theme.subColor)
    ctx.setFontSize(24)
    ctx.fillText(zone.label, cardX + 30, y - r - 6)
    ctx.setTextAlign('center')

    for (let i = 0; i < nums.length; i += perRow) {
      const rowNums = nums.slice(i, i + perRow)
      let x = W / 2 - ((rowNums.length - 1) * gap) / 2
      for (const num of rowNums) {
        // 球体（带阴影）
        ctx.setShadow(0, 3, 6, 'rgba(0,0,0,0.30)')
        ctx.beginPath()
        ctx.arc(x, y, r, 0, 2 * Math.PI)
        ctx.setFillStyle(zone.color)
        ctx.fill()
        ctx.setShadow(0, 0, 0, 'rgba(0,0,0,0)')
        // 高光
        ctx.beginPath()
        ctx.arc(x - r * 0.3, y - r * 0.34, r * 0.26, 0, 2 * Math.PI)
        ctx.setFillStyle('rgba(255,255,255,0.35)')
        ctx.fill()
        // 数字
        ctx.setFillStyle('#ffffff')
        ctx.setFontSize(32)
        ctx.fillText(String(num).padStart(pad, '0'), x, y + 11)
        x += gap
      }
      y += 82
    }
    y += 28
  }

  // 底栏：来源网址 + 品牌
  ctx.setTextAlign('center')
  ctx.setFillStyle(theme.subColor)
  ctx.setFontSize(22)
  ctx.fillText(data.source, W / 2, H - 54)
  ctx.setFillStyle(theme.accent)
  ctx.setFontSize(20)
  ctx.fillText('彩票工具', W / 2, H - 26)

  ctx.draw()
}
