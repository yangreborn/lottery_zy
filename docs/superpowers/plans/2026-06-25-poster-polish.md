# 开奖海报优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复海报 canvas 截断（rpx/px 坐标错配），并重绘 `drawPoster` 让海报更美观。

**Architecture:** 保持 600×840 设计坐标系，页面用 `uni.upx2px` 算缩放因子传入 `drawPoster`，函数内 `ctx.scale` 适配真实画布；`drawPoster` 重绘为渐变背景 + 标题 + 期号胶囊 + 号码卡片（分区标签 + 阴影球）+ 来源/品牌底栏。zone 标签与颜色取自 `rule_config.zones`。

**Tech Stack:** uni-app (Vue3 setup) + uni canvas (createCanvasContext) + vitest。

## Global Constraints

- 纯前端改动，无后端 / 无新依赖。
- 设计坐标系固定 `W=600, H=840`；缩放因子 `scale = uni.upx2px(600) / 600`，在 `drawPoster` 开头 `ctx.scale(scale, scale)`。
- 数据来源底栏只显示网址（体彩 `sporttery.cn`，其它 `cwl.gov.cn`），不含「数据来源」字样（note 31 方向）。
- zone 球颜色优先 `zone.color`（来自 rule_config），回退 `ballColor(key)`；zone 标签优先 `rule_config.zones[].label`，回退 key。
- 回复与注释用中文。

---

### Task 1: poster.js —— 主题、buildPosterData、drawPoster(scale)

**Files:**
- Modify: `lottery_frontend/src/utils/poster.js`（整文件重写）
- Test: `lottery_frontend/tests/poster.test.js`

**Interfaces:**
- Consumes: `ballColor(key)` from `src/utils/format.js`。
- Produces:
  - `POSTER_THEMES`: `[{ key, label, bg, bg2, card, titleColor, subColor, accent }]`（3 套）。
  - `buildPosterData(detail, lottery)` → `{ name, issue, date, zones:[{key,nums,label,color}], source }`。
  - `drawPoster(ctx, data, theme, scale)` —— 供 index.vue 调用。

- [ ] **Step 1: 改写测试 `tests/poster.test.js`**

```js
import { describe, it, expect } from 'vitest'
import { POSTER_THEMES, buildPosterData } from '../src/utils/poster.js'
import { ballColor } from '../src/utils/format.js'

describe('POSTER_THEMES', () => {
  it('3 套主题，含渐变/卡片/强调字段', () => {
    expect(POSTER_THEMES.length).toBe(3)
    for (const t of POSTER_THEMES) {
      expect(t.key).toBeTruthy()
      expect(t.label).toBeTruthy()
      expect(t.bg).toBeTruthy()
      expect(t.bg2).toBeTruthy()
      expect(t.card).toBeTruthy()
      expect(t.titleColor).toBeTruthy()
      expect(t.subColor).toBeTruthy()
      expect(t.accent).toBeTruthy()
    }
  })
})

describe('buildPosterData', () => {
  const lottery = {
    name: '双色球', category: '福彩',
    rule_config: { zones: [
      { key: 'red', label: '红球', color: '#e53935' },
      { key: 'blue', label: '蓝球', color: '#1e88e5' },
    ] },
  }
  const detail = { issue: '2026073', draw_date: '2026-06-20', numbers: { red: [1, 2], blue: [7] } }

  it('整理 name/issue/date 与带 label/color 的 zones', () => {
    const d = buildPosterData(detail, lottery)
    expect(d.name).toBe('双色球')
    expect(d.issue).toBe('2026073')
    expect(d.date).toBe('2026-06-20')
    expect(d.zones).toEqual([
      { key: 'red', nums: [1, 2], label: '红球', color: '#e53935' },
      { key: 'blue', nums: [7], label: '蓝球', color: '#1e88e5' },
    ])
  })

  it('rule_config 缺该 zone 时 label 回退 key、color 回退 ballColor', () => {
    const bare = { name: '双色球', category: '福彩', rule_config: { zones: [] } }
    const d = buildPosterData(detail, bare)
    expect(d.zones[0]).toEqual({ key: 'red', nums: [1, 2], label: 'red', color: ballColor('red') })
  })

  it('福彩 source 为 cwl.gov.cn 且不含「数据来源」', () => {
    const d = buildPosterData(detail, lottery)
    expect(d.source).toBe('cwl.gov.cn')
    expect(d.source).not.toContain('数据来源')
  })

  it('体彩 source 为 sporttery.cn', () => {
    const dlt = { name: '超级大乐透', category: '体彩', rule_config: { zones: [] } }
    expect(buildPosterData(detail, dlt).source).toBe('sporttery.cn')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_frontend && npm test -- poster`
