export const SHORT_NAMES = { dlt: '大乐透' }
// 全局规范彩种顺序：双色球、大乐透、福彩3D、快乐8、排列3
export const LOTTERY_ORDER = ['ssq', 'dlt', '3d', 'kl8', 'pl3']
export const HOT_CODES = ['ssq', 'dlt', '3d', 'kl8', 'pl3']

export function shortLotteryName(item) {
  return (item && (SHORT_NAMES[item.code] || item.name)) || ''
}

// 按 LOTTERY_ORDER 排序；不在表内的 code 依原相对序排末尾（稳定排序）
export function sortLotteries(list) {
  const rank = (code) => {
    const i = LOTTERY_ORDER.indexOf(code)
    return i === -1 ? LOTTERY_ORDER.length : i
  }
  return [...(list || [])].sort((a, b) => rank(a.code) - rank(b.code))
}

export function splitTabs(list, hotCodes = HOT_CODES) {
  const arr = list || []
  return {
    visible: arr.filter((x) => hotCodes.includes(x.code)),
    overflow: arr.filter((x) => !hotCodes.includes(x.code)),
  }
}
