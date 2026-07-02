import { reactive } from 'vue'

const STORAGE_KEY = 'app_theme'

/**
 * 主题 = 一组设计令牌（CSS 变量）。
 * 新增风格只需在 THEMES 里再加一项（给一份 mk() 的颜色对象），页面/组件零改动。
 * 令牌通过 CSS 变量下发：
 *  - H5：写到 documentElement，全局生效
 *  - 各端通用：页面根 <view> 绑定 :style="themeVarString"，变量向下继承
 */
function mk(c) {
  return {
    '--bg': c.bg,
    '--surface': c.surface,
    '--surface-2': c.surface2,
    '--border': c.border,
    '--text': c.text,
    '--text-2': c.text2,
    '--text-3': c.text3,
    '--brand': c.brand,
    '--brand-on': c.brandOn || '#ffffff',
    '--brand-soft-bg': c.softBg,
    '--brand-soft-border': c.softBorder,
    '--brand-soft-text': c.softText,
    '--accent': c.accent || c.brand,
    '--chip-bg': c.chipBg,
    '--chip-border': c.chipBorder || 'transparent',
    '--chip-text': c.chipText,
    '--shadow-card': c.shadowCard,
    '--shadow-chip': c.shadowChip,
    '--banner-bg': c.bannerBg,
    '--banner-text': c.bannerText,
    '--banner-border': c.bannerBorder || 'transparent',
    '--mask': c.mask || 'rgba(0,0,0,0.45)',
    '--ball-red': c.ballRed,
    '--ball-blue': c.ballBlue,
    '--ball-main': c.ballMain,
    '--ball-digits': c.ballDigits,
    '--ball-default': c.ballDefault,
    '--ball-glow-red': c.glowRed,
    '--ball-glow-blue': c.glowBlue,
    '--ball-glow-main': c.glowMain,
    '--ball-glow-digits': c.glowDigits,
    '--ball-glow-default': c.glowDefault,
    '--pick-red': c.pickRed,
    '--pick-blue': c.pickBlue,
    '--heat-0': c.heat[0],
    '--heat-1': c.heat[1],
    '--heat-2': c.heat[2],
    '--heat-3': c.heat[3],
    '--heat-4': c.heat[4],
    '--heat-text': c.heatText,
    '--heat-meta': c.heatMeta,
    '--trend-bar': c.trendBar,
    '--trend-bar-text': c.trendText,
    '--trend-header-bg': c.headerBg,
    '--grid-line': c.gridLine,
    '--matrix-miss': c.matrixMiss || c.text3,
  }
}

const SOFT = (rgb) => `0 6rpx 12rpx rgba(${rgb})`
const NEON = (rgb) => `0 0 16rpx rgba(${rgb})`
// 扁平号码球用的柔和落影（无外发光，配合 Ball 组件内阴影形成克制的立体感）
const FLAT = (rgb) => `0 4rpx 10rpx -4rpx rgba(${rgb})`

