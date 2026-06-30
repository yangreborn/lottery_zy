<template>
  <view class="page" :style="themeVars">
    <TopBanner title="我要反馈" :back="true" />
    <view class="form">
      <textarea class="ta" v-model="content" placeholder="请写下你的意见或建议…" maxlength="500" />
      <input class="ipt" v-model="contact" placeholder="联系方式（可选）" />
      <button class="btn" :disabled="!content.trim() || submitting" @click="submit">提交</button>
    </view>
  </view>
</template>

<script setup>
import { computed as __cmp } from 'vue'
import { themeState as __ts, themeVarString as __tvs } from '../../store/theme.js'
const themeVars = __cmp(() => { void __ts.key; return __tvs() })

import { ref } from 'vue'
import TopBanner from '../../components/TopBanner.vue'
import { submitFeedback } from '../../api/user.js'
import { reportAccess } from '../../utils/report.js'

const content = ref('')
const contact = ref('')
const submitting = ref(false)

async function submit() {
  if (!content.value.trim() || submitting.value) return
  submitting.value = true
  try {
    await submitFeedback({ content: content.value.trim(), contact: contact.value.trim() })
    reportAccess('feedback', { action: 'feedback' })
    uni.showToast({ title: '已收到，谢谢反馈', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form { padding: 24rpx; }
.ta { background: var(--surface); border-radius: 12rpx; padding: 20rpx; width: 100%; height: 240rpx; font-size: 28rpx; box-sizing: border-box; }
.ipt { background: var(--surface); border-radius: 12rpx; padding: 20rpx; margin-top: 20rpx; font-size: 28rpx; }
.btn { background: var(--brand); color: var(--surface); font-size: 30rpx; margin-top: 32rpx; }
.page { background: var(--bg); min-height: 100vh; }
</style>
