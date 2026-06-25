# 通知体系 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 玩法介绍改名「玩法说明」并新增「通知」类型承载彩票中心历史通知，首页通知栏展示重要通知。

**Architecture:** 复用 guide app 的 PlayGuide：加 `is_important` 字段 + `notice` 类型 + verbose_name 改名；GuideListView 加 `important` 过滤。前端玩法说明页加 notice tab，首页加 NoticeBar 组件拉重要通知。通知由运营 admin 录入。

**Tech Stack:** Django 5.2 + DRF（pytest + APIClient）；uni-app Vue3（vitest，mock request）。

## Global Constraints

- 后端 logging 不用 print；API 统一 make_response（code=0/1）。
- 复用 PlayGuide，不新建模型；通知 admin 录入。
- `is_important` 默认 False；`?important=1` 过滤 is_important=True。
- 前端无 Pinia/Vuex；api 走 request；首页通知拉取失败不阻塞首页。
- 不删既有测试。

---

### Task 1: 后端 PlayGuide 通知字段与过滤

**Files:**
- Modify: `lottery_backend/guide/models.py`（加 notice type + is_important + 改 verbose_name）
- Modify: `lottery_backend/guide/serializers.py`（两 serializer 加 is_important）
- Modify: `lottery_backend/guide/views.py`（GuideListView 加 important 过滤）
- Modify: `lottery_backend/guide/admin.py`（list_display/filter/editable 加 is_important）
- Create: migration（makemigrations 自动生成）
- Test: `lottery_backend/guide/tests/test_api_guide.py`（加 important + serializer 用例）

**Interfaces:**
- Produces:
  - PlayGuide 新增 `is_important`(bool)、`notice` 类型
  - `GET /api/openapi/guide/list?important=1` → 只返回 is_important 可见条目
  - list/detail serializer 含 `is_important`

- [ ] **Step 1: 写失败测试**

`lottery_backend/guide/tests/test_api_guide.py` 末尾追加：
```python
def test_list_important_filter(ssq):
    PlayGuide.objects.create(lottery=ssq, type="notice", title="重要通知", is_important=True)
    PlayGuide.objects.create(lottery=ssq, type="notice", title="普通通知", is_important=False)
    titles = [g["title"] for g in APIClient().get("/api/openapi/guide/list?code=ssq&important=1").json()["data"]]
    assert "重要通知" in titles
    assert "普通通知" not in titles


def test_list_serializer_has_is_important(ssq):
    PlayGuide.objects.create(lottery=ssq, type="notice", title="通知", is_important=True)
    data = APIClient().get("/api/openapi/guide/list?code=ssq").json()["data"]
    assert data[0]["is_important"] is True


def test_list_notice_type_filter(ssq):
    PlayGuide.objects.create(lottery=ssq, type="notice", title="通知一")
    PlayGuide.objects.create(lottery=ssq, type="intro", title="玩法一")
    titles = [g["title"] for g in APIClient().get("/api/openapi/guide/list?code=ssq&type=notice").json()["data"]]
    assert titles == ["通知一"]
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_backend && python -m pytest guide/tests/test_api_guide.py -v`
Expected: FAIL（`is_important` 字段不存在 / serializer 无该字段）

- [ ] **Step 3: 改模型**

`lottery_backend/guide/models.py`：
- 把 type 常量段改为：
```python
    TYPE_INTRO = "intro"
    TYPE_RULE = "rule"
    TYPE_ACTIVITY = "activity"
    TYPE_NOTICE = "notice"
    TYPE_CHOICES = [(TYPE_INTRO, "玩法说明"), (TYPE_RULE, "奖级规则"),
                    (TYPE_ACTIVITY, "活动公告"), (TYPE_NOTICE, "通知公告")]
```
- 在 `is_active` 字段后加：
```python
    is_important = models.BooleanField("重要通知", default=False)
```
- Meta 的 `verbose_name = verbose_name_plural = "玩法介绍"` 改为 `"玩法说明"`。

- [ ] **Step 4: 生成迁移**

Run: `cd lottery_backend && python manage.py makemigrations guide`
Expected: 生成 `guide/migrations/000X_*.py`（加 is_important + alter type choices）。

- [ ] **Step 5: serializer 加 is_important**

`lottery_backend/guide/serializers.py`：`GuideListSerializer.Meta.fields` 与 `GuideDetailSerializer.Meta.fields` 都加 `"is_important"`：
```python
        fields = ["id", "type", "type_label", "title", "sort", "publish_at", "is_important"]
```
```python
        fields = ["id", "type", "type_label", "title", "content", "sort", "publish_at", "is_important"]
```

- [ ] **Step 6: view 加 important 过滤**

