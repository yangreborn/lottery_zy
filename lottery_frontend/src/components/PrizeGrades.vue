<template>
  <view v-if="hasData" class="grades">
    <view class="grade head-row">
      <text class="c1">奖级</text><text class="c2">注数</text><text class="c3">单注奖金</text>
    </view>
    <template v-if="!data.grouped">
      <view v-for="(g, i) in data.flat" :key="i" class="grade">
        <text class="c1" :class="{ top: i === 0 }">{{ g.label }}</text>
        <text class="c2">{{ g.count }}</text>
        <text class="c3">{{ formatAmount(g.amount) }}</text>
      </view>
    </template>
    <template v-else>
      <view v-for="grp in data.groups" :key="grp.pick" class="kgroup">
        <view class="ghead" @click="toggle(grp.pick)">
          <text>{{ grp.label }}（{{ grp.rows.length }}档）</text>
          <text class="caret">{{ open.includes(grp.pick) ? '▲' : '▼' }}</text>
        </view>
        <template v-if="open.includes(grp.pick)">
          <view v-for="(g, i) in grp.rows" :key="i" class="grade">
            <text class="c1">{{ g.label }}</text>
            <text class="c2">{{ g.count }}</text>
            <text class="c3">{{ formatAmount(g.amount) }}</text>
          </view>
        </template>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { normalizePrizes } from '../utils/prize.js'
import { formatAmount } from '../utils/format.js'

const props = defineProps({
  grades: { type: Array, default: () => [] },
})
const data = computed(() => normalizePrizes(props.grades))
// 无有效奖级数据时整块不渲染（如福彩3D：官方接口未回填中奖注数/奖金）
const hasData = computed(() =>
  data.value.grouped
    ? data.value.groups.some((g) => g.rows.length)
    : data.value.flat.length > 0
)
const open = ref([])
function toggle(pick) {
  open.value = open.value.includes(pick)
    ? open.value.filter((p) => p !== pick)
    : [...open.value, pick]
}
</script>

<style scoped>
.grades { border-top: 1rpx solid var(--border); padding-top: 16rpx; margin-top: 4rpx; }
.grade {
  display: flex; align-items: center; padding: 14rpx 0;
  font-size: 28rpx; color: var(--text-2);
  border-bottom: 1rpx solid var(--border);
}
.c1 { flex: 2; font-weight: 600; }
.c1.top { color: var(--brand); }
.c2 { flex: 1; text-align: center; font-variant-numeric: tabular-nums; color: var(--text); }
.c3 {
  flex: 2; text-align: right; font-weight: 700; color: var(--text);
  font-variant-numeric: tabular-nums;
}
.head-row { border-bottom: 1rpx solid var(--border); }
.head-row .c1, .head-row .c2, .head-row .c3 { color: var(--text-3); font-weight: 600; font-size: 24rpx; }
.ghead {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18rpx 0; font-size: 28rpx; color: var(--text); font-weight: 700;
}
.caret { font-size: 22rpx; color: var(--text-3); }
</style>
