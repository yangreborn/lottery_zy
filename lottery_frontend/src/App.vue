<script>
import { loadToken, authState } from './store/auth.js'
import { ensureLogin } from './api/user.js'

export default {
  onLaunch: async function () {
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
