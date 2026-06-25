# 微信 unionid/昵称/授权 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Checkbox steps.

**Goal:** 微信登录落 unionid（有则存），授权弹窗取微信昵称写档案。

**Architecture:** AppUser 加 unionid；auth 加 wechat_code_to_session；WechatLoginView 存 unionid；前端 getUserProfile→setProfile。

**Tech Stack:** Django+DRF+pytest；uni-app Vue3。

## Global Constraints

- unionid 非唯一、可空（开放平台未绑定则空）。
- `wechat_code_to_session(code)`→`{openid, unionid}`|None；保留 `wechat_code_to_openid`（code_to_openid 仍用）。
- 昵称复用 `POST /api/user/profile`（不新开接口）；getUserProfile 仅微信端可用，H5 跳过。
- 日志 logging；不执行 migrate（仅 makemigrations）。

---

### Task 1: AppUser.unionid + 迁移

**Files:** usernumber/models.py、migrations/0006_*、tests/test_appuser.py

- [ ] **Step 1:** test_appuser.py 加：

```python
@pytest.mark.django_db
def test_appuser_unionid_default_blank():
    u = get_or_create_app_user("hashu", "openidu")
    assert u.unionid == ""
```

- [ ] **Step 2:** `python -m pytest usernumber/tests/test_appuser.py::test_appuser_unionid_default_blank -q` 失败。
- [ ] **Step 3:** AppUser 增字段（openid 之后）：

```python
    unionid = models.CharField("unionid", max_length=128, blank=True, default="", db_index=True)
```

- [ ] **Step 4:** `python manage.py makemigrations usernumber`（生成 0006）。
- [ ] **Step 5:** 测试通过；提交 `feat(user): AppUser 增 unionid 字段`。

### Task 2: wechat_code_to_session

**Files:** common/auth.py、common/tests/test_auth.py

- [ ] **Step 1:** test_auth.py 加（monkeypatch urlopen）：

```python
import json, io
from common import auth

class _Resp:
    def __init__(self, payload): self._p = json.dumps(payload).encode()
    def read(self): return self._p
    def __enter__(self): return self
    def __exit__(self, *a): return False

def test_session_parses_openid_unionid(monkeypatch):
    monkeypatch.setattr(auth.settings, "WECHAT_APPID", "a", raising=False)
    monkeypatch.setattr(auth.settings, "WECHAT_SECRET", "s", raising=False)
    monkeypatch.setattr(auth.urllib.request, "urlopen", lambda url, timeout=5: _Resp({"openid": "o1", "unionid": "u1"}))
    assert auth.wechat_code_to_session("c") == {"openid": "o1", "unionid": "u1"}

def test_session_unionid_absent_is_blank(monkeypatch):
    monkeypatch.setattr(auth.urllib.request, "urlopen", lambda url, timeout=5: _Resp({"openid": "o2"}))
    assert auth.wechat_code_to_session("c") == {"openid": "o2", "unionid": ""}

def test_session_no_openid_returns_none(monkeypatch):
    monkeypatch.setattr(auth.urllib.request, "urlopen", lambda url, timeout=5: _Resp({"errcode": 40029}))
    assert auth.wechat_code_to_session("c") is None
```

- [ ] **Step 2:** 运行失败。
- [ ] **Step 3:** common/auth.py 增 `wechat_code_to_session` 并让 `wechat_code_to_openid` 复用：

```python
def wechat_code_to_session(code):
    """真实微信 code2session，返回 {openid, unionid}；失败返回 None。"""
    params = urllib.parse.urlencode({
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    })
    url = f"{WECHAT_CODE2SESSION_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        logger.error("微信 code2session 请求失败", exc_info=True)
        return None
    openid = data.get("openid")
    if not openid:
        logger.warning("微信 code2session 未返回 openid: %s", data)
        return None
    return {"openid": openid, "unionid": data.get("unionid", "") or ""}


def wechat_code_to_openid(code):
    """真实微信 code2session，换取 openid；失败返回 None。"""
    session = wechat_code_to_session(code)
    return session["openid"] if session else None
```

（删除原 `wechat_code_to_openid` 旧实现体，替换为上面复用版；保留 `code_to_openid`/`mock_code_to_openid` 不变。）

- [ ] **Step 4:** `python -m pytest common/tests/test_auth.py -q` 全绿。
- [ ] **Step 5:** 提交 `feat(auth): wechat_code_to_session 解析 openid+unionid`。

### Task 3: WechatLoginView 存 unionid

**Files:** usernumber/views.py、tests/test_wechat_login.py、tests/test_appuser_register.py

- [ ] **Step 1:** 更新 test_wechat_login.py：把 monkeypatch 目标由 `wechat_code_to_openid` 改 `wechat_code_to_session` 返回 dict；新增 unionid 落库断言：

