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
    monkeypatch.setattr("usernumber.views.wechat_code_to_session",
                        lambda code: {"openid": "wx-openid-9", "unionid": ""})
    APIClient().post("/api/user/login/wechat", {"code": "c"}, format="json")
    assert AppUser.objects.filter(openid="wx-openid-9").count() == 1
