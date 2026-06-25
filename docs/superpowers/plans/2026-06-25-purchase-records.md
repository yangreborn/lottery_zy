# 购买记录 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 记录用户每期实际购买的号码（独立于「我的号码」），含后端独立表+CRUD、前端列表页+手选新增页+从「我的号码」一键转入。

**Architecture:** 后端 `usernumber` app 加 `PurchaseRecord` 模型 + serializer + 3 接口（create/list/delete）。前端首页菜单加入口，新增列表页与手选新增页（复用 `getZones`/`BallSelectable`/`picker.js` 工具），「我的号码」每条加「标为已购」一键转入。

**Tech Stack:** Django 5.2 + DRF（pytest + APIClient）；uni-app Vue3（vitest，mock request）。

## Global Constraints

- 后端用 `logging` 标准库，不用 `print`；API 统一 `make_response`（成功 code=0/失败 code=1）。
- 用户标识 hash：`current_user_id(request)`；所有查询/删除带 `user_id=uid` 只动本人记录。
- `PurchaseRecord` 与 `UserNumber` 完全独立（不同表）。
- 号码校验复用 `validate_numbers(rule_config, numbers)`；彩种用 `_get_active_lottery(code)`。
- 删除前端必须 `showModal` 确认（note 24）。
- 前端无 Pinia/Vuex；api 走 `request`；手选复用既有工具，不合并 picker 组件。
- bet_count 默认 1、<1 取 1；purchase_date 缺省今天。
- 不删既有测试。

---

### Task 1: 后端 PurchaseRecord（模型+serializer+admin+3接口+迁移）

**Files:**
- Modify: `lottery_backend/usernumber/models.py`（加 PurchaseRecord）
- Modify: `lottery_backend/usernumber/serializers.py`（加 PurchaseRecordSerializer）
- Modify: `lottery_backend/usernumber/admin.py`（注册 PurchaseRecord）
- Modify: `lottery_backend/usernumber/views.py`（加 3 个 View）
- Modify: `lottery_backend/usernumber/urls.py`（加 3 条路由）
- Create: migration（makemigrations 自动生成）
- Test: `lottery_backend/usernumber/tests/test_purchase.py`

**Interfaces:**
- Produces:
  - `PurchaseRecord` 模型（user_id/lottery/issue/numbers/bet_count/purchase_date/created_at）
  - `POST /api/user/purchase/create` `{code, issue, numbers, bet_count?, purchase_date?}` → serializer data
  - `GET /api/user/purchase/list?code=` → list
  - `DELETE /api/user/purchase/<id>` → `{deleted: True}`

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_purchase.py`：
```python
import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from lottery.models import Lottery
from usernumber.models import PurchaseRecord
from common.auth import hash_user_id


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


VALID = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}


def _make(openid, lottery, issue="2026073"):
    return PurchaseRecord.objects.create(
        user_id=hash_user_id(openid), lottery=lottery,
        issue=issue, numbers=VALID, purchase_date="2026-06-20",
    )


def test_purchase_create(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": VALID, "bet_count": 2, "purchase_date": "2026-06-20"},
        format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["issue"] == "2026073"
    assert body["data"]["bet_count"] == 2
    assert str(body["data"]["purchase_date"]) == "2026-06-20"
    assert body["data"]["code"] == "ssq"


def test_purchase_create_issue_required(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "  ", "numbers": VALID}, format="json")
    assert resp.json()["code"] == 1
    assert PurchaseRecord.objects.count() == 0


