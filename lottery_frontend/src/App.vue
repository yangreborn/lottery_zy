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
</style>
