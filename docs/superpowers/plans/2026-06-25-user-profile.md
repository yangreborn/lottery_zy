# 用户体系 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 建用户档案(openid+昵称)，登录时注册，后台用短 id+昵称区分用户，前端可设昵称。

**Architecture:** 新 AppUser 模型；登录视图注册；ProfileView 读写昵称；admin 短哈希展示；hub 加昵称 UI。

**Tech Stack:** Django 5 + DRF + pytest（后端）；uni-app Vue3 + vitest（前端）。

## Global Constraints

- `user_id` = openid 的 sha256 hash（对外标识）；AppUser 存 openid + nickname；记录表仍存 user_id 字符串不动。
- 后台短标识 = AppUser 自增 id；记录 admin 列表显示 `user_id[:8]`，完整 user_id 仍可搜。
- 昵称 ≤30 字符、去空格；接口未登录 code=1。
- 日志用 logging 不用 print；中文。
- 不执行 migrate（仅 makemigrations 生成文件，应用由用户做）。

---

### Task 1: AppUser 模型 + 迁移 + 辅助函数

**Files:**
- Modify: `lottery_backend/usernumber/models.py`
- Create: `lottery_backend/usernumber/migrations/0005_appuser.py`（makemigrations 生成）
- Test: `lottery_backend/usernumber/tests/test_appuser.py`

- [ ] **Step 1: 写失败测试 `tests/test_appuser.py`**

```python
import pytest
from usernumber.models import AppUser, get_or_create_app_user


@pytest.mark.django_db
def test_get_or_create_app_user_idempotent():
    u1 = get_or_create_app_user("hash123", "openid-abc")
    u2 = get_or_create_app_user("hash123", "openid-abc")
    assert u1.id == u2.id
    assert AppUser.objects.count() == 1
    assert u1.openid == "openid-abc"


@pytest.mark.django_db
def test_short_id_and_str():
    u = get_or_create_app_user("abcdef0123456789", "openid-x")
    u.nickname = "小明"
    u.save()
    assert u.short_id == "abcdef01"
    assert str(u) == f"#{u.id} 小明"
```

