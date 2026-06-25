# IA 改名 + 我要反馈 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 消除「选号记录/我的号码」命名混淆（改名），新增「我要反馈」（后端 Feedback 存储 + 首页入口 + 反馈页）。

**Architecture:** 后端在 `usernumber` app 加 `Feedback` 模型 + admin + `POST /api/user/feedback`（匿名可提交、content 必填≤500）。前端 `HOME_MENU` 改名 picker 标题、加反馈入口，新增反馈页 + `submitFeedback` api。两任务（后端、前端）各自独立可测。

**Tech Stack:** Django 5.2 + DRF（pytest + APIClient）；uni-app Vue3（vitest，mock request）。

## Global Constraints

- 后端用 `logging` 标准库记录异常，不用 `print`（记录异常偏好 `logging.error(..., exc_info=True)`）。
- API 统一返回 `make_response(data, code, msg, error)`（`common/utils.py`）；成功 `code=0`，失败 `code=1`。
- 用户标识用 hash：`current_user_id(request)`（session uid 或 X-User-Id 头），匿名时为 `None` → 存空串。
- 配置只放密钥；接口端点直接写代码。
- 前端无 Pinia/Vuex；api 走 `request` 封装。
- content 校验：去首尾空白后非空、长度 ≤ 500。
- 不删既有测试（新增项导致 `menu.test.js` 计数变化属合理更新，非删除）。

---

### Task 1: 后端 Feedback（模型 + admin + 接口）

**Files:**
- Modify: `lottery_backend/usernumber/models.py`（加 `Feedback`）
- Create: `lottery_backend/usernumber/admin.py`
- Modify: `lottery_backend/usernumber/views.py`（加 `FeedbackCreateView`）
- Modify: `lottery_backend/usernumber/urls.py`（加路由）
- Create: `lottery_backend/usernumber/migrations/000X_feedback.py`（makemigrations 自动生成）
- Test: `lottery_backend/usernumber/tests/test_feedback.py`

**Interfaces:**
- Produces:
  - `Feedback` 模型：字段 `user_id`(str)、`content`(text)、`contact`(str)、`created_at`(datetime)
  - `POST /api/user/feedback`，body `{content: str, contact?: str}` → `make_response(data={"id": int})` 或 `code=1`

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_feedback.py`：
```python
import pytest
from rest_framework.test import APIClient
from usernumber.models import Feedback


@pytest.fixture
def api_client():
    return APIClient()


def test_feedback_create_anonymous(db, api_client):
    resp = api_client.post("/api/user/feedback", {"content": "界面建议调大字体"}, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["id"]
    rec = Feedback.objects.get(id=body["data"]["id"])
    assert rec.user_id == ""
    assert rec.content == "界面建议调大字体"


def test_feedback_empty_content_rejected(db, api_client):
    resp = api_client.post("/api/user/feedback", {"content": "   "}, format="json")
    assert resp.json()["code"] == 1
    assert Feedback.objects.count() == 0


def test_feedback_too_long_rejected(db, api_client):
    resp = api_client.post("/api/user/feedback", {"content": "x" * 501}, format="json")
    assert resp.json()["code"] == 1
    assert Feedback.objects.count() == 0
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_feedback.py -v`
Expected: FAIL（`Feedback` 无法 import / 接口 404）

- [ ] **Step 3: 加 Feedback 模型**

`lottery_backend/usernumber/models.py` 末尾追加（文件顶部已有 `from django.db import models`）：
```python
class Feedback(models.Model):
    """用户反馈。user_id 存 hash，匿名时为空串。"""
    user_id = models.CharField("用户哈希", max_length=64, blank=True, default="", db_index=True)
    content = models.TextField("反馈内容")
    contact = models.CharField("联系方式", max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户反馈"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id[:8] or '匿名'} {self.content[:20]}"
```

- [ ] **Step 4: 生成迁移**

Run: `cd lottery_backend && python manage.py makemigrations usernumber`
Expected: 生成 `usernumber/migrations/000X_feedback.py`，含 Feedback 建表。

- [ ] **Step 5: 加 admin**

`lottery_backend/usernumber/admin.py`（新建）：
```python
from django.contrib import admin

from usernumber.models import UserNumber, Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "short_content", "contact", "user_id", "created_at")
    search_fields = ("content", "contact")
    readonly_fields = ("user_id", "content", "contact", "created_at")

    def short_content(self, obj):
        return obj.content[:30]
    short_content.short_description = "反馈内容"


@admin.register(UserNumber)
class UserNumberAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "lottery", "gen_type", "group_name", "created_at")
    list_filter = ("gen_type", "lottery")
    search_fields = ("user_id", "note")
