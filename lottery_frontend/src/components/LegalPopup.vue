<template>
  <view v-if="visible" class="mask" @click="$emit('close')">
    <view class="dialog" @click.stop>
      <view class="title">{{ doc.title }}</view>
      <scroll-view scroll-y class="content">
        <view v-for="(p, i) in doc.paragraphs" :key="i" class="para">{{ p }}</view>
      </scroll-view>
      <view class="btn" @click="$emit('close')">我知道了</view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { getLegalDoc } from '../utils/legal.js'

const props = defineProps({
  visible: { type: Boolean, default: false },
  type: { type: String, default: 'agreement' },
})
defineEmits(['close'])
const doc = computed(() => getLegalDoc(props.type))
</script>

<style scoped>
.mask { position: fixed; left: 0; right: 0; top: 0; bottom: 0; background: var(--mask); display: flex; align-items: center; justify-content: center; z-index: 100; }
.dialog { width: 80%; background: var(--surface); border-radius: 24rpx; overflow: hidden; border: 1rpx solid var(--border); }
.title { text-align: center; font-size: 34rpx; font-weight: 700; color: var(--text); padding: 28rpx 0 16rpx; }
.content { max-height: 56vh; padding: 0 28rpx; }
.para { font-size: 26rpx; color: var(--text-2); line-height: 1.8; margin-bottom: 16rpx; }
.btn { text-align: center; color: var(--brand); font-size: 32rpx; font-weight: 600; padding: 24rpx 0; border-top: 1rpx solid var(--border); }
</style>