- [ ] **Step 2: 运行确认失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_appuser.py -q`
Expected: FAIL（AppUser 不存在）。

- [ ] **Step 3: 加 AppUser 模型与辅助（models.py 末尾）**

```python
class AppUser(models.Model):
    """登录用户档案。user_id 是 openid 的 hash(对外标识)，openid 仅后台留存。"""
    user_id = models.CharField("用户哈希", max_length=64, unique=True, db_index=True)
    openid = models.CharField("openid", max_length=128, unique=True)
    nickname = models.CharField("昵称", max_length=30, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户"
        ordering = ["-created_at"]

    @property
    def short_id(self):
        return self.user_id[:8]

    def __str__(self):
        return f"#{self.id} {self.nickname or self.short_id}"


def get_or_create_app_user(user_id, openid):
    user, _ = AppUser.objects.get_or_create(user_id=user_id, defaults={"openid": openid})
    return user
```

- [ ] **Step 4: 生成迁移**

Run: `cd lottery_backend && python manage.py makemigrations usernumber`
Expected: 生成 `0005_appuser.py`。

- [ ] **Step 5: 运行确认通过**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_appuser.py -q`
Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/models.py lottery_backend/usernumber/migrations/0005_appuser.py lottery_backend/usernumber/tests/test_appuser.py
git commit -m "feat(user): 新增 AppUser 档案模型(openid/昵称/short_id)"
```

---

### Task 2: 登录时注册 AppUser

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（LoginView、WechatLoginView）
- Test: `lottery_backend/usernumber/tests/test_appuser_register.py`

- [ ] **Step 1: 写失败测试 `tests/test_appuser_register.py`**

```python
from rest_framework.test import APIClient
from usernumber.models import AppUser


def test_anonymous_login_registers_appuser(db):
    APIClient().post("/api/user/login", {"code": "dev-xyz"}, format="json")
    assert AppUser.objects.filter(openid="dev-xyz").count() == 1


def test_repeat_login_no_duplicate(db):
    APIClient().post("/api/user/login", {"code": "dev-xyz"}, format="json")
    APIClient().post("/api/user/login", {"code": "dev-xyz"}, format="json")
    assert AppUser.objects.filter(openid="dev-xyz").count() == 1


def test_wechat_login_registers_appuser(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"
    settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_openid", lambda code: "wx-openid-9")
    APIClient().post("/api/user/login/wechat", {"code": "c"}, format="json")
    assert AppUser.objects.filter(openid="wx-openid-9").count() == 1
```

- [ ] **Step 2: 运行确认失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_appuser_register.py -q`
Expected: FAIL（未注册）。

- [ ] **Step 3: 在两个登录视图注册**

`usernumber/views.py` 顶部 import 加入 `get_or_create_app_user`：

```python
from usernumber.models import UserNumber, Feedback, PurchaseRecord, get_or_create_app_user
```

`LoginView.post` 的成功分支改为：

```python
        uid = set_user_session(request, openid)
        get_or_create_app_user(uid, openid)
        return Response(make_response(data={"logged_in": True, "token": uid}))
```

`WechatLoginView.post` 的成功分支改为：

```python
        uid = set_user_session(request, openid)
        get_or_create_app_user(uid, openid)
        return Response(make_response(data={"logged_in": True, "token": uid}))
```

- [ ] **Step 4: 运行确认通过**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_appuser_register.py usernumber/tests/test_wechat_login.py -q`
Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/tests/test_appuser_register.py
git commit -m "feat(user): 登录(匿名/微信)时注册 AppUser 并落库 openid"
```

---

### Task 3: ProfileView 昵称读写

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（新增 ProfileView）
- Modify: `lottery_backend/usernumber/urls.py`
- Test: `lottery_backend/usernumber/tests/test_profile.py`

- [ ] **Step 1: 写失败测试 `tests/test_profile.py`**

```python
from rest_framework.test import APIClient


def _login(c):
    c.post("/api/user/login", {"code": "dev-prof"}, format="json")


def test_profile_requires_login(db):
    assert APIClient().get("/api/user/profile").json()["code"] == 1


def test_set_and_get_nickname(db):
    c = APIClient()
    _login(c)
    r = c.post("/api/user/profile", {"nickname": " 小红 "}, format="json").json()
    assert r["code"] == 0
    assert r["data"]["nickname"] == "小红"
    g = c.get("/api/user/profile").json()
    assert g["data"]["nickname"] == "小红"
    assert len(g["data"]["short_id"]) == 8


def test_nickname_too_long(db):
    c = APIClient()
    _login(c)
    r = c.post("/api/user/profile", {"nickname": "x" * 31}, format="json").json()
    assert r["code"] == 1
```

- [ ] **Step 2: 运行确认失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_profile.py -q`
Expected: FAIL（无 profile 路由）。

- [ ] **Step 3: 新增 ProfileView（views.py 末尾）**

```python
class ProfileView(APIView):
    """GET/POST /api/user/profile —— 读取/设置当前用户昵称。"""
    authentication_classes = []

    def get(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        user = AppUser.objects.filter(user_id=uid).first()
        nickname = user.nickname if user else ""
        return Response(make_response(data={"nickname": nickname, "short_id": uid[:8]}))

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        nickname = (request.data.get("nickname") or "").strip()
        if len(nickname) > 30:
            return Response(make_response(code=1, msg="昵称过长", error="昵称不超过 30 字符"))
        user = get_or_create_app_user(uid, uid)
        user.nickname = nickname
        user.save(update_fields=["nickname", "updated_at"])
        return Response(make_response(data={"nickname": user.nickname, "short_id": user.short_id}))
```

并把顶部 import 补上 `AppUser`：

```python
from usernumber.models import UserNumber, Feedback, PurchaseRecord, AppUser, get_or_create_app_user
```

- [ ] **Step 4: 注册路由 urls.py**

在 `login/wechat` 行后加：

```python
    path("profile", views.ProfileView.as_view(), name="user-profile"),
```

- [ ] **Step 5: 运行确认通过**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_profile.py -q`
Expected: PASS。

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_profile.py
git commit -m "feat(user): ProfileView 读写昵称(/api/user/profile)"
```

---

### Task 4: Admin 可区分

**Files:**
- Modify: `lottery_backend/usernumber/admin.py`

- [ ] **Step 1: 注册 AppUser + 记录表显示短哈希**

整文件改为：

```python
from django.contrib import admin

from usernumber.models import UserNumber, Feedback, PurchaseRecord, AppUser


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("id", "nickname", "short_id", "openid", "created_at")
    search_fields = ("nickname", "user_id", "openid")
    readonly_fields = ("user_id", "openid", "created_at", "updated_at")

    def short_id(self, obj):
        return obj.short_id
    short_id.short_description = "短ID"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "short_content", "contact", "short_uid", "created_at")
    search_fields = ("content", "contact", "user_id")
    readonly_fields = ("user_id", "content", "contact", "created_at")

    def short_content(self, obj):
        return obj.content[:30]
    short_content.short_description = "反馈内容"

    def short_uid(self, obj):
        return obj.user_id[:8] or "匿名"
    short_uid.short_description = "用户"


@admin.register(UserNumber)
class UserNumberAdmin(admin.ModelAdmin):
    list_display = ("id", "short_uid", "lottery", "gen_type", "group_name", "created_at")
    list_filter = ("gen_type", "lottery")
    search_fields = ("user_id", "note")

    def short_uid(self, obj):
        return obj.user_id[:8]
    short_uid.short_description = "用户"


@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "short_uid", "lottery", "issue", "bet_count", "purchase_date", "created_at")
    list_filter = ("lottery",)
    search_fields = ("user_id", "issue")

    def short_uid(self, obj):
        return obj.user_id[:8]
    short_uid.short_description = "用户"
```

- [ ] **Step 2: 冒烟校验**

Run: `cd lottery_backend && python manage.py check`
Expected: System check identified no issues。

- [ ] **Step 3: 提交**

```bash
git add lottery_backend/usernumber/admin.py
git commit -m "feat(admin): 用户档案后台 + 记录表显示短哈希(note34)"
```

---

### Task 5: 前端昵称 UI

**Files:**
- Modify: `lottery_frontend/src/api/user.js`
- Modify: `lottery_frontend/src/pages/mine/index.vue`
- Test: `lottery_frontend/tests/user_profile.test.js`

- [ ] **Step 1: 写失败测试 `tests/user_profile.test.js`**

```js
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../src/api/request.js', () => ({ request: vi.fn(() => Promise.resolve({})) }))
vi.mock('../src/utils/device.js', () => ({ getOrCreateDeviceCode: () => 'dev' }))
import { request } from '../src/api/request.js'
import { getProfile, setProfile } from '../src/api/user.js'

describe('profile api', () => {
  beforeEach(() => { request.mockClear() })

  it('getProfile 走 GET /api/user/profile', async () => {
    await getProfile()
    expect(request).toHaveBeenCalledWith('/api/user/profile')
  })

  it('setProfile 走 POST 带 nickname', async () => {
    await setProfile('小红')
    expect(request).toHaveBeenCalledWith('/api/user/profile', { method: 'POST', data: { nickname: '小红' } })
  })
})
```

- [ ] **Step 2: 运行确认失败**

Run: `cd lottery_frontend && npm test -- user_profile`
Expected: FAIL（函数不存在）。

- [ ] **Step 3: api/user.js 加 getProfile/setProfile**

在文件末尾追加：

```js
export function getProfile() {
  return request('/api/user/profile')
}

export function setProfile(nickname) {
  return request('/api/user/profile', { method: 'POST', data: { nickname } })
}
```

- [ ] **Step 4: 运行确认通过**

Run: `cd lottery_frontend && npm test -- user_profile`
Expected: PASS。

- [ ] **Step 5: hub 加昵称行**

`src/pages/mine/index.vue`：authbar 下方、menu 上方插入昵称行；脚本引入 profile api 并在 onShow 拉取、提供编辑。

模板 authbar 之后插入：

```html
    <view class="profile" @click="editNickname">
      <text class="plabel">昵称</text>
      <text class="pval">{{ nickname || '点击设置' }}</text>
      <text class="arr">›</text>
    </view>
```

脚本改为：

```js
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopBanner from '../../components/TopBanner.vue'
import { ensureLogin, wechatLogin, getProfile, setProfile } from '../../api/user.js'
import { authState, setToken } from '../../store/auth.js'
import { reportAccess } from '../../utils/report.js'

const auth = authState
const nickname = ref('')
function go(url) { uni.navigateTo({ url }) }

async function loadProfile() {
  try { const p = await getProfile(); nickname.value = p.nickname || '' } catch (e) { /* 容错 */ }
}

function editNickname() {
  uni.showModal({
    title: '设置昵称',
    editable: true,
    placeholderText: '输入昵称(≤30字)',
    content: nickname.value,
    success: async (res) => {
      if (!res.confirm) return
      try {
        const p = await setProfile((res.content || '').trim())
        nickname.value = p.nickname || ''
        uni.showToast({ title: '已保存', icon: 'success' })
      } catch (e) {
        uni.showToast({ title: e.msg || '保存失败', icon: 'none' })
      }
    },
  })
}

function doWechatLogin() {
  uni.login({
    success: async (r) => {
      if (!r.code) { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }); return }
      try {
        const res = await wechatLogin(r.code)
        setToken(res.token, true)
        uni.showToast({ title: '登录成功', icon: 'success' })
        loadProfile()
      } catch (e) {
        uni.showToast({ title: e.msg || '登录失败', icon: 'none' })
      }
    },
    fail: () => { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }) },
  })
}

