<template>
  <view class="page" :style="themeVars" :class="{ 'has-batch': manageMode }">
    <TopBanner title="我的号码" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar">
      <button v-if="items.length" class="manage" size="mini" @click="toggleManage">{{ manageMode ? '完成' : '管理' }}</button>
      <button class="go" size="mini" @click="goPicker">去选号</button>
    </view>
    <view v-for="grp in groups" :key="grp.name" class="group">
      <view class="group-title">{{ grp.name }}（{{ grp.records.length }}）</view>
      <view
        v-for="rec in grp.records" :key="rec.id"
        class="card" :class="{ sel: manageMode && selectedIds.includes(rec.id) }"
        @click="manageMode && toggleSel(rec.id)"
      >
        <view class="top">
          <view class="top-left">
            <text v-if="manageMode" class="chk">{{ selectedIds.includes(rec.id) ? '✓' : '○' }}</text>
            <text class="tag">{{ genLabel(rec.gen_type) }}</text>
          </view>
          <text v-if="rec.target_issue" class="issue">目标 {{ rec.target_issue }}</text>
        </view>
        <view class="balls">
          <template v-for="(nums, key) in rec.numbers">
            <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
          </template>
        </view>
        <view v-if="rec.note" class="note">{{ rec.note }}</view>
        <view class="time">{{ formatTime(rec.created_at) }}</view>
        <view v-if="!manageMode" class="ops">
          <picker mode="selector" :range="issueLabels" :disabled="!issues.length" @change="onPickPurchase(rec, $event)">
            <text class="op">标为已购</text>
          </picker>
          <text class="op" @click="doGroup(rec)">归组</text>
          <text v-if="rec.target_issue" class="op" @click="doCheck(rec.id)">比对</text>
          <text class="op del" @click="doDelete(rec.id)">删除</text>
        </view>
      </view>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
    <view v-if="manageMode" class="batchbar">
      <text class="bb" @click="selectAll">{{ allSelected ? '取消全选' : '全选' }}</text>
      <text class="bb" :class="{ disabled: !selectedIds.length }" @click="doBatchGroup">归组({{ selectedIds.length }})</text>
      <text class="bb del" :class="{ disabled: !selectedIds.length }" @click="doBatchDelete">删除({{ selectedIds.length }})</text>
    </view>
  </view>
</template>

<script setup>
import { computed as __cmp } from 'vue'
import { themeState as __ts, themeVarString as __tvs } from '../../store/theme.js'
const themeVars = __cmp(() => { void __ts.key; return __tvs() })

import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList, getHistory } from '../../api/lottery.js'
import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup, batchDelete, batchGroup, purchaseCreate } from '../../api/user.js'
import { reportAccess } from '../../utils/report.js'
import { formatTime, groupRecords, todayStr, issueLabel } from '../../utils/records.js'
import { toggleIndex } from '../../utils/picker.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const issues = ref([])
const issueLabels = computed(() => issues.value.map(issueLabel))
const emptyMsg = ref('加载中…')

const manageMode = ref(false)
const selectedIds = ref([])

const groups = computed(() => groupRecords(items.value))
const allIds = computed(() => items.value.map((r) => r.id))
const allSelected = computed(() => allIds.value.length > 0 && selectedIds.value.length === allIds.value.length)

const GEN = { manual: '手动', random: '机选', dan_random: '定胆' }
function genLabel(g) { return GEN[g] || g }

async function load() {
  emptyMsg.value = '加载中…'
  try {
    await ensureLogin()
    items.value = await listNumbers(store.code)
    if (!items.value.length) emptyMsg.value = '还没有记录，去选号吧'
    loadIssues()
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
    uni.showToast({ title: e.msg || '加载失败', icon: 'none' })
  }
}

function onChange(code) { exitManage(); setCode(code); load() }
function goPicker() { uni.switchTab({ url: '/pages/mine/picker' }) }

function toggleManage() {
  manageMode.value = !manageMode.value
  selectedIds.value = []
}
function exitManage() { manageMode.value = false; selectedIds.value = [] }
function toggleSel(id) { selectedIds.value = toggleIndex(selectedIds.value, id) }
function selectAll() { selectedIds.value = allSelected.value ? [] : [...allIds.value] }

