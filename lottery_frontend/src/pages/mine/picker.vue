<template>
  <view class="page">
    <TopBanner title="选号" />
    <template v-if="rule">
      <view class="modes">
        <view class="mode" :class="{ active: mode === 'jixuan' }" @click="mode = 'jixuan'"><text>机选</text></view>
        <view class="mode" :class="{ active: mode === 'manual' }" @click="mode = 'manual'"><text>手动</text></view>
      </view>

      <view v-if="mode === 'jixuan'">
        <view class="gen-bar">
          <button class="btn" size="mini" @click="doGenerate(5)">机选5注</button>
          <button class="btn" size="mini" @click="doGenerate(10)">机选10注</button>
          <button class="btn alt" size="mini" :disabled="!sets.length" @click="reroll">换一批</button>
        </view>
        <view
          v-for="(s, i) in sets" :key="i"
          class="setrow" :class="{ sel: selected.includes(i) }" @click="toggleSel(i)"
        >
          <text class="chk">{{ selected.includes(i) ? '✓' : '○' }}</text>
          <view class="balls">
            <Ball v-for="(n, ri) in s.red" :key="'r'+ri" :value="n" zone="red" />
            <Ball v-for="(n, bi) in s.blue" :key="'b'+bi" :value="n" zone="blue" />
          </view>
        </view>
        <view v-if="!sets.length" class="hint">点上面"机选5注/10注"先生成，再勾选要保存的。</view>
      </view>

      <view v-else>
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
      </view>

      <view class="fields">
        <input class="ipt" v-model="note" placeholder="备注（可空）" />
        <input class="ipt" v-model="targetIssue" placeholder="目标期号（可空，用于比对）" />
      </view>
      <view class="actions">
        <button v-if="mode === 'jixuan'" class="btn save" :disabled="!selected.length" @click="saveBatch">
          保存选中({{ selected.length }})
        </button>
        <button v-else class="btn save" :disabled="!canSaveManual" @click="saveManual">保存手选</button>
      </view>
    </template>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import Ball from '../../components/Ball.vue'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, createNumber, generateNumbers } from '../../api/user.js'
import { toggleBall, selectionComplete, toggleIndex } from '../../utils/picker.js'
import { reportAccess } from '../../utils/report.js'

const rule = ref(null)
const emptyMsg = ref('加载中…')
const mode = ref('jixuan')
const code = lotteryStore.code

const sel = reactive({ red: [], blue: [] })
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

const sets = ref([])
const selected = ref([])
const lastCount = ref(5)

async function doGenerate(n) {
  lastCount.value = n
  try {
    await ensureLogin()
    const res = await generateNumbers(code, n)
    sets.value = res.sets || []
    selected.value = sets.value.map((_, i) => i)
  } catch (e) {
    uni.showToast({ title: e.msg || '生成失败', icon: 'none' })
  }
}
function reroll() { doGenerate(lastCount.value) }
function toggleSel(i) { selected.value = toggleIndex(selected.value, i) }

const note = ref('')
const targetIssue = ref('')

async function saveOne(numbers, genType) {
  await ensureLogin()
  return createNumber({ code, gen_type: genType, numbers, note: note.value, target_issue: targetIssue.value })
}

async function saveManual() {
  if (!canSaveManual.value) return
  try {
    await saveOne({ red: sel.red, blue: sel.blue }, 'manual')
    uni.showToast({ title: '已保存', icon: 'success' })
    reportAccess('mine/create', { lottery_code: code, action: 'save_number' })
    setTimeout(() => uni.switchTab({ url: '/pages/mine/index' }), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
}

async function saveBatch() {
  if (!selected.value.length) {
    uni.showToast({ title: '请先勾选', icon: 'none' })
    return
  }
  let ok = 0
  let fail = 0
  for (const i of selected.value) {
    try { await saveOne(sets.value[i], 'random'); ok += 1 } catch (e) { fail += 1 }
  }
  uni.showToast({ title: fail ? `成功${ok}注 失败${fail}注` : `已保存${ok}注`, icon: fail ? 'none' : 'success' })
  if (ok > 0) reportAccess('mine/create', { lottery_code: code, action: 'save_number' })
  if (ok && !fail) setTimeout(() => uni.switchTab({ url: '/pages/mine/index' }), 700)
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
.modes { display: flex; margin: 16rpx 20rpx; background: #fff; border-radius: 12rpx; overflow: hidden; }
.mode { flex: 1; text-align: center; padding: 20rpx 0; color: #666; font-size: 30rpx; }
.mode.active { background: #e53935; color: #fff; font-weight: 600; }
.gen-bar { display: flex; flex-wrap: wrap; padding: 12rpx 20rpx; }
.setrow { display: flex; align-items: center; background: #fff; margin: 12rpx 20rpx; padding: 18rpx; border-radius: 12rpx; border: 2rpx solid transparent; }
.setrow.sel { border-color: #e53935; }
.chk { font-size: 34rpx; color: #e53935; width: 48rpx; }
.balls { display: flex; flex-wrap: wrap; flex: 1; }
.hint { text-align: center; color: #999; padding: 40rpx 20rpx; font-size: 26rpx; }
.zone { background: #fff; margin: 16rpx 20rpx; padding: 20rpx; border-radius: 12rpx; }
.zt { font-size: 30rpx; color: #666; }
.grid { display: flex; flex-wrap: wrap; margin-top: 12rpx; }
.fields { margin: 0 20rpx; }
.ipt { background: #fff; border-radius: 10rpx; padding: 18rpx; margin-top: 16rpx; font-size: 28rpx; }
.actions { padding: 24rpx 20rpx; }
.btn { background: #e53935; color: #fff; font-size: 30rpx; margin: 8rpx; }
.btn.alt { background: #1e88e5; }
.btn.save { width: 100%; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