function doLogout() {
  setToken('', false)
  uni.showToast({ title: '已退出', icon: 'none' })
  loadProfile()
}

onShow(async () => {
  reportAccess('mine/index', {})
  await ensureLogin()
  loadProfile()
})
```

样式追加：

```css
.profile { display: flex; align-items: center; margin: 0 20rpx 12rpx; background: #fff; border-radius: 16rpx; padding: 28rpx; }
.plabel { color: #888; font-size: 30rpx; margin-right: 24rpx; }
.pval { flex: 1; color: #333; font-size: 30rpx; }
```

- [ ] **Step 6: 全量前端测试**

Run: `cd lottery_frontend && npm test`
Expected: PASS。

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/api/user.js lottery_frontend/src/pages/mine/index.vue lottery_frontend/tests/user_profile.test.js
git commit -m "feat(user): 我的页支持设置昵称"
```

---

## Self-Review

**Spec coverage:**
- note 34（后台区分）→ AppUser.id 短标识 + admin short_id/short_uid（Task 1/4）✓
- note 35（记录 openid + 昵称）→ AppUser.openid 登录注册（Task 2）+ ProfileView 昵称（Task 3）+ 前端 UI（Task 5）✓

**Placeholder scan:** 无 TBD/TODO；代码完整。

**Type consistency:** `get_or_create_app_user(user_id, openid)` 在 models 定义、views(Task2/3) 消费一致；`AppUser.short_id` 属性在 admin/ProfileView 一致；`/api/user/profile` GET/POST 与前端 `getProfile`/`setProfile` 一致；migration 0005 依赖 0004。

**注意：** 不执行 migrate；测试用 test DB（pytest-django 自动建表），依赖 0005 迁移文件已由 Task1 Step4 生成。