function doBatchDelete() {
  if (!selectedIds.value.length) return
  const ids = [...selectedIds.value]
  uni.showModal({
    title: '确认删除',
    content: `删除选中的 ${ids.length} 条？删除后不可恢复`,
    success: async (res) => {
      if (!res.confirm) return
      try { await batchDelete(ids); exitManage(); load() }
      catch (e) { uni.showToast({ title: e.msg || '删除失败', icon: 'none' }) }
    },
  })
}

function doBatchGroup() {
  if (!selectedIds.value.length) return
  const ids = [...selectedIds.value]
  uni.showModal({
    title: '批量归组',
    editable: true,
    placeholderText: '输入组名(留空取消分组)',
    success: async (res) => {
      if (!res.confirm) return
      try { await batchGroup(ids, (res.content || '').trim()); exitManage(); load() }
      catch (e) { uni.showToast({ title: e.msg || '归组失败', icon: 'none' }) }
    },
  })
}

async function loadIssues() {
  try { const res = await getHistory(store.code, { page: 1 }); issues.value = res.results || [] }
  catch (e) { issues.value = [] }
}

async function onPickPurchase(rec, e) {
  const sel = issues.value[Number(e.detail.value)]
  if (!sel) { uni.showToast({ title: '暂无可选期次', icon: 'none' }); return }
  try {
    await purchaseCreate({ code: store.code, issue: sel.issue, numbers: rec.numbers, bet_count: 1, purchase_date: todayStr() })
    reportAccess('mine/purchase', { action: 'mark_purchased', lottery_code: store.code })
    uni.showToast({ title: '已记录购买', icon: 'success' })
  } catch (err) {
    uni.showToast({ title: err.msg || '记录失败', icon: 'none' })
  }
}

function doGroup(rec) {
  uni.showModal({
    title: '归组',
    editable: true,
    placeholderText: '输入组名(留空取消分组)',
    content: rec.group_name || '',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await setGroup(rec.id, (res.content || '').trim())
        load()
      } catch (e) {
        uni.showToast({ title: e.msg || '归组失败', icon: 'none' })
      }
    },
  })
}

async function doCheck(id) {
  try {
    const r = await checkNumber(id)
    reportAccess('mine/check', { lottery_code: store.code, action: 'check_number' })
    uni.showModal({
      title: '比对结果',
      content: `${r.desc}，${r.label}`,
      showCancel: false,
    })
  } catch (e) {
    uni.showToast({ title: e.msg || '比对失败', icon: 'none' })
  }
}

function doDelete(id) {
  uni.showModal({
    title: '确认删除',
    content: '删除后不可恢复，确定删除这条号码？',
    success: async (res) => {
      if (!res.confirm) return
      try {
        await deleteNumber(id)
        load()
      } catch (e) {
        uni.showToast({ title: e.msg || '删除失败', icon: 'none' })
      }
    },
  })
}

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞列表 */ }
  }
  load()
})
</script>

<style scoped>
.page.has-batch { padding-bottom: 120rpx; }
.bar { display: flex; justify-content: flex-end; padding: 16rpx 20rpx 0; }
.manage { background: var(--surface); color: var(--brand); border: 1rpx solid var(--brand); margin-right: 16rpx; }
.go { background: var(--brand); color: var(--surface); }
.group-title { padding: 16rpx 24rpx 4rpx; font-size: 28rpx; color: var(--brand); font-weight: bold; }
.card { background: var(--surface); margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.card.sel { box-shadow: 0 0 0 2rpx var(--brand); }
.top { display: flex; justify-content: space-between; font-size: 28rpx; color: var(--text-2); }
.top-left { display: flex; align-items: center; }
.chk { font-size: 34rpx; color: var(--brand); margin-right: 12rpx; }
.tag { color: var(--brand); }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.note { font-size: 28rpx; color: var(--text-3); }
.time { font-size: 24rpx; color: var(--text-3); margin-top: 6rpx; }
.ops { display: flex; justify-content: flex-end; margin-top: 10rpx; }
.op { margin-left: 28rpx; font-size: 30rpx; color: var(--accent); }
.op.del { color: var(--text-3); }
.empty { text-align: center; color: var(--text-3); padding: 80rpx 0; }
.batchbar { position: fixed; left: 0; right: 0; bottom: 0; display: flex; background: var(--surface); border-top: 1rpx solid var(--border); padding: 20rpx 0; }
.bb { flex: 1; text-align: center; font-size: 30rpx; color: var(--accent); }
.bb.del { color: var(--brand); }
.bb.disabled { color: var(--text-3); }
.page { background: var(--bg); min-height: 100vh; }
</style>
