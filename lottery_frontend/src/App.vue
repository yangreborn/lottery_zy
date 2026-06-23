<script>
import { loadToken } from './store/auth.js'

export default {
  onLaunch: function () {
    loadToken()
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
