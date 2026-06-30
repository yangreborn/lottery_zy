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
/* 胶囊式彩种切换：选中态填充品牌色 */
.tabs {
  display: flex; align-items: center; gap: 12rpx;
  background: var(--surface); padding: 18rpx 24rpx;
  border-bottom: 1rpx solid var(--border); position: relative;
}
.tab {
  flex: none; padding: 12rpx 26rpx; border-radius: 999rpx;
  background: var(--chip-bg); border: 1rpx solid var(--chip-border);
  color: var(--chip-text); font-size: 27rpx;
}
.tab.active {
  background: var(--brand); color: var(--brand-on); font-weight: 700;
  border-color: var(--brand);
}
.more { flex: none; }
.dropdown {
  position: absolute; right: 24rpx; top: 100%; z-index: 20;
  background: var(--surface); box-shadow: var(--shadow-card);
  border: 1rpx solid var(--border); border-radius: 18rpx; overflow: hidden;
  min-width: 200rpx; margin-top: 8rpx;
}
.ditem { padding: 22rpx 28rpx; color: var(--text-2); font-size: 27rpx; }
.ditem.active { color: var(--brand); font-weight: 700; background: var(--brand-soft-bg); }
</style>
