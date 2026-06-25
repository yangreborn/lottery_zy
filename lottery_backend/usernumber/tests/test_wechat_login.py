from rest_framework.test import APIClient


def test_wechat_login_success(db, monkeypatch):
    monkeypatch.setattr("usernumber.views.wechat_code_to_openid", lambda code: "wx-openid-123")
    c = APIClient()
    resp = c.post("/api/user/login/wechat", {"code": "wxcode"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["logged_in"] is True
    assert len(body["data"]["token"]) == 64
    assert c.session.get("uid")


def test_wechat_login_failure(db, monkeypatch):
    monkeypatch.setattr("usernumber.views.wechat_code_to_openid", lambda code: None)
    resp = APIClient().post("/api/user/login/wechat", {"code": "badcode"}, format="json")
    assert resp.json()["code"] == 1


def test_wechat_login_missing_code(db):
    resp = APIClient().post("/api/user/login/wechat", {}, format="json")
    assert resp.json()["code"] == 1


def test_anonymous_login_uses_mock(db):
    resp = APIClient().post("/api/user/login", {"code": "dev-xyz"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["token"]) == 64