```

- [ ] **Step 6: 加 FeedbackCreateView**

`lottery_backend/usernumber/views.py`：先在顶部 import 处把 `from usernumber.models import UserNumber` 改为 `from usernumber.models import UserNumber, Feedback`；然后在文件末尾追加：
```python
class FeedbackCreateView(APIView):
    """POST /api/user/feedback —— 提交用户反馈(匿名可提交)。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request) or ""
        content = (request.data.get("content") or "").strip()
        if not content:
            return Response(make_response(code=1, msg="请填写反馈内容"))
        if len(content) > 500:
            return Response(make_response(code=1, msg="反馈内容过长"))
        contact = (request.data.get("contact") or "").strip()
        rec = Feedback.objects.create(user_id=uid, content=content, contact=contact)
        return Response(make_response(data={"id": rec.id}))
```

- [ ] **Step 7: 注册路由**

`lottery_backend/usernumber/urls.py` 的 `urlpatterns` 里，在 `login` 行之后加一行：
```python
    path("feedback", views.FeedbackCreateView.as_view(), name="user-feedback"),
```

- [ ] **Step 8: 跑测试确认通过 + 全量回归**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_feedback.py -v && python -m pytest`
Expected: test_feedback 3 用例 PASS；全量无回归。

- [ ] **Step 9: 提交**

```bash
git add lottery_backend/usernumber/models.py lottery_backend/usernumber/admin.py lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/migrations/ lottery_backend/usernumber/tests/test_feedback.py
git commit -m "feat: 后端用户反馈Feedback模型+接口+admin"
```

---

### Task 2: 前端 改名 + 反馈页

**Files:**
- Modify: `lottery_frontend/src/utils/menu.js`（改名 + 加 feedback 项）
- Modify: `lottery_frontend/src/api/user.js`（加 `submitFeedback`）
- Create: `lottery_frontend/src/pages/feedback/index.vue`
- Modify: `lottery_frontend/src/pages.json`（注册反馈页）
- Test: `lottery_frontend/tests/user.test.js`（加 submitFeedback 用例）、`lottery_frontend/tests/menu.test.js`（计数 6→7 + feedback 项断言）

**Interfaces:**
- Consumes: `POST /api/user/feedback`（Task 1）。
- Produces: `submitFeedback({content, contact})` → request POST `/api/user/feedback`。

- [ ] **Step 1: 写失败测试（api + menu）**

`lottery_frontend/tests/user.test.js`：import 行追加 `submitFeedback`：
```js
import { login, createNumber, listNumbers, deleteNumber, checkNumber, generateNumbers, submitFeedback } from '../src/api/user.js'
```
在 `describe('user api', ...)` 内追加用例：
```js
  it('submitFeedback', async () => {
    await submitFeedback({ content: '建议', contact: 'wx123' })
    expect(request).toHaveBeenCalledWith('/api/user/feedback', { method: 'POST', data: { content: '建议', contact: 'wx123' } })
  })
```

`lottery_frontend/tests/menu.test.js`：把 `expect(HOME_MENU.length).toBe(6)` 改为 `toBe(7)`；在第二个 it（nav 断言）里追加：
```js
    expect(byKey.feedback.nav).toBe('navigateTo')
```

- [ ] **Step 2: 跑测试确认失败**

Run: `cd lottery_frontend && npm test -- user menu`
Expected: FAIL（`submitFeedback` 未导出；`feedback` 项不存在 / length 仍为 6）

- [ ] **Step 3: api 加 submitFeedback**

`lottery_frontend/src/api/user.js` 末尾追加：
```js
export function submitFeedback({ content, contact }) {
  return request('/api/user/feedback', { method: 'POST', data: { content, contact } })
}
```

- [ ] **Step 4: menu 改名 + 加 feedback 项**

`lottery_frontend/src/utils/menu.js`：
- 把 picker 行 `title: '选号记录'` 改为 `title: '选号'`（该行其余不变：`{ key: 'picker', title: '选号', icon: '✏️', path: '/pages/mine/picker', nav: 'switchTab' },`）。
- 在 `mine` 行之后、数组结束 `]` 之前追加一行：
```js
  { key: 'feedback', title: '我要反馈', icon: '💬', path: '/pages/feedback/index', nav: 'navigateTo' },
```

- [ ] **Step 5: 新建反馈页**

`lottery_frontend/src/pages/feedback/index.vue`：
```vue
<template>
  <view class="page">
    <TopBanner title="我要反馈" :back="true" />
    <view class="form">
      <textarea class="ta" v-model="content" placeholder="请写下你的意见或建议…" maxlength="500" />
      <input class="ipt" v-model="contact" placeholder="联系方式（可选）" />
      <button class="btn" :disabled="!content.trim() || submitting" @click="submit">提交</button>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import TopBanner from '../../components/TopBanner.vue'
import { submitFeedback } from '../../api/user.js'

const content = ref('')
const contact = ref('')
const submitting = ref(false)

async function submit() {
  if (!content.value.trim() || submitting.value) return
  submitting.value = true
  try {
    await submitFeedback({ content: content.value.trim(), contact: contact.value.trim() })
    uni.showToast({ title: '已收到，谢谢反馈', icon: 'success' })
    setTimeout(() => uni.navigateBack(), 600)
  } catch (e) {
    uni.showToast({ title: e.msg || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form { padding: 24rpx; }
.ta { background: #fff; border-radius: 12rpx; padding: 20rpx; width: 100%; height: 240rpx; font-size: 28rpx; box-sizing: border-box; }
.ipt { background: #fff; border-radius: 12rpx; padding: 20rpx; margin-top: 20rpx; font-size: 28rpx; }
.btn { background: #e53935; color: #fff; font-size: 30rpx; margin-top: 32rpx; }
</style>
```

- [ ] **Step 6: pages.json 注册**

`lottery_frontend/src/pages.json` 的 `pages` 数组里，在 `pages/legal/doc` 行之后加一条（注意给 legal/doc 行末补逗号，保持 JSON 合法）：
```json
    { "path": "pages/feedback/index", "style": { "navigationBarTitleText": "我要反馈" } }
```

- [ ] **Step 7: 跑测试 + build**

Run: `cd lottery_frontend && npm test && npm run build:h5`
Expected: 全绿；`Build complete.`

- [ ] **Step 8: 提交**

```bash
git add lottery_frontend/src/utils/menu.js lottery_frontend/src/api/user.js lottery_frontend/src/pages/feedback/index.vue lottery_frontend/src/pages.json lottery_frontend/tests/user.test.js lottery_frontend/tests/menu.test.js
git commit -m "feat: 选号记录改名为选号 + 我要反馈页与入口"
```

---

## 计划自检

**1. Spec 覆盖：**
- IA 改名（spec §1）→ Task 2 Step 4 ✓
- Feedback 模型（spec §2.1）→ Task 1 Step 3 ✓
- admin（spec §2.2）→ Task 1 Step 5 ✓
- 接口 + 校验（spec §2.3）→ Task 1 Step 6/7 ✓
- 前端反馈页 + 入口 + api + pages.json（spec §3）→ Task 2 Step 3-6 ✓
- 错误处理（spec §4）→ Task 1 校验分支 + Task 2 toast ✓
- 测试（spec §5）→ Task 1 Step 1（3 后端用例）、Task 2 Step 1（api + menu）✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码与确切命令。

**3. 类型/签名一致性：** `Feedback` 字段 user_id/content/contact/created_at 在模型、admin、view、测试一致；`/api/user/feedback` 在 url、view、前端 api、测试一致；`submitFeedback({content,contact})` 在 api、测试、反馈页一致；`HOME_MENU` 加项后 length=7 与 menu.test 一致。