```python
def test_wechat_login_success(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"; settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_session", lambda code: {"openid": "wx-openid-123", "unionid": "uni-1"})
    c = APIClient()
    body = c.post("/api/user/login/wechat", {"code": "wxcode"}, format="json").json()
    assert body["code"] == 0 and len(body["data"]["token"]) == 64
    from usernumber.models import AppUser
    assert AppUser.objects.get(openid="wx-openid-123").unionid == "uni-1"

def test_wechat_login_failure(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"; settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_session", lambda code: None)
    body = APIClient().post("/api/user/login/wechat", {"code": "bad"}, format="json").json()
    assert body["code"] == 1 and body["msg"] == "微信登录失败"

def test_wechat_login_missing_code(db):
    assert APIClient().post("/api/user/login/wechat", {}, format="json").json()["code"] == 1

def test_wechat_login_not_configured(db, settings):
    settings.WECHAT_APPID = ""; settings.WECHAT_SECRET = ""
    body = APIClient().post("/api/user/login/wechat", {"code": "x"}, format="json").json()
    assert body["code"] == 1 and body["msg"] == "微信登录未配置"

def test_anonymous_login_uses_mock(db):
    body = APIClient().post("/api/user/login", {"code": "dev-xyz"}, format="json").json()
    assert body["code"] == 0 and len(body["data"]["token"]) == 64
```

test_appuser_register.py 的 `test_wechat_login_registers_appuser` 改 monkeypatch `wechat_code_to_session` 返回 `{"openid":"wx-openid-9","unionid":""}`。

- [ ] **Step 2:** 运行失败（views 仍用 openid 版）。
- [ ] **Step 3:** views.py：import 改 `wechat_code_to_session`；WechatLoginView.post：

```python
        session = wechat_code_to_session(code)
        if not session:
            return Response(make_response(code=1, msg="微信登录失败", error="code 无效或已过期"))
        openid = session["openid"]
        uid = set_user_session(request, openid)
        user = get_or_create_app_user(uid, openid)
        unionid = session.get("unionid") or ""
        if unionid and user.unionid != unionid:
            user.unionid = unionid
            user.save(update_fields=["unionid", "updated_at"])
        return Response(make_response(data={"logged_in": True, "token": uid}))
```

顶部 import：`from common.auth import mock_code_to_openid, wechat_code_to_session, set_user_session, current_user_id`（去掉 wechat_code_to_openid 若不再用；LoginView 用 mock）。

- [ ] **Step 4:** `python -m pytest usernumber/tests/test_wechat_login.py usernumber/tests/test_appuser_register.py -q` 全绿。
- [ ] **Step 5:** 提交 `feat(login): 微信登录落库 unionid(note44)`。

### Task 4: admin 显示 unionid

**Files:** usernumber/admin.py

- [ ] **Step 1:** AppUserAdmin list_display 增 unionid，readonly 增 unionid：

```python
    list_display = ("id", "nickname", "short_id", "openid", "unionid", "created_at")
    readonly_fields = ("user_id", "openid", "unionid", "created_at", "updated_at")
```

- [ ] **Step 2:** `python manage.py check` 通过；提交 `feat(admin): 用户档案显示 unionid`。

### Task 5: 前端授权取昵称

**Files:** src/pages/mine/index.vue

- [ ] **Step 1:** `doWechatLogin` 改为先 getUserProfile 取昵称再登录：

```js
function doWechatLogin() {
  uni.getUserProfile({
    desc: '用于完善个人资料',
    success: (p) => finishWechatLogin(p.userInfo && p.userInfo.nickName),
    fail: () => finishWechatLogin(''),
  })
}

function finishWechatLogin(nickName) {
  uni.login({
    success: async (r) => {
      if (!r.code) { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }); return }
      try {
        const res = await wechatLogin(r.code)
        setToken(res.token, true)
        if (nickName) { try { await setProfile(nickName) } catch (e) { /* 昵称写入失败不阻塞登录 */ } }
        uni.showToast({ title: '登录成功', icon: 'success' })
        loadProfile()
      } catch (e) {
        uni.showToast({ title: e.msg || '登录失败', icon: 'none' })
      }
    },
    fail: () => { uni.showToast({ title: '请在微信小程序中使用', icon: 'none' }) },
  })
}
```

- [ ] **Step 2:** `npm test` 全绿（mine/index 无单测，回归）；提交 `feat(user): 微信登录授权获取昵称(note44)`。

---

## Self-Review

- note44 unionid→Task1-3；昵称授权→Task5；admin→Task4。
- 类型一致：`wechat_code_to_session`→{openid,unionid} 在 auth 定义、views 消费、测试 monkeypatch 一致；AppUser.unionid 字段在 model/admin/view 一致。
- 迁移 0006 依赖 0005；不执行 migrate（生成文件，应用我可按授权自行 migrate）。
