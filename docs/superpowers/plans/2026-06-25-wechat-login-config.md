# 微信登录配置诊断 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 微信登录未配置 AppID/Secret 时返回明确「微信登录未配置」，便于自查。

**Architecture:** WechatLoginView 在 code2session 前校验 settings 配置。

**Tech Stack:** Django + DRF + pytest（pytest-django 的 `settings` fixture 注入配置）。

## Global Constraints

- 未配置 → `code=1, msg="微信登录未配置"`；配置齐全后保留原流程（无效 code → `msg="微信登录失败"`）。
- 匿名登录 LoginView 不变。
- 日志用 logging 不用 print。

---

### Task 1: WechatLoginView 配置校验

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（顶部 import settings；WechatLoginView 增校验）
- Test: `lottery_backend/usernumber/tests/test_wechat_login.py`

- [ ] **Step 1: 更新/新增测试**

把 `test_wechat_login.py` 改为（success/failure 用 `settings` fixture 注入配置；新增未配置用例）：

```python
from rest_framework.test import APIClient


def test_wechat_login_success(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"
    settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_openid", lambda code: "wx-openid-123")
    resp = APIClient().post("/api/user/login/wechat", {"code": "wxcode"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["logged_in"] is True
    assert body["data"]["token"]


def test_wechat_login_failure(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"
    settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_openid", lambda code: None)
    body = APIClient().post("/api/user/login/wechat", {"code": "badcode"}, format="json").json()
    assert body["code"] == 1
    assert body["msg"] == "微信登录失败"


def test_wechat_login_missing_code(db):
    assert APIClient().post("/api/user/login/wechat", {}, format="json").json()["code"] == 1


def test_wechat_login_not_configured(db, settings):
    settings.WECHAT_APPID = ""
    settings.WECHAT_SECRET = ""
    body = APIClient().post("/api/user/login/wechat", {"code": "wxcode"}, format="json").json()
    assert body["code"] == 1
    assert body["msg"] == "微信登录未配置"
```

- [ ] **Step 2: 运行确认未配置用例失败**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_wechat_login.py::test_wechat_login_not_configured -q`
Expected: FAIL（现返回「微信登录失败」而非「微信登录未配置」）。

- [ ] **Step 3: 实现配置校验**

`usernumber/views.py` 顶部加 `from django.conf import settings`；WechatLoginView.post 改为：

```python
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(make_response(code=1, msg="缺少 code"))
        if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
            return Response(make_response(code=1, msg="微信登录未配置",
                                          error="后端缺少 WECHAT_APPID/WECHAT_SECRET"))
        openid = wechat_code_to_openid(code)
        if not openid:
            return Response(make_response(code=1, msg="微信登录失败", error="code 无效或已过期"))
        uid = set_user_session(request, openid)
        return Response(make_response(data={"logged_in": True, "token": uid}))
```

- [ ] **Step 4: 运行确认全绿**

Run: `cd lottery_backend && python -m pytest usernumber/tests/test_wechat_login.py -q`
Expected: PASS（4 个用例）。

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/tests/test_wechat_login.py
git commit -m "feat(login): 微信未配置 AppID/Secret 时返回明确诊断(note33)"
```

---

## Self-Review

- note 33 → 未配置明确提示 ✓；原配置路径行为保留（success/failure 用 settings fixture 注入配置后仍按原逻辑）。
- 无 placeholder；LoginView 未动。