export const THEMES = [
  {
    key: 'light',
    name: '暖白',
    desc: '干净克制 · 官方可信',
    swatch: ['#f3efe6', '#ce3f26', '#1c1a15'],
    vars: mk({
      bg: '#f3efe6', surface: '#fcfbf7', surface2: '#efeae0', border: '#e5dfd1',
      text: '#1c1a15', text2: '#57524a', text3: '#9a9388',
      brand: '#ce3f26', softBg: '#f7e3db', softBorder: '#f0d3c6', softText: '#a8391f', accent: '#2c5f8a',
      chipBg: '#efeae0', chipText: '#57524a',
      shadowCard: '0 16rpx 36rpx -22rpx rgba(60,40,20,0.30)', shadowChip: '0 8rpx 20rpx -10rpx rgba(60,40,20,0.22)',
      bannerBg: '#fcfbf7', bannerText: '#1c1a15', bannerBorder: '#e5dfd1',
      ballRed: '#ce3f26',
      ballBlue: '#2c6bb0',
      ballMain: '#c4892c',
      ballDigits: '#3c8b5a',
      ballDefault: '#9a9388',
      glowRed: FLAT('120,50,30,0.24'), glowBlue: FLAT('30,70,120,0.22'), glowMain: FLAT('120,80,20,0.22'),
      glowDigits: FLAT('40,90,60,0.22'), glowDefault: FLAT('90,80,70,0.20'),
      pickRed: '#ce3f26', pickBlue: '#2c6bb0',
      heat: ['#efeae0', '#f4dbc0', '#ecb37b', '#de8a45', '#ce3f26'], heatText: '#1c1a15', heatMeta: '#57524a',
      trendBar: '#f7e3db', trendText: '#ce3f26', headerBg: '#f6f1e8', gridLine: '#eae4d6', matrixMiss: '#b8b0a4',
    }),
  },
  {
    key: 'dark',
    name: '深色',
    desc: '霓虹发光 · 科技终端',
    swatch: ['#0e1116', '#ff4356', '#36d1c4'],
    vars: mk({
      bg: '#0e1116', surface: '#161b22', surface2: '#1c232d', border: '#232b36',
      text: '#e6edf3', text2: '#aab4c0', text3: '#8b97a6',
      brand: '#ff4356', softBg: 'rgba(255,67,86,0.12)', softBorder: 'rgba(255,67,86,0.25)', softText: '#e6a3aa', accent: '#36d1c4',
      chipBg: '#161b22', chipBorder: '#232b36', chipText: '#8b97a6',
      shadowCard: '0 16rpx 36rpx -22rpx rgba(0,0,0,0.6)', shadowChip: '0 8rpx 20rpx -10rpx rgba(0,0,0,0.6)',
      bannerBg: '#0b0e12', bannerText: '#e6edf3', bannerBorder: '#1b222b', mask: 'rgba(0,0,0,0.6)',
      ballRed: 'radial-gradient(circle at 33% 28%, #ff8088, #ff4356 55%, #c5102a)',
      ballBlue: 'radial-gradient(circle at 33% 28%, #7fd6ff, #2c9be0 55%, #1768a8)',
      ballMain: 'radial-gradient(circle at 33% 28%, #ffd27f, #ffab2c 55%, #d97600)',
      ballDigits: 'radial-gradient(circle at 33% 28%, #8fe6b0, #36d18a 55%, #1f9460)',
      ballDefault: 'radial-gradient(circle at 33% 28%, #aab4c0, #6b7686 55%, #45505e)',
      glowRed: NEON('255,67,86,0.5'), glowBlue: NEON('60,160,230,0.5'), glowMain: NEON('255,171,44,0.5'),
      glowDigits: NEON('54,209,138,0.5'), glowDefault: NEON('124,134,150,0.45'),
      pickRed: '#ff4356', pickBlue: '#2c9be0',
      heat: ['#232b36', '#3a2f1a', '#6b4e1a', '#c98a2a', '#ff9a3c'], heatText: '#e6edf3', heatMeta: '#aab4c0',
      trendBar: 'rgba(255,67,86,0.22)', trendText: '#ff7984', headerBg: '#11161d', gridLine: '#1b222b', matrixMiss: '#5c6675',
    }),
  },
  {
    key: 'festive',
    name: '喜庆红金',
    desc: '红金贺岁 · 节日氛围',
    swatch: ['#c8102e', '#e0a830', '#fbeede'],
    vars: mk({
      bg: '#fbeede', surface: '#fffaf2', surface2: '#f6e7d3', border: '#efdcc4',
      text: '#3b241a', text2: '#7c5a45', text3: '#b09478',
      brand: '#c21f2c', brandOn: '#ffe9b8', softBg: '#f6e1cc', softBorder: '#efcfa8', softText: '#a8431f', accent: '#b8892a',
      chipBg: '#f6e7d3', chipText: '#7c5a45',
      shadowCard: '0 16rpx 36rpx -22rpx rgba(120,70,20,0.28)', shadowChip: '0 8rpx 20rpx -10rpx rgba(120,70,20,0.22)',
      bannerBg: 'linear-gradient(180deg, #d4162e, #a8121f)', bannerText: '#ffe6b0', bannerBorder: 'transparent', mask: 'rgba(60,20,10,0.5)',
      ballRed: '#c21f2c',
      ballBlue: '#2c6bb0',
      ballMain: '#c99128',
      ballDigits: '#3c8b5a',
      ballDefault: '#b89766',
      glowRed: FLAT('158,15,28,0.28'), glowBlue: FLAT('30,90,160,0.24'), glowMain: FLAT('179,121,26,0.26'),
      glowDigits: FLAT('47,125,51,0.24'), glowDefault: FLAT('140,110,66,0.24'),
      pickRed: '#d51a30', pickBlue: '#2566ab',
      heat: ['#f3ece0', '#f6dca8', '#eac06a', '#d49a2a', '#a8631a'], heatText: '#3b241a', heatMeta: '#7c5a45',
      trendBar: '#f6dca8', trendText: '#c8102e', headerBg: '#fbf2e6', gridLine: '#f0e2d2', matrixMiss: '#c2a98c',
    }),
  },
  {
    key: 'minimal',
    name: '极简灰',
    desc: '黑白灰 · 留白克制',
    swatch: ['#ffffff', '#1a1a1a', '#999999'],
    vars: mk({
      bg: '#f6f6f6', surface: '#ffffff', surface2: '#f1f1f1', border: '#ececec',
      text: '#1a1a1a', text2: '#555555', text3: '#999999',
      brand: '#1a1a1a', softBg: '#f1f1f1', softBorder: '#e4e4e4', softText: '#555555', accent: '#1a1a1a',
      chipBg: '#f1f1f1', chipText: '#666666',
      shadowCard: '0 12rpx 30rpx -20rpx rgba(0,0,0,0.12)', shadowChip: '0 6rpx 16rpx -10rpx rgba(0,0,0,0.10)',
      bannerBg: '#ffffff', bannerText: '#1a1a1a', bannerBorder: '#ececec', mask: 'rgba(0,0,0,0.4)',
      ballRed: '#e1404a',
      ballBlue: '#3a7bc0',
      ballMain: '#f59a1f',
      ballDigits: '#46a04c',
      ballDefault: '#9a9a9a',
      glowRed: FLAT('0,0,0,0.16'), glowBlue: FLAT('0,0,0,0.16'), glowMain: FLAT('0,0,0,0.16'),
      glowDigits: FLAT('0,0,0,0.16'), glowDefault: FLAT('0,0,0,0.16'),
      pickRed: '#e1404a', pickBlue: '#3a7bc0',
      heat: ['#f0f0f0', '#e0e0e0', '#cccccc', '#b0b0b0', '#909090'], heatText: '#1a1a1a', heatMeta: '#555555',
      trendBar: '#e2e2e2', trendText: '#1a1a1a', headerBg: '#fafafa', gridLine: '#ededed', matrixMiss: '#cccccc',
    }),
  },
]

