export const HOME_MENU = [
  { key: 'latest', title: '当期中奖', icon: '🎯', path: '/pages/draw/latest', nav: 'navigateTo' },
  { key: 'history', title: '往期开奖', icon: '📅', path: '/pages/draw/history', nav: 'navigateTo' },
  { key: 'stats', title: '号码统计', icon: '📊', path: '/pages/draw/stats', nav: 'switchTab' },
  { key: 'picker', title: '选号', icon: '✏️', path: '/pages/mine/picker', nav: 'switchTab' },
  { key: 'guide', title: '玩法说明', icon: '📖', path: '/pages/guide/index', nav: 'navigateTo' },
  { key: 'notice', title: '通知', icon: '📢', path: '/pages/notice/index', nav: 'navigateTo' },
  { key: 'poster', title: '开奖海报', icon: '🖼️', path: '/pages/poster/index', nav: 'navigateTo' },
  { key: 'chart', title: '走势图', icon: '📈', path: '/pages/chart/index', nav: 'navigateTo' },
]

export function goMenu(item) {
  if (item.nav === 'switchTab') {
    uni.switchTab({ url: item.path })
  } else {
    uni.navigateTo({ url: item.path })
  }
}
