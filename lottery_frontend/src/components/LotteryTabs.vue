<template>
  <view class="tabs">
    <view
      v-for="item in list"
      :key="item.code"
      class="tab"
      :class="{ active: item.code === active }"
      @click="$emit('change', item.code)"
    >
      <text>{{ item.name }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  list: { type: Array, default: () => [] },
  active: { type: String, default: '' },
})
defineEmits(['change'])
</script>

<style scoped>
.tabs { display: flex; border-bottom: 1px solid #eee; }
.tab { flex: 1; text-align: center; padding: 20rpx 0; color: #666; }
.tab.active { color: #e53935; border-bottom: 4rpx solid #e53935; font-weight: 600; }
</style>
