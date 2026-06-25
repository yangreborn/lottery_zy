export const SHORT_NAMES = { dlt: '大乐透' }
export const HOT_CODES = ['ssq', 'dlt', '3d', 'pl3', 'kl8']

export function shortLotteryName(item) {
  return (item && (SHORT_NAMES[item.code] || item.name)) || ''
}

export function splitTabs(list, hotCodes = HOT_CODES) {
  const arr = list || []
  return {
    visible: arr.filter((x) => hotCodes.includes(x.code)),
    overflow: arr.filter((x) => !hotCodes.includes(x.code)),
  }
}
