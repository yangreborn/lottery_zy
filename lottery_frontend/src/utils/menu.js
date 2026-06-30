// 菜单图标用语义 key（见 utils/icons.js 的 PATHS），
// 由页面按当前主题着色，实现深/浅色切换时图标描边色自动跟随。
export const HOME_MENU = [
  { key: 'history', title: '往期开奖', icon: 'calendar', path: '/pages/draw/history', nav: 'navigateTo' },
  { key: 'stats', title: '号码统计', icon: 'bars', path: '/pages/draw/stats', nav: 'switchTab' },
  { key: 'picker', title: '选号', icon: 'pencil', path: '/pages/mine/picker', nav: 'switchTab' },
  { key: 'guide', title: '玩法说明', icon: 'book', path: '/pages/guide/index', nav: 'navigateTo' },
  { key: 'notice', title: '通知', icon: 'bell', path: '/pages/notice/index', nav: 'navigateTo' },
  { key: 'poster', title: '开奖海报', icon: 'image', path: '/pages/poster/index', nav: 'navigateTo' },
  { key: 'chart', title: '走势图', icon: 'trending', path: '/pages/chart/index', nav: 'navigateTo' },
]

export function goMenu(item) {
  if (item.nav === 'switchTab') {
    uni.switchTab({ url: item.path })
  } else {
    uni.navigateTo({ url: item.path })
  }
}
