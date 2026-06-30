<script>
import { loadToken, authState } from './store/auth.js'
import { ensureLogin } from './api/user.js'
import { initTheme } from './store/theme.js'

export default {
  onLaunch: async function () {
    initTheme()
    loadToken()
    if (!authState.token) {
      try { await ensureLogin() } catch (e) { /* 匿名登录失败不阻塞启动 */ }
    }
  },
  onShow: function () {
  },
  onHide: function () {
  },
}
</script>

<style>
/*每个页面公共css */

/* 主题令牌默认值（暖白）。运行时由 store/theme.js 覆盖；
   也作为 H5 首屏渲染、以及未显式绑定主题变量的页面的兜底。 */
page {
  --bg: #f4f1ed;
  --surface: #ffffff;
  --surface-2: #f4f1ed;
  --border: #efe9e3;
  --text: #211c1a;
  --text-2: #4a423d;
  --text-3: #9a928c;
  --brand: #c8102e;
  --brand-on: #ffffff;
  --brand-soft-bg: #fbe9ec;
  --brand-soft-border: #f6d4da;
  --brand-soft-text: #9a3340;
  --accent: #c8102e;
  --chip-bg: #f4f1ed;
  --chip-border: transparent;
  --chip-text: #6b6460;
  --shadow-card: 0 16rpx 36rpx -22rpx rgba(60, 40, 30, 0.28);
  --shadow-chip: 0 8rpx 20rpx -10rpx rgba(60, 40, 30, 0.22);
  --ball-red: radial-gradient(circle at 33% 28%, #f2666b, #d92b32 58%, #b3151c);
  --ball-blue: radial-gradient(circle at 33% 28%, #62a0db, #2566ab 58%, #184c84);
  --ball-main: radial-gradient(circle at 33% 28%, #ffb259, #fb8c00 58%, #d97600);
  --ball-digits: radial-gradient(circle at 33% 28%, #7bc47f, #43a047 58%, #2f7d33);
  --ball-default: radial-gradient(circle at 33% 28%, #c2bbb5, #9a928c 58%, #7c746e);
  --ball-glow-red: 0 6rpx 12rpx rgba(196, 30, 40, 0.34);
  --ball-glow-blue: 0 6rpx 12rpx rgba(30, 90, 160, 0.32);
  --ball-glow-main: 0 6rpx 12rpx rgba(217, 118, 0, 0.32);
  --ball-glow-digits: 0 6rpx 12rpx rgba(47, 125, 51, 0.32);
  --ball-glow-default: 0 6rpx 12rpx rgba(124, 116, 110, 0.30);
  --pick-red: #d92b32;
  --pick-blue: #2566ab;
  --banner-bg: #ffffff;
  --banner-text: #211c1a;
  --banner-border: #efe9e3;
  --mask: rgba(0, 0, 0, 0.45);
  --heat-0: #eeeeee;
  --heat-1: #ffe0b2;
  --heat-2: #ffb74d;
  --heat-3: #fb8c00;
  --heat-4: #e65100;
  --heat-text: #3a322e;
  --heat-meta: #6b6460;
  --trend-bar: #ffd9d4;
  --trend-bar-text: #c8102e;
  --trend-header-bg: #faf7f3;
  --grid-line: #f0ece6;
  --matrix-miss: #cfc7bf;
}

/* #ifdef H5 */
/* PC 网页底部 tabBar 默认字号偏小，放大到清晰可读 */
.uni-tabbar__label {
  font-size: 15px !important;
  line-height: 1.4 !important;
}
.uni-tabbar__item {
  padding: 4px 0 !important;
}
/* #endif */
</style>
