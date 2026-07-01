// 菜单图标用语义 key（见 utils/icons.js 的 PATHS），
// 由页面按当前主题着色，实现深/浅色切换时图标描边色自动跟随。
// 走势图、选号已在底边栏，不再放首页；统计非 tab 页，走 navigateTo
export const HOME_MENU = [
  { key: 'history', title: '往期开奖', icon: 'calendar', path: '/pages/draw/history', nav: 'navigateTo' },
  { key: 'stats', title: '号码统计', icon: 'bars', path: '/pages/draw/stats', nav: 'navigateTo' },
  { key: 'notice', title: '通知', icon: 'bell', path: '/pages/notice/index', nav: 'navigateTo' },
  { key: 'poster', title: '开奖海报', icon: 'image', path: '/pages/poster/index', nav: 'navigateTo' },
]

export function goMenu(item) {
  if (item.nav === 'switchTab') {
    uni.switchTab({ url: item.path })
  } else {
    uni.navigateTo({ url: item.path })
  }
}
