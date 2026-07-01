<template>
  <view v-if="visible" class="mask" @click="$emit('close')">
    <view class="sheet" @click.stop>
      <view class="sheet-head">
        <text class="title">界面风格</text>
        <text class="close" @click="$emit('close')">✕</text>
      </view>
      <view
        v-for="t in themes"
        :key="t.key"
        class="opt"
        :class="{ active: t.key === current }"
        @click="pick(t.key)"
      >
        <view class="swatch">
          <view v-for="(c, i) in t.swatch" :key="i" class="dot" :style="{ background: c }" />
        </view>
        <view class="meta">
          <text class="name">{{ t.name }}</text>
          <text class="desc">{{ t.desc }}</text>
        </view>
        <view class="radio" :class="{ on: t.key === current }">
          <view v-if="t.key === current" class="radio-in" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { THEMES, themeState, setTheme } from '../store/theme.js'

defineProps({ visible: { type: Boolean, default: false } })
const emit = defineEmits(['close'])

const themes = THEMES
const current = computed(() => themeState.key)
function pick(key) {
  setTheme(key)
  emit('close')
}
</script>

<style scoped>
.mask {
  position: fixed; left: 0; right: 0; top: 0; bottom: 0; z-index: 200;
  background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: flex-end;
}
.sheet {
  width: 100%; background: var(--surface); border-radius: 32rpx 32rpx 0 0;
  padding: 28rpx 28rpx calc(120rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid var(--border);
}
.sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12rpx; }
.title { font-size: 32rpx; font-weight: 700; color: var(--text); }
.close { font-size: 30rpx; color: var(--text-3); padding: 8rpx 12rpx; }

.opt {
  display: flex; align-items: center; gap: 20rpx;
  padding: 22rpx 8rpx; border-bottom: 1rpx solid var(--border);
}
.opt:last-child { border-bottom: none; }
.swatch { display: flex; flex: none; }
.dot {
  width: 40rpx; height: 40rpx; border-radius: 50%;
  border: 2rpx solid var(--surface); margin-left: -10rpx;
  box-shadow: 0 2rpx 6rpx rgba(0, 0, 0, 0.18);
}
.dot:first-child { margin-left: 0; }
.meta { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.name { font-size: 29rpx; font-weight: 600; color: var(--text); }
.desc { font-size: 23rpx; color: var(--text-3); }
.radio {
  width: 38rpx; height: 38rpx; border-radius: 50%; flex: none;
  border: 2rpx solid var(--border);
  display: flex; align-items: center; justify-content: center;
}
.radio.on { border-color: var(--brand); }
.radio-in { width: 20rpx; height: 20rpx; border-radius: 50%; background: var(--brand); }
</style>