`lottery_backend/guide/views.py` `GuideListView.get` 中，在 type 过滤之后、return 之前加：
```python
        if request.query_params.get("important"):
            qs = qs.filter(is_important=True)
```

- [ ] **Step 7: admin 加 is_important**

`lottery_backend/guide/admin.py` 的 `PlayGuideAdmin` 改为：
```python
@admin.register(PlayGuide)
class PlayGuideAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "lottery", "is_active", "is_important", "sort", "publish_at")
    list_filter = ("type", "is_active", "is_important", "lottery")
    search_fields = ("title", "content")
    list_editable = ("is_active", "is_important", "sort")
```

- [ ] **Step 8: 跑测试通过 + 全量回归**

Run: `cd lottery_backend && python -m pytest guide/tests/test_api_guide.py -v && python -m pytest -q`
Expected: 新增 3 用例 PASS；全量无回归。

- [ ] **Step 9: 提交**

```bash
git add lottery_backend/guide/models.py lottery_backend/guide/serializers.py lottery_backend/guide/views.py lottery_backend/guide/admin.py lottery_backend/guide/migrations/ lottery_backend/guide/tests/test_api_guide.py
git commit -m "feat: 玩法说明加通知类型与重要通知字段+important过滤"
```

---

### Task 2: 前端 玩法说明改名 + 通知 tab

**Files:**
- Modify: `lottery_frontend/src/pages/guide/index.vue`（标题改名 + notice tab）
- Modify: `lottery_frontend/src/utils/menu.js`（guide 项改名）
- Test: `lottery_frontend/tests/menu.test.js`（加 guide title 断言）

**Interfaces:**
- Consumes: 后端 `type=notice` 过滤（Task 1）。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/menu.test.js`：在第二个 it（nav 断言）里追加：
```js
    expect(byKey.guide.title).toBe('玩法说明')
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- menu`
Expected: FAIL（guide.title 仍为 '玩法介绍'）

- [ ] **Step 3: menu 改名**

`lottery_frontend/src/utils/menu.js`：把 guide 行 `title: '玩法介绍'` 改为 `title: '玩法说明'`（该行其余不变：`{ key: 'guide', title: '玩法说明', icon: '📖', path: '/pages/guide/index', nav: 'navigateTo' },`）。

- [ ] **Step 4: guide 页改名 + notice tab**

`lottery_frontend/src/pages/guide/index.vue`：
- TopBanner 标题：`<TopBanner title="玩法介绍" />` → `<TopBanner title="玩法说明" />`。
- `types` 数组在 `{ key: 'activity', label: '活动' }` 之后加一项：
```js
  { key: 'notice', label: '通知' },
```

- [ ] **Step 5: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/pages/guide/index.vue lottery_frontend/src/utils/menu.js lottery_frontend/tests/menu.test.js
git commit -m "feat: 玩法介绍改名玩法说明+通知tab"
```

---

### Task 3: 前端 首页通知栏

**Files:**
- Modify: `lottery_frontend/src/api/guide.js`（加 getNotices）
- Create: `lottery_frontend/src/components/NoticeBar.vue`
- Modify: `lottery_frontend/src/pages/home/index.vue`（插入通知栏）
- Test: `lottery_frontend/tests/guide.test.js`（加 getNotices 用例）

**Interfaces:**
- Consumes: `GET /api/openapi/guide/list?important=1`（Task 1）。
- Produces: `getNotices(code)` → request `/api/openapi/guide/list` data `{important:1, code?}`。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/guide.test.js`：import 行追加 `getNotices`：
```js
import { getGuideList, getGuideDetail, getNotices } from '../src/api/guide.js'
```
在 `describe('guide api', ...)` 内追加：
```js
  it('getNotices 带 code', async () => {
    await getNotices('ssq')
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/list', { data: { important: 1, code: 'ssq' } })
  })
  it('getNotices 无 code', async () => {
    await getNotices('')
    expect(request).toHaveBeenCalledWith('/api/openapi/guide/list', { data: { important: 1 } })
  })
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- guide`
Expected: FAIL（getNotices 未导出）

- [ ] **Step 3: api 加 getNotices**

`lottery_frontend/src/api/guide.js` 末尾追加：
```js
export function getNotices(code) {
  const data = { important: 1 }
  if (code) data.code = code
  return request('/api/openapi/guide/list', { data })
}
```

- [ ] **Step 4: NoticeBar 组件**

`lottery_frontend/src/components/NoticeBar.vue`：
```vue
<template>
  <view v-if="notice" class="notice-bar" @click="$emit('tap')">
    <text class="ico">📢</text>
    <text class="txt">{{ notice.title }}</text>
    <text class="more">详情</text>
  </view>
</template>

<script setup>
defineProps({ notice: { type: Object, default: null } })
defineEmits(['tap'])
</script>

