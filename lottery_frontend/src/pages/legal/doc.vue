<template>
  <view class="page">
    <TopBanner :title="doc.title" :back="true" />
    <view class="body">
      <view v-for="(p, i) in doc.paragraphs" :key="i" class="para">{{ p }}</view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { getLegalDoc } from '../../utils/legal.js'

const doc = ref(getLegalDoc('agreement'))
onLoad((q) => { doc.value = getLegalDoc(q && q.type) })
</script>

<style scoped>
.body { padding: 24rpx; }
.para { font-size: 28rpx; color: #555; line-height: 1.8; margin-bottom: 18rpx; }
</style>