function readStoredKey() {
  try {
    if (typeof uni !== 'undefined') {
      const k = uni.getStorageSync(STORAGE_KEY)
      if (k && THEMES.some((t) => t.key === k)) return k
    }
  } catch (e) { /* 读存储失败兜底 */ }
  return 'light'
}

export const themeState = reactive({ key: readStoredKey() })

export function currentTheme() {
  return THEMES.find((t) => t.key === themeState.key) || THEMES[0]
}

/** 把当前主题变量拼成 inline style 字符串，供页面根 <view> 绑定（各端通用） */
export function themeVarString() {
  const v = currentTheme().vars
  return Object.keys(v).map((k) => `${k}:${v[k]}`).join(';')
}

/** H5 下把变量写到根节点，实现一处切换、全局生效 */
export function applyTheme() {
  const v = currentTheme().vars
  // #ifdef H5
  if (typeof document !== 'undefined' && document.documentElement) {
    Object.keys(v).forEach((k) => document.documentElement.style.setProperty(k, v[k]))
    document.documentElement.setAttribute('data-theme', themeState.key)
  }
  // #endif
  // 原生 tabBar 跟随主题（CSS 变量管不到，需用 API）
  try {
    if (typeof uni !== 'undefined' && uni.setTabBarStyle) {
      uni.setTabBarStyle({
        backgroundColor: v['--surface'],
        color: v['--text-3'],
        selectedColor: v['--brand'],
        borderStyle: themeState.key === 'dark' ? 'white' : 'black',
      })
    }
  } catch (e) { /* 非 tab 页 / 暂不支持时忽略 */ }
}

export function setTheme(key) {
  if (!THEMES.some((t) => t.key === key)) return
  themeState.key = key
  try {
    if (typeof uni !== 'undefined') uni.setStorageSync(STORAGE_KEY, key)
  } catch (e) { /* 写存储失败不影响本次 */ }
  applyTheme()
}

export function initTheme() {
  applyTheme()
}