def test_purchase_create_invalid_numbers(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": {"red": [1], "blue": [7]}}, format="json")
    assert resp.json()["code"] == 1


def test_purchase_create_defaults(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": VALID}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["bet_count"] == 1
    rec = PurchaseRecord.objects.get(id=body["data"]["id"])
    assert rec.purchase_date == timezone.now().date()


def test_purchase_create_unauthenticated(ssq):
    resp = APIClient().post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": VALID}, format="json")
    assert resp.json()["code"] == 1


def test_purchase_list_only_own(ssq, auth_client):
    _make("tester-openid", ssq)
    _make("other-openid", ssq)
    resp = auth_client.get("/api/user/purchase/list")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) == 1


def test_purchase_delete_own(ssq, auth_client):
    rec = _make("tester-openid", ssq)
    resp = auth_client.delete(f"/api/user/purchase/{rec.id}")
    assert resp.json()["code"] == 0
    assert not PurchaseRecord.objects.filter(id=rec.id).exists()


def test_purchase_delete_other_forbidden(ssq, auth_client):
    rec = _make("other-openid", ssq)
    resp = auth_client.delete(f"/api/user/purchase/{rec.id}")
    assert resp.json()["code"] == 1
    assert PurchaseRecord.objects.filter(id=rec.id).exists()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_purchase.py -v`
Expected: FAIL（`PurchaseRecord` 无法 import）

- [ ] **Step 3: 加模型**

`lottery_backend/usernumber/models.py` 末尾追加（顶部已 `from lottery.models import Lottery`）：
```python
class PurchaseRecord(models.Model):
    """用户实际购买记录，独立于 UserNumber(只选不买)。"""
    user_id = models.CharField("用户哈希", max_length=64, db_index=True)
    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE,
                                related_name="purchases", verbose_name="彩种")
    issue = models.CharField("期号", max_length=20)
    numbers = models.JSONField("号码", default=dict)
    bet_count = models.PositiveIntegerField("注数", default=1)
    purchase_date = models.DateField("购买日期")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "购买记录"
        ordering = ["-purchase_date", "-created_at"]

    def __str__(self):
        return f"{self.user_id[:8]} {self.lottery.code} {self.issue}"
```

- [ ] **Step 4: 加 serializer**

`lottery_backend/usernumber/serializers.py`：import 行改为 `from usernumber.models import UserNumber, PurchaseRecord`，末尾追加：
```python
class PurchaseRecordSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="lottery.code", read_only=True)

    class Meta:
        model = PurchaseRecord
        fields = ["id", "code", "issue", "numbers", "bet_count", "purchase_date", "created_at"]
```

- [ ] **Step 5: 生成迁移**

Run: `cd lottery_backend && python manage.py makemigrations usernumber`
Expected: 生成 `usernumber/migrations/000X_purchaserecord.py`。

- [ ] **Step 6: 注册 admin**

`lottery_backend/usernumber/admin.py`：import 行改为 `from usernumber.models import UserNumber, Feedback, PurchaseRecord`，末尾追加：
```python
@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "lottery", "issue", "bet_count", "purchase_date", "created_at")
    list_filter = ("lottery",)
    search_fields = ("user_id", "issue")