Expected: FAIL（buildPosterData 旧签名、主题缺 bg2/card/accent）。

- [ ] **Step 3: 重写 `src/utils/poster.js`**

```js
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd lottery_frontend && npm test -- poster`
Expected: PASS（POSTER_THEMES + buildPosterData 全绿）。

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/utils/poster.js lottery_frontend/tests/poster.test.js
git commit -m "feat(poster): 主题扩展 + buildPosterData 取 rule_config 标签/颜色 + drawPoster 支持 scale 与美化"
```

---

### Task 2: poster/index.vue —— 缩放绘制、传 lottery 对象、高清导出

**Files:**
- Modify: `lottery_frontend/src/pages/poster/index.vue`

**Interfaces:**
- Consumes: `buildPosterData(detail, lottery)`、`drawPoster(ctx, data, theme, scale)`（Task 1）。

- [ ] **Step 1: 用整盘 lottery 对象构建海报数据**

把 `curName()` / `curCategory()` 两个辅助替换为 `curLottery()`，并更新 `chooseIssue`：

```js
function curLottery() {
  return (
    lotteries.value.find((x) => x.code === store.code) ||
    { name: store.code, category: '福彩', rule_config: { zones: [] } }
  )
}
```

```js
async function chooseIssue(it) {
  try {
    const detail = await getDetail(store.code, it.issue)
    posterData = buildPosterData(detail, curLottery())
    curIssue.value = it.issue
    redraw()
  } catch (e) {
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}
```

删除原 `curName()` 与 `curCategory()` 定义（已被 `curLottery()` 取代）。

- [ ] **Step 2: redraw 传缩放因子**

```js
function redraw() {
  if (!posterData) return
  const ctx = uni.createCanvasContext('poster')
  const scale = uni.upx2px(600) / 600
  drawPoster(ctx, posterData, curTheme(), scale)
}
```

- [ ] **Step 3: 导出高清图**

把 `save()` 中的 `canvasToTempFilePath` 调用补上真实尺寸与 2× 输出：

```js
function save() {
  if (!curIssue.value) { uni.showToast({ title: '请先选择期次', icon: 'none' }); return }
  uni.canvasToTempFilePath({
    canvasId: 'poster',
    width: uni.upx2px(600),
    height: uni.upx2px(840),
    destWidth: 1200,
    destHeight: 1680,
    success: (r) => {
      uni.saveImageToPhotosAlbum({
        filePath: r.tempFilePath,
        success: () => uni.showToast({ title: '已保存到相册', icon: 'success' }),
        fail: () => uni.showToast({ title: '请在设置中开启相册权限', icon: 'none' }),
      })
    },
    fail: () => uni.showToast({ title: '请在微信小程序中保存', icon: 'none' }),
  })
}
```

- [ ] **Step 4: 全量前端测试回归**

Run: `cd lottery_frontend && npm test`
Expected: PASS（无回归；index.vue 无单测，靠 poster.js 单测覆盖逻辑）。

- [ ] **Step 5: 提交**

```bash
git add lottery_frontend/src/pages/poster/index.vue
git commit -m "feat(poster): 页面按真实像素缩放绘制并导出 2x 高清海报"
```

---

## Self-Review

**Spec coverage:**
- note 26 截断 → Task 1 `drawPoster(scale)` + Task 2 `redraw` 缩放、Task 2 高清导出 ✓
- note 27 美化 → Task 1 渐变背景/标题/胶囊/卡片/分区标签/阴影球/底栏 ✓
- zone 标签/颜色取自 rule_config → Task 1 buildPosterData ✓
- 来源只显示网址 → Task 1 source ✓

**Placeholder scan:** 无 TBD/TODO；每个代码步骤含完整代码。

**Type consistency:** `buildPosterData(detail, lottery)`、`drawPoster(ctx, data, theme, scale)`、zone 形状 `{key,nums,label,color}` 在 Task 1/2/测试中一致；`curLottery()` 返回带 `rule_config.zones` 的对象，与 buildPosterData 期望一致。
