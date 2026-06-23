<template>
  <view class="page" v-if="rule">
    <view class="zone">
      <text class="zt">红球（选 {{ rule.red.count }}）</text>
      <view class="grid">
        <BallSelectable
          v-for="n in redRange" :key="'r'+n" :value="n" zone="red"
          :selected="sel.red.includes(n)" @toggle="toggle('red', $event)"
        />
      </view>
    </view>
    <view class="zone">
      <text class="zt">蓝球（选 {{ rule.blue.count }}）</text>
      <view class="grid">
        <BallSelectable
          v-for="n in blueRange" :key="'b'+n" :value="n" zone="blue"
          :selected="sel.blue.includes(n)" @toggle="toggle('blue', $event)"
        />
      </view>
    </view>
    <view class="fields">
      <input class="ipt" v-model="note" placeholder="备注（可空）" />
      <input class="ipt" v-model="targetIssue" placeholder="目标期号（可空，用于比对）" />
    </view>
    <view class="actions">
      <button class="btn" @click="saveManual" :disabled="!canSaveManual">保存手选</button>
      <button class="btn alt" @click="saveRandom">机选保存</button>
      <button class="btn alt" @click="saveDan">定胆随机</button>
    </view>
  </view>
  <view v-else class="empty">{{ emptyMsg }}</view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, createNumber } from '../../api/user.js'
import { toggleBall, selectionComplete } from '../../utils/picker.js'
import { reportAccess } from '../../utils/report.js'

const rule = ref(null)
const emptyMsg = ref('加载中…')
const sel = reactive({ red: [], blue: [] })
const note = ref('')
const targetIssue = ref('')

const code = lotteryStore.code

function range(r) {
  const arr = []
  for (let i = r.min; i <= r.max; i++) arr.push(i)
  return arr
}
const redRange = computed(() => (rule.value ? range(rule.value.red) : []))
const blueRange = computed(() => (rule.value ? range(rule.value.blue) : []))
const canSaveManual = computed(() => rule.value && selectionComplete(sel, rule.value))

function toggle(zone, n) {
  sel[zone] = toggleBall(sel[zone], n, rule.value[zone].count)
}

async function save(payload) {
  try {
    await ensureLogin()
    await createNumber({ code, note: note.value, target_issue: targetIssue.value, ...payload })
    uni.showToast({ title: '已保存', icon: 'success' })
    reportAccess('mine/create', { lottery_code: code, action: 'save_number' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
}

function saveManual() {
  if (!canSaveManual.value) return
  save({ gen_type: 'manual', numbers: { red: sel.red, blue: sel.blue } })
}
function saveRandom() {
  save({ gen_type: 'random' })
}
function saveDan() {
  save({ gen_type: 'dan_random', dan_numbers: { red: sel.red, blue: sel.blue } })
}

onLoad(async () => {
  try {
    const list = await getLotteryList()
    const found = list.find((l) => l.code === code)
    if (found) rule.value = found.rule_config
    else emptyMsg.value = '彩种不存在'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
})
</script>

<style scoped>
.zone { background: #fff; margin: 16rpx 20rpx; padding: 20rpx; border-radius: 12rpx; }
.zt { font-size: 26rpx; color: #666; }
.grid { display: flex; flex-wrap: wrap; margin-top: 12rpx; }
.fields { margin: 0 20rpx; }
.ipt { background: #fff; border-radius: 10rpx; padding: 18rpx; margin-top: 16rpx; font-size: 26rpx; }
.actions { display: flex; flex-wrap: wrap; padding: 24rpx 20rpx; }
.btn { flex: 1; margin: 8rpx; background: #e53935; color: #fff; font-size: 26rpx; }
.btn.alt { background: #1e88e5; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