<style scoped>
.notice-bar { display: flex; align-items: center; background: #fff8e1; margin: 16rpx 20rpx 0; padding: 16rpx 20rpx; border-radius: 12rpx; }
.ico { font-size: 30rpx; margin-right: 12rpx; }
.txt { flex: 1; font-size: 28rpx; color: #8a6d3b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.more { font-size: 24rpx; color: #e53935; margin-left: 12rpx; }
</style>
```

- [ ] **Step 5: home 插入通知栏（整体替换）**

`lottery_frontend/src/pages/home/index.vue` 整体替换为：
```vue
<template>
  <view class="home">
    <view class="banner"><text class="bt">彩票查询</text></view>
    <NoticeBar :notice="topNotice" @tap="goNotices" />
    <view class="grid">
      <view v-for="m in menu" :key="m.key" class="mcard" @click="go(m)">
        <text class="ic">{{ m.icon }}</text>
        <text class="tx">{{ m.title }}</text>
      </view>
    </view>
    <view class="footer">
      <view class="links">
        <text class="lk" @click="openDoc('agreement')">用户协议</text>
        <text class="sep">·</text>
        <text class="lk" @click="openDoc('privacy')">隐私协议</text>
      </view>
      <text class="src">数据来源：中国福彩网 cwl.gov.cn · 中国体彩网 sporttery.cn</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import NoticeBar from '../../components/NoticeBar.vue'
import { HOME_MENU, goMenu } from '../../utils/menu.js'
import { getNotices } from '../../api/guide.js'
import { lotteryStore } from '../../store/lottery.js'

const menu = HOME_MENU
const topNotice = ref(null)
function go(m) { goMenu(m) }
function openDoc(type) { uni.navigateTo({ url: `/pages/legal/doc?type=${type}` }) }
function goNotices() { uni.navigateTo({ url: '/pages/guide/index' }) }

onShow(async () => {
  try {
    const list = await getNotices(lotteryStore.code)
    topNotice.value = (list && list.length) ? list[0] : null
  } catch (e) {
    topNotice.value = null
  }
})
</script>

<style scoped>
.home { min-height: 100vh; background: linear-gradient(180deg, #ffd9d4 0%, #fff0ee 35%, #fbfbfb 100%); }
.banner { background: linear-gradient(180deg, #e53935 0%, #ff6f61 100%); padding: 44rpx 0; text-align: center; }
.bt { color: #fff; font-size: 42rpx; font-weight: 700; letter-spacing: 8rpx; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24rpx; padding: 28rpx; }
.mcard { background: #fff; border-radius: 20rpx; padding: 44rpx 0; text-align: center; box-shadow: 0 4rpx 16rpx rgba(229, 57, 53, 0.10); }
.ic { font-size: 56rpx; display: block; }
.tx { font-size: 32rpx; font-weight: 600; color: #333; display: block; margin-top: 14rpx; }
.footer { padding: 20rpx 28rpx 40rpx; text-align: center; }
.links { margin-bottom: 12rpx; }
.lk { color: #e53935; font-size: 26rpx; }
.sep { color: #bbb; font-size: 26rpx; margin: 0 12rpx; }
.src { color: #999; font-size: 22rpx; display: block; line-height: 1.6; }
</style>
```

- [ ] **Step 6: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/api/guide.js lottery_frontend/src/components/NoticeBar.vue lottery_frontend/src/pages/home/index.vue lottery_frontend/tests/guide.test.js
git commit -m "feat: 首页通知栏展示重要通知"
```

---

## 计划自检

**1. Spec 覆盖：**
- is_important 字段 + notice 类型 + verbose_name 改名（spec §2.1）→ Task 1 Step 3 ✓
- serializer 含 is_important（spec §2.2）→ Task 1 Step 5 ✓
- GuideListView important 过滤（spec §2.3）→ Task 1 Step 6 ✓
- admin is_important（spec §2.4）→ Task 1 Step 7 ✓
- 玩法说明改名 + notice tab（spec §3）→ Task 2 ✓
- 首页通知栏 + NoticeBar + getNotices（spec §4）→ Task 3 ✓
- 错误处理 首页失败不阻塞（spec §5）→ Task 3 home onShow try/catch ✓
- 测试（spec §6）→ Task 1（important/serializer/notice 后端）、Task 2（menu title）、Task 3（getNotices）✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码与确切命令。

**3. 类型/签名一致性：** `getNotices(code)` 在 api、测试、home 一致；`is_important` 在模型、serializer、view、测试一致；`?important=1`/`type=notice` 在 view、前端、测试一致；NoticeBar props `notice`、emit `tap` 在组件与 home 一致；HOME_MENU guide title '玩法说明' 在 menu.js 与 menu.test 一致。
