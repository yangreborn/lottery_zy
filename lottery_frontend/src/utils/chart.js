// 折线图数据与绘制工具。draws 约定为「从新到旧」(接口 history 顺序)。

// 取主号码区 key（rule_config.zones 第一个有 min/max 的区）。
export function primaryZoneKey(rule) {
  const zones = (rule && rule.zones) || []
  const z = zones.find((x) => x.min !== undefined && x.max !== undefined) || zones[0]
  return z ? z.key : ''
}

// 和值走势：每期主号码区数字之和，按时间从旧到新。
export function sumSeries(draws, zoneKey) {
  const ordered = [...(draws || [])].reverse()
  return ordered.map((d) => {
    const nums = (d.numbers && d.numbers[zoneKey]) || []
    const value = nums.reduce((s, n) => s + Number(n), 0)
    return { issue: d.issue, value }
  })
}

// 单号遗漏走势：每期该号码的连续遗漏值（出现当期=0），从旧到新。
export function missSeries(draws, zoneKey, number) {
  const ordered = [...(draws || [])].reverse()
  const out = []
  let miss = 0
  for (const d of ordered) {
    const nums = (d.numbers && d.numbers[zoneKey]) || []
    if (nums.includes(number)) miss = 0
    else miss += 1
    out.push({ issue: d.issue, value: miss })
  }
  return out
}

export function seriesRange(series) {
  if (!series || !series.length) return { min: 0, max: 1 }
  let min = Infinity
  let max = -Infinity
  for (const p of series) {
    if (p.value < min) min = p.value
    if (p.value > max) max = p.value
  }
  if (min === max) { min -= 1; max += 1 }
  return { min, max }
}

const PAD_L = 64
const PAD_R = 28
const PAD_T = 36
const PAD_B = 56

// 按点间距算出画布逻辑宽度。
export function chartWidth(pointCount, spacing) {
  const n = Math.max(1, pointCount)
  return PAD_L + PAD_R + (n - 1) * spacing
}

export function drawLineChart(ctx, series, opts, scale = 1) {
  const H = opts.height || 460
  const spacing = opts.spacing || 60
  const W = chartWidth(series.length, spacing)
  const color = opts.color || '#e53935'
  const title = opts.title || ''

  ctx.save()
  ctx.scale(scale, scale)
  ctx.setFillStyle('#ffffff')
  ctx.fillRect(0, 0, W, H)

  // 标题
  if (title) {
    ctx.setFillStyle('#333333')
    ctx.setFontSize(24)
    ctx.setTextAlign('left')
    ctx.fillText(title, PAD_L, 24)
  }

  if (!series.length) { ctx.restore(); ctx.draw(); return }

  const { min, max } = seriesRange(series)
  const plotH = H - PAD_T - PAD_B
  const plotW = W - PAD_L - PAD_R
  const xOf = (i) => PAD_L + (series.length === 1 ? plotW / 2 : (i * plotW) / (series.length - 1))
  const yOf = (v) => PAD_T + plotH - ((v - min) / (max - min)) * plotH

  // y 轴网格 + 刻度（4 段）
  ctx.setTextAlign('right')
  ctx.setFontSize(20)
  for (let g = 0; g <= 4; g++) {
    const v = min + ((max - min) * g) / 4
    const y = yOf(v)
    ctx.beginPath()
    ctx.setStrokeStyle('#eeeeee')
    ctx.moveTo(PAD_L, y)
    ctx.lineTo(W - PAD_R, y)
    ctx.stroke()
    ctx.setFillStyle('#999999')
    ctx.fillText(String(Math.round(v)), PAD_L - 8, y + 6)
  }

  // x 轴标签（稀疏，最多 ~6 个，取期号后 4 位）
  const step = Math.max(1, Math.ceil(series.length / 6))
  ctx.setTextAlign('center')
  ctx.setFillStyle('#999999')
  ctx.setFontSize(18)
  for (let i = 0; i < series.length; i += step) {
    const label = String(series[i].issue).slice(-4)
    ctx.fillText(label, xOf(i), H - PAD_B + 28)
  }

  // 折线
  ctx.beginPath()
  ctx.setStrokeStyle(color)
  ctx.setLineWidth(3)
  series.forEach((p, i) => {
    const x = xOf(i)
    const y = yOf(p.value)
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  })
  ctx.stroke()

  // 数据点
  ctx.setFillStyle(color)
  series.forEach((p, i) => {
    ctx.beginPath()
    ctx.arc(xOf(i), yOf(p.value), 4, 0, 2 * Math.PI)
    ctx.fill()
  })

  ctx.restore()
  ctx.draw()
}
