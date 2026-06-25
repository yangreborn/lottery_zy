<template>
  <view class="tabs">
    <view
      v-for="item in visible"
      :key="item.code"
      class="tab"
      :class="{ active: item.code === active }"
      @click="$emit('change', item.code)"
    >
      <text>{{ shortLotteryName(item) }}</text>
    </view>
    <view
      v-if="overflow.length"
      class="tab more"
      :class="{ active: activeInOverflow }"
      @click="open = !open"
    >
      <text>更多 ▾</text>
    </view>
    <view v-if="open && overflow.length" class="dropdown">
      <view
        v-for="item in overflow"
        :key="item.code"
        class="ditem"
        :class="{ active: item.code === active }"
        @click="pick(item.code)"
      >
        <text>{{ shortLotteryName(item) }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { shortLotteryName, splitTabs } from '../utils/lottery.js'

const props = defineProps({
  list: { type: Array, default: () => [] },
  active: { type: String, default: '' },
})
const emit = defineEmits(['change'])

const open = ref(false)
const parts = computed(() => splitTabs(props.list))
const visible = computed(() => parts.value.visible)
const overflow = computed(() => parts.value.overflow)
const activeInOverflow = computed(() => overflow.value.some((x) => x.code === props.active))

function pick(code) {
  open.value = false
  emit('change', code)
}
</script>

<style scoped>
.tabs { display: flex; border-bottom: 1px solid #eee; position: relative; }
.tab { flex: 1; text-align: center; padding: 20rpx 0; color: #666; }
.tab.active { color: #e53935; border-bottom: 4rpx solid #e53935; font-weight: 600; }
.more { flex: 0 0 120rpx; }
.dropdown { position: absolute; right: 0; top: 100%; z-index: 20; background: #fff; box-shadow: 0 6rpx 20rpx rgba(0,0,0,0.12); border-radius: 0 0 12rpx 12rpx; min-width: 180rpx; }
.ditem { padding: 20rpx 28rpx; color: #666; }
.ditem.active { color: #e53935; font-weight: 600; }
</style>
