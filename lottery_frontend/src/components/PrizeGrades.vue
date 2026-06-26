<template>
  <view v-if="hasData" class="grades">
    <view class="grade head-row">
      <text class="c1">奖级</text><text class="c2">注数</text><text class="c3">单注奖金</text>
    </view>
    <template v-if="!data.grouped">
      <view v-for="(g, i) in data.flat" :key="i" class="grade">
        <text class="c1">{{ g.label }}</text>
        <text class="c2">{{ g.count }}</text>
        <text class="c3">{{ formatAmount(g.amount) }}</text>
      </view>
    </template>
    <template v-else>
      <view v-for="grp in data.groups" :key="grp.pick" class="kgroup">
        <view class="ghead" @click="toggle(grp.pick)">
          <text>{{ grp.label }}（{{ grp.rows.length }}档）</text>
          <text>{{ open.includes(grp.pick) ? '▲' : '▼' }}</text>
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
.grades { border-top: 1px solid #f0f0f0; padding-top: 16rpx; }
.grade { display: flex; padding: 10rpx 0; font-size: 30rpx; color: #555; }
.c1 { flex: 2; }
.c2 { flex: 1; text-align: center; }
.c3 { flex: 2; text-align: right; }
.head-row { color: #999; font-weight: 600; }
.kgroup { border-bottom: 1px solid #f5f5f5; }
.ghead { display: flex; justify-content: space-between; padding: 16rpx 0; font-size: 30rpx; color: #555; font-weight: 600; }
</style>