```

- [ ] **Step 7: 加 3 个 View**

`lottery_backend/usernumber/views.py`：
顶部 import 段补充：
```python
from django.utils import timezone
from django.utils.dateparse import parse_date
```
并把 `from usernumber.models import UserNumber, Feedback` 改为 `from usernumber.models import UserNumber, Feedback, PurchaseRecord`；
`from usernumber.serializers import UserNumberSerializer` 改为 `from usernumber.serializers import UserNumberSerializer, PurchaseRecordSerializer`。
文件末尾追加：
```python
class PurchaseCreateView(APIView):
    """POST /api/user/purchase/create —— 记录一条实际购买。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        code = request.data.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        issue = str(request.data.get("issue") or "").strip()
        if not issue:
            return Response(make_response(code=1, msg="请填写期号"))
        numbers = request.data.get("numbers") or {}
        errors = validate_numbers(lottery.rule_config, numbers)
        if errors:
            return Response(make_response(code=1, msg="号码非法", error="; ".join(errors)))
        try:
            bet_count = int(request.data.get("bet_count", 1))
        except (TypeError, ValueError):
            bet_count = 1
        if bet_count < 1:
            bet_count = 1
        raw_date = request.data.get("purchase_date")
        if raw_date:
            parsed = parse_date(str(raw_date))
            if parsed is None:
                return Response(make_response(code=1, msg="购买日期非法"))
            purchase_date = parsed
        else:
            purchase_date = timezone.now().date()
        rec = PurchaseRecord.objects.create(
            user_id=uid, lottery=lottery, issue=issue, numbers=numbers,
            bet_count=bet_count, purchase_date=purchase_date,
        )
        return Response(make_response(data=PurchaseRecordSerializer(rec).data))


class PurchaseListView(APIView):
    """GET /api/user/purchase/list?code= —— 当前用户购买记录。"""
    authentication_classes = []

    def get(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        qs = PurchaseRecord.objects.filter(user_id=uid)
        code = request.query_params.get("code")
        if code:
            qs = qs.filter(lottery__code=code)
        return Response(make_response(data=PurchaseRecordSerializer(qs, many=True).data))


class PurchaseDeleteView(APIView):
    """DELETE /api/user/purchase/<id> —— 删除自己的购买记录。"""
    authentication_classes = []

    def delete(self, request, pk):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        rec = PurchaseRecord.objects.filter(id=pk, user_id=uid).first()
        if rec is None:
            return Response(make_response(code=1, msg="记录不存在"))
        rec.delete()
        return Response(make_response(data={"deleted": True}))
```

- [ ] **Step 8: 注册路由**

`lottery_backend/usernumber/urls.py` 的 `urlpatterns` 末尾追加（在 `number/<int:pk>` 之后即可，purchase 前缀不冲突）：
```python
    path("purchase/create", views.PurchaseCreateView.as_view(), name="user-purchase-create"),
    path("purchase/list", views.PurchaseListView.as_view(), name="user-purchase-list"),
    path("purchase/<int:pk>", views.PurchaseDeleteView.as_view(), name="user-purchase-delete"),
```

- [ ] **Step 9: 跑测试通过 + 全量回归**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_purchase.py -v && python -m pytest -q`
Expected: 8 用例 PASS；全量无回归。

- [ ] **Step 10: 提交**

```bash
git add lottery_backend/usernumber/models.py lottery_backend/usernumber/serializers.py lottery_backend/usernumber/admin.py lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/migrations/ lottery_backend/usernumber/tests/test_purchase.py
git commit -m "feat: 后端购买记录PurchaseRecord模型+接口+admin"
```

---

### Task 2: 前端 api + 列表页 + 入口

**Files:**
- Modify: `lottery_frontend/src/api/user.js`（加 purchaseCreate/purchaseList/purchaseDelete）
- Modify: `lottery_frontend/src/utils/menu.js`（加购买记录入口）
- Create: `lottery_frontend/src/pages/purchase/index.vue`
- Modify: `lottery_frontend/src/pages.json`（注册 purchase/index）
- Test: `lottery_frontend/tests/user.test.js`、`lottery_frontend/tests/menu.test.js`

**Interfaces:**
- Consumes: Task 1 的 3 个接口。
- Produces: `purchaseCreate(payload)`、`purchaseList(code)`、`purchaseDelete(id)`（供 Task 3/4）。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/user.test.js`：import 行追加 `purchaseCreate, purchaseList, purchaseDelete`：
```js
import { login, createNumber, listNumbers, deleteNumber, checkNumber, generateNumbers, submitFeedback, batchDelete, batchGroup, purchaseCreate, purchaseList, purchaseDelete } from '../src/api/user.js'
```
在 `describe('user api', ...)` 内追加：
```js
  it('purchaseCreate', async () => {
    await purchaseCreate({ code: 'ssq', issue: '2026073', numbers: { red: [1] }, bet_count: 2, purchase_date: '2026-06-20' })
    expect(request).toHaveBeenCalledWith('/api/user/purchase/create', { method: 'POST', data: { code: 'ssq', issue: '2026073', numbers: { red: [1] }, bet_count: 2, purchase_date: '2026-06-20' } })
  })
  it('purchaseList 带 code', async () => {
    await purchaseList('ssq')
    expect(request).toHaveBeenCalledWith('/api/user/purchase/list', { data: { code: 'ssq' } })
  })
  it('purchaseList 无 code', async () => {
    await purchaseList('')
    expect(request).toHaveBeenCalledWith('/api/user/purchase/list', { data: {} })
  })
  it('purchaseDelete', async () => {
    await purchaseDelete(5)
    expect(request).toHaveBeenCalledWith('/api/user/purchase/5', { method: 'DELETE' })
  })
```

`lottery_frontend/tests/menu.test.js`：把 `expect(HOME_MENU.length).toBe(7)` 改为 `toBe(8)`；在 nav 断言处追加 `expect(byKey.purchase.nav).toBe('navigateTo')`。

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- user menu`
Expected: FAIL（purchase* 未导出 / purchase 项不存在）

- [ ] **Step 3: api 加 3 函数**

`lottery_frontend/src/api/user.js` 末尾追加：
```js
export function purchaseCreate(payload) {
  return request('/api/user/purchase/create', { method: 'POST', data: payload })
}

export function purchaseList(code) {
  return request('/api/user/purchase/list', { data: code ? { code } : {} })
}

export function purchaseDelete(id) {
  return request(`/api/user/purchase/${id}`, { method: 'DELETE' })
}
```

- [ ] **Step 4: menu 加入口**

`lottery_frontend/src/utils/menu.js`：在 `feedback` 行之后、数组 `]` 之前追加：
```js
  { key: 'purchase', title: '购买记录', icon: '🛒', path: '/pages/purchase/index', nav: 'navigateTo' },
```

- [ ] **Step 5: 列表页**

`lottery_frontend/src/pages/purchase/index.vue`：
```vue
<template>
  <view class="page">
    <TopBanner title="购买记录" :back="true" />
    <LotteryTabs :list="lotteries" :active="store.code" @change="onChange" />
    <view class="bar"><button class="go" size="mini" @click="goCreate">新增购买</button></view>
    <view v-for="rec in items" :key="rec.id" class="card">
      <view class="top">
        <text class="issue">第 {{ rec.issue }} 期</text>
        <text class="date">{{ rec.purchase_date }}</text>
      </view>
      <view class="balls">
        <template v-for="(nums, key) in rec.numbers">
          <Ball v-for="(n, i) in nums" :key="key + i" :value="n" :zone="key" :pad="key === 'digits' ? 1 : 2" />
        </template>
      </view>
      <view class="meta">
        <text class="bet">{{ rec.bet_count }} 注</text>
        <text class="op del" @click="doDelete(rec.id)">删除</text>
      </view>
    </view>
    <view v-if="!items.length" class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import LotteryTabs from '../../components/LotteryTabs.vue'
import Ball from '../../components/Ball.vue'
import { lotteryStore, setCode } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, purchaseList, purchaseDelete } from '../../api/user.js'

const store = lotteryStore
const lotteries = ref([])
const items = ref([])
const emptyMsg = ref('加载中…')

async function load() {
  emptyMsg.value = '加载中…'
  try {
    await ensureLogin()
    items.value = await purchaseList(store.code)
    if (!items.value.length) emptyMsg.value = '还没有购买记录'
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
}

function onChange(code) { setCode(code); load() }
function goCreate() { uni.navigateTo({ url: '/pages/purchase/create' }) }

function doDelete(id) {
  uni.showModal({
    title: '确认删除',
    content: '删除后不可恢复，确定删除这条购买记录？',
    success: async (res) => {
      if (!res.confirm) return
      try { await purchaseDelete(id); load() }
      catch (e) { uni.showToast({ title: e.msg || '删除失败', icon: 'none' }) }
    },
  })
}

onShow(async () => {
  if (!lotteries.value.length) {
    try { lotteries.value = await getLotteryList() } catch (e) { /* 容错: 彩种拉取失败不阻塞 */ }
  }
  load()
})
</script>

<style scoped>
.bar { display: flex; justify-content: flex-end; padding: 16rpx 20rpx 0; }
.go { background: #e53935; color: #fff; }
.card { background: #fff; margin: 16rpx 20rpx; padding: 24rpx; border-radius: 12rpx; }
.top { display: flex; justify-content: space-between; font-size: 30rpx; color: #888; }
.balls { display: flex; flex-wrap: wrap; margin: 14rpx 0; }
.meta { display: flex; justify-content: space-between; align-items: center; }
.bet { font-size: 28rpx; color: #fb8c00; }
.op.del { font-size: 30rpx; color: #999; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 6: pages.json 注册 index**

`lottery_frontend/src/pages.json` 的 `pages` 数组里，在 `pages/feedback/index` 行后加（给 feedback 行末补逗号）：
```json
    { "path": "pages/purchase/index", "style": { "navigationBarTitleText": "购买记录" } }
```

- [ ] **Step 7: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 8: 提交**

```bash
git add lottery_frontend/src/api/user.js lottery_frontend/src/utils/menu.js lottery_frontend/src/pages/purchase/index.vue lottery_frontend/src/pages.json lottery_frontend/tests/user.test.js lottery_frontend/tests/menu.test.js
git commit -m "feat: 购买记录列表页+首页入口+api"
```

---

### Task 3: 前端 手选新增页

**Files:**
- Modify: `lottery_frontend/src/utils/records.js`（加 todayStr）
- Create: `lottery_frontend/src/pages/purchase/create.vue`
- Modify: `lottery_frontend/src/pages.json`（注册 purchase/create）
- Test: `lottery_frontend/tests/records.test.js`（加 todayStr 用例）

**Interfaces:**
- Consumes: `purchaseCreate`（Task 2）；`getZones`、`BallSelectable`、`toggleBall`/`selectionComplete`/`digitsFilled`。
- Produces: `todayStr()` → `'YYYY-MM-DD'`（供 Task 4）。

- [ ] **Step 1: 写 todayStr 失败测试**

`lottery_frontend/tests/records.test.js`：import 行追加 `todayStr`（若该文件无 import 行则新增）。在文件内追加：
```js
import { todayStr } from '../src/utils/records.js'

describe('todayStr', () => {
  it('返回 YYYY-MM-DD 格式', () => {
    expect(todayStr()).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })
})
```
（若 records.test.js 顶部已有 `import { ... } from '../src/utils/records.js'`，把 `todayStr` 加进那一行即可，不重复 import。）

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- records`
Expected: FAIL（todayStr 未导出）

- [ ] **Step 3: records.js 加 todayStr**

`lottery_frontend/src/utils/records.js` 末尾追加：
```js
export function todayStr() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`
}
```

- [ ] **Step 4: 新增选号页**

`lottery_frontend/src/pages/purchase/create.vue`：
```vue
<template>
  <view class="page">
    <TopBanner title="新增购买" :back="true" />
    <template v-if="zones.length">
      <view v-if="variableZone" class="play">
        <text class="pt">玩法（选几个）</text>
        <view class="play-opts">
          <view v-for="k in playOptions" :key="k" class="popt" :class="{ active: k === pickCount }" @click="setPick(k)"><text>选{{ k }}</text></view>
        </view>
      </view>
      <template v-if="digitZone">
        <view v-for="pos in digitZone.count" :key="pos" class="zone">
          <text class="zt">第 {{ pos }} 位（{{ digitAt(pos - 1) }}）</text>
          <view class="grid">
            <view v-for="d in digitRange" :key="d" class="dbtn" :class="{ active: digitAt(pos - 1) === d }" @click="setDigit(pos - 1, d)"><text>{{ d }}</text></view>
          </view>
        </view>
      </template>
      <template v-else>
        <view v-for="zone in zones" :key="zone.key" class="zone">
          <text class="zt">{{ zone.label }}（选 {{ targetOf(zone) }}）</text>
          <view class="grid">
            <BallSelectable v-for="n in rangeOf(zone)" :key="zone.key + n" :value="n" :zone="zone.key" :selected="(sel[zone.key] || []).includes(n)" @toggle="toggle(zone, $event)" />
          </view>
        </view>
      </template>
      <view class="fields">
        <input class="ipt" v-model="issue" placeholder="期号（必填）" />
        <input class="ipt" v-model.number="betCount" type="number" placeholder="注数(默认1)" />
        <picker mode="date" :value="purchaseDate" @change="onDate">
          <view class="ipt date">购买日期：{{ purchaseDate }}</view>
        </picker>
      </view>
      <view class="actions">
        <button class="btn save" :disabled="!canSave" @click="save">保存购买记录</button>
      </view>
    </template>
    <view v-else class="empty">{{ emptyMsg }}</view>
  </view>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import BallSelectable from '../../components/BallSelectable.vue'
import { lotteryStore } from '../../store/lottery.js'
import { getLotteryList } from '../../api/lottery.js'
import { ensureLogin, purchaseCreate } from '../../api/user.js'
import { toggleBall, selectionComplete, digitsFilled } from '../../utils/picker.js'
import { getZones } from '../../utils/zones.js'
import { todayStr } from '../../utils/records.js'

const rule = ref(null)
const emptyMsg = ref('加载中…')
const code = lotteryStore.code
const issue = ref('')
const betCount = ref(1)
const purchaseDate = ref(todayStr())
const sel = reactive({})

const zones = computed(() => getZones(rule.value))
const variableZone = computed(() => zones.value.find((z) => z.pick_min !== undefined && z.pick_max !== undefined) || null)
const digitZone = computed(() => zones.value.find((z) => z.ordered && z.allow_repeat) || null)
const digitRange = computed(() => (digitZone.value ? rangeOf(digitZone.value) : []))
const playOptions = computed(() => {
  const z = variableZone.value
  if (!z) return []
  const arr = []
  for (let k = z.pick_min; k <= z.pick_max; k++) arr.push(k)
  return arr
})
const pickCount = ref(0)
const picksObj = computed(() => (variableZone.value ? { [variableZone.value.key]: pickCount.value } : {}))

function rangeOf(zone) { const arr = []; for (let i = zone.min; i <= zone.max; i++) arr.push(i); return arr }
function targetOf(zone) { if (zone.pick_min !== undefined && zone.pick_max !== undefined) return pickCount.value; return zone.count }
function toggle(zone, n) { sel[zone.key] = toggleBall(sel[zone.key] || [], n, targetOf(zone)) }
function setPick(k) { pickCount.value = k; if (variableZone.value) sel[variableZone.value.key] = [] }
function digitAt(i) { const a = digitZone.value ? sel[digitZone.value.key] : null; return a && a[i] !== null && a[i] !== undefined ? a[i] : '?' }
function setDigit(pos, d) { const key = digitZone.value.key; sel[key] = sel[key].map((v, i) => (i === pos ? d : v)) }
function onDate(e) { purchaseDate.value = e.detail.value }

const canSave = computed(() => {
  if (!rule.value || !issue.value.trim()) return false
  if (digitZone.value) return digitsFilled(sel[digitZone.value.key])
  return selectionComplete(sel, rule.value, picksObj.value)
})

async function save() {
  if (!canSave.value) return
  try {
    await ensureLogin()
    await purchaseCreate({ code, issue: issue.value.trim(), numbers: { ...sel }, bet_count: betCount.value || 1, purchase_date: purchaseDate.value })
    uni.showToast({ title: '已记录', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
  }
}

onLoad(async () => {
  try {
    const list = await getLotteryList()
    const found = list.find((l) => l.code === code)
    if (found) {
      rule.value = found.rule_config
      for (const z of zones.value) {
        sel[z.key] = z.ordered && z.allow_repeat ? new Array(z.count).fill(null) : []
      }
      if (variableZone.value) pickCount.value = variableZone.value.pick_min
    } else {
      emptyMsg.value = '彩种不存在'
    }
  } catch (e) {
    emptyMsg.value = e.msg || '加载失败'
  }
})
</script>

<style scoped>
.play { background: #fff; margin: 16rpx 20rpx 12rpx; padding: 16rpx 20rpx; border-radius: 12rpx; }
.pt { font-size: 28rpx; color: #888; }
.play-opts { display: flex; flex-wrap: wrap; margin-top: 10rpx; }
.popt { padding: 10rpx 22rpx; margin: 6rpx 14rpx 6rpx 0; background: #f5f5f5; border-radius: 28rpx; color: #666; font-size: 28rpx; }
.popt.active { background: #fb8c00; color: #fff; }
.zone { background: #fff; margin: 16rpx 20rpx; padding: 20rpx; border-radius: 12rpx; }
.zt { font-size: 30rpx; color: #666; }
.grid { display: flex; flex-wrap: wrap; margin-top: 12rpx; }
.dbtn { width: 64rpx; height: 64rpx; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; margin: 8rpx; font-size: 32rpx; border: 2rpx solid #43a047; color: #43a047; }
.dbtn.active { background: #43a047; color: #fff; }
.fields { margin: 0 20rpx; }
.ipt { background: #fff; border-radius: 10rpx; padding: 18rpx; margin-top: 16rpx; font-size: 28rpx; }
.ipt.date { color: #555; }
.actions { padding: 24rpx 20rpx; }
.btn.save { width: 100%; background: #e53935; color: #fff; font-size: 30rpx; }
.empty { text-align: center; color: #999; padding: 80rpx 0; }
</style>
```

- [ ] **Step 5: pages.json 注册 create**

`lottery_frontend/src/pages.json` 的 `pages` 数组里，在 `pages/purchase/index` 行后加（给 index 行末补逗号）：
```json
    { "path": "pages/purchase/create", "style": { "navigationBarTitleText": "新增购买" } }
```

- [ ] **Step 6: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/utils/records.js lottery_frontend/src/pages/purchase/create.vue lottery_frontend/src/pages.json lottery_frontend/tests/records.test.js
git commit -m "feat: 购买记录手选新增页"
```

---

### Task 4: 我的号码一键转入购买

**Files:**
- Modify: `lottery_frontend/src/pages/mine/index.vue`（每条加「标为已购」）

**Interfaces:**
- Consumes: `purchaseCreate`（Task 2）、`todayStr`（Task 3）。

- [ ] **Step 1: mine 页加转入逻辑**

`lottery_frontend/src/pages/mine/index.vue`：
① import 段：把 `import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup, batchDelete, batchGroup } from '../../api/user.js'` 改为追加 `purchaseCreate`：
```js
import { ensureLogin, listNumbers, deleteNumber, checkNumber, setGroup, batchDelete, batchGroup, purchaseCreate } from '../../api/user.js'
```
并把 `import { formatTime, groupRecords } from '../../utils/records.js'` 改为追加 `todayStr`：
```js
import { formatTime, groupRecords, todayStr } from '../../utils/records.js'
```

② 模板里单条 ops（`<view v-if="!manageMode" class="ops">`）的「归组」之前加一项：
```html
          <text class="op" @click="doMarkPurchased(rec)">标为已购</text>
```

③ script 加函数（放在 doGroup 之前或之后）：
```js
function doMarkPurchased(rec) {
  uni.showModal({
    title: '标为已购',
    editable: true,
    placeholderText: '输入购买期号',
    success: async (res) => {
      if (!res.confirm) return
      const issue = (res.content || '').trim()
      if (!issue) { uni.showToast({ title: '请填期号', icon: 'none' }); return }
      try {
        await purchaseCreate({ code: store.code, issue, numbers: rec.numbers, bet_count: 1, purchase_date: todayStr() })
        uni.showToast({ title: '已记录购买', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.msg || '记录失败', icon: 'none' })
      }
    },
  })
}
```

- [ ] **Step 2: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿（无新增测试，回归不破）；`Build complete.`

- [ ] **Step 3: 提交**

```bash
git add lottery_frontend/src/pages/mine/index.vue
git commit -m "feat: 我的号码一键标为已购转入购买记录"
```

---

## 计划自检

**1. Spec 覆盖：**
- PurchaseRecord 模型（spec §1）→ Task 1 Step 3 ✓
- serializer/admin/迁移（spec §1）→ Task 1 Step 4/6/5 ✓
- create/list/delete 接口 + 校验（spec §2）→ Task 1 Step 7 + 测试 ✓
- 首页入口（spec §3.1）→ Task 2 Step 4 ✓
- 列表页（spec §3.2）→ Task 2 Step 5 ✓
- 手选新增页（spec §3.3）→ Task 3 Step 4 ✓
- 一键转入（spec §3.4）→ Task 4 ✓
- api（spec §3.5）→ Task 2 Step 3 ✓
- 错误处理（spec §4）→ Task 1 校验分支 + 前端 toast ✓
- 测试（spec §5）→ Task 1（8 后端用例）、Task 2（api+menu）、Task 3（todayStr）✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码与确切命令。

**3. 类型/签名一致性：** `purchaseCreate(payload)`/`purchaseList(code)`/`purchaseDelete(id)` 在 api、测试、列表页、新增页、mine 一致；端点 `/api/user/purchase/create|list|<id>` 在 url、view、api、测试一致；`PurchaseRecord` 字段 issue/numbers/bet_count/purchase_date 在模型、serializer、view、测试、前端展示一致；`todayStr()` 在 records.js 定义、create/mine 消费一致；HOME_MENU 加 purchase 后 length=8 与 menu.test 一致。
