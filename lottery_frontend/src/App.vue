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
  --bg: #f3efe6;
  --surface: #fcfbf7;
  --surface-2: #efeae0;
  --border: #e5dfd1;
  --text: #1c1a15;
  --text-2: #57524a;
  --text-3: #9a9388;
  --brand: #ce3f26;
  --brand-on: #ffffff;
  --brand-soft-bg: #f7e3db;
  --brand-soft-border: #f0d3c6;
  --brand-soft-text: #a8391f;
  --accent: #2c5f8a;
  --chip-bg: #efeae0;
  --chip-border: transparent;
  --chip-text: #57524a;
  --shadow-card: 0 16rpx 36rpx -22rpx rgba(60, 40, 20, 0.30);
  --shadow-chip: 0 8rpx 20rpx -10rpx rgba(60, 40, 20, 0.22);
  --ball-red: #ce3f26;
  --ball-blue: #2c6bb0;
  --ball-main: #c4892c;
  --ball-digits: #3c8b5a;
  --ball-default: #9a9388;
  --ball-glow-red: 0 4rpx 10rpx -4rpx rgba(120, 50, 30, 0.24);
  --ball-glow-blue: 0 4rpx 10rpx -4rpx rgba(30, 70, 120, 0.22);
  --ball-glow-main: 0 4rpx 10rpx -4rpx rgba(120, 80, 20, 0.22);
  --ball-glow-digits: 0 4rpx 10rpx -4rpx rgba(40, 90, 60, 0.22);
  --ball-glow-default: 0 4rpx 10rpx -4rpx rgba(90, 80, 70, 0.20);
  --pick-red: #ce3f26;
  --pick-blue: #2c6bb0;
  --banner-bg: #fcfbf7;
  --banner-text: #1c1a15;
  --banner-border: #e5dfd1;
  --mask: rgba(0, 0, 0, 0.45);
  --heat-0: #efeae0;
  --heat-1: #f4dbc0;
  --heat-2: #ecb37b;
  --heat-3: #de8a45;
  --heat-4: #ce3f26;
  --heat-text: #1c1a15;
  --heat-meta: #57524a;
  --trend-bar: #f7e3db;
  --trend-bar-text: #ce3f26;
  --trend-header-bg: #f6f1e8;
  --grid-line: #eae4d6;
  --matrix-miss: #b8b0a4;
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
