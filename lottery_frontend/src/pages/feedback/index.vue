<template>
  <view class="page">
    <TopBanner title="我要反馈" :back="true" />
    <view class="form">
      <textarea class="ta" v-model="content" placeholder="请写下你的意见或建议…" maxlength="500" />
      <input class="ipt" v-model="contact" placeholder="联系方式（可选）" />
      <button class="btn" :disabled="!content.trim() || submitting" @click="submit">提交</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import TopBanner from '../../components/TopBanner.vue'
import { submitFeedback } from '../../api/user.js'

const content = ref('')
const contact = ref('')
const submitting = ref(false)

async function submit() {
  if (!content.value.trim() || submitting.value) return
  submitting.value = true
  try {
    await submitFeedback({ content: content.value.trim(), contact: contact.value.trim() })
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
.ta { background: #fff; border-radius: 12rpx; padding: 20rpx; width: 100%; height: 240rpx; font-size: 28rpx; box-sizing: border-box; }
.ipt { background: #fff; border-radius: 12rpx; padding: 20rpx; margin-top: 20rpx; font-size: 28rpx; }
.btn { background: #e53935; color: #fff; font-size: 30rpx; margin-top: 32rpx; }
</style>
