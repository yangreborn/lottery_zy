from rest_framework.test import APIClient
from usernumber.models import AppUser


def test_wechat_login_success(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"
    settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_session",
                        lambda code: {"openid": "wx-openid-123", "unionid": "uni-1"})
    c = APIClient()
    body = c.post("/api/user/login/wechat", {"code": "wxcode"}, format="json").json()
    assert body["code"] == 0
    assert body["data"]["logged_in"] is True
    assert len(body["data"]["token"]) == 64
    assert c.session.get("uid")
    assert AppUser.objects.get(openid="wx-openid-123").unionid == "uni-1"


def test_wechat_login_no_unionid_blank(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"
    settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_session",
                        lambda code: {"openid": "wx-openid-x", "unionid": ""})
    APIClient().post("/api/user/login/wechat", {"code": "c"}, format="json")
    assert AppUser.objects.get(openid="wx-openid-x").unionid == ""


def test_wechat_login_failure(db, monkeypatch, settings):
    settings.WECHAT_APPID = "appid"
    settings.WECHAT_SECRET = "secret"
    monkeypatch.setattr("usernumber.views.wechat_code_to_session", lambda code: None)
    body = APIClient().post("/api/user/login/wechat", {"code": "bad"}, format="json").json()
    assert body["code"] == 1
    assert body["msg"] == "微信登录失败"
    assert body["error"]


def test_wechat_login_missing_code(db):
    assert APIClient().post("/api/user/login/wechat", {}, format="json").json()["code"] == 1


def test_wechat_login_not_configured(db, settings):
    settings.WECHAT_APPID = ""
    settings.WECHAT_SECRET = ""
    body = APIClient().post("/api/user/login/wechat", {"code": "wxcode"}, format="json").json()
    assert body["code"] == 1
    assert body["msg"] == "微信登录未配置"


def test_anonymous_login_uses_mock(db):
    body = APIClient().post("/api/user/login", {"code": "dev-xyz"}, format="json").json()
    assert body["code"] == 0
    assert len(body["data"]["token"]) == 64


def test_wechat_mock_login_bypasses_code2session(db, settings):
    # 假微信登录开关开启：无需 appid/secret，直接返回固定测试身份
    settings.WECHAT_MOCK_LOGIN = True
    settings.WECHAT_MOCK_OPENID = "mock-wechat-user"
    settings.WECHAT_APPID = ""
    settings.WECHAT_SECRET = ""
    body = APIClient().post("/api/user/login/wechat", {"code": "anything"}, format="json").json()
    assert body["code"] == 0
    assert body["data"]["logged_in"] is True
    assert AppUser.objects.filter(openid="mock-wechat-user").exists()


def test_wechat_mock_login_stable_identity(db, settings):
    # 每次登录都是同一个测试身份：token 稳定，昵称等可持久
    settings.WECHAT_MOCK_LOGIN = True
    settings.WECHAT_MOCK_OPENID = "mock-wechat-user"
    c = APIClient()
    t1 = c.post("/api/user/login/wechat", {"code": "code-1"}, format="json").json()["data"]["token"]
    t2 = c.post("/api/user/login/wechat", {"code": "code-2"}, format="json").json()["data"]["token"]
    assert t1 == t2
    assert AppUser.objects.filter(openid="mock-wechat-user").count() == 1
