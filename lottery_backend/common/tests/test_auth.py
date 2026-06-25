import pytest
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from common import auth


def _request_with_session():
    req = RequestFactory().get("/")
    SessionMiddleware(lambda r: None).process_request(req)
    return req


def test_hash_user_id_deterministic_and_not_raw():
    h1 = auth.hash_user_id("openid_xyz")
    h2 = auth.hash_user_id("openid_xyz")
    assert h1 == h2
    assert h1 != "openid_xyz"
    assert len(h1) == 64


def test_mock_returns_code_as_openid():
    assert auth.mock_code_to_openid("openid_abc") == "openid_abc"
    assert auth.mock_code_to_openid("") is None


def test_selector_uses_mock_without_credentials(settings):
    settings.WECHAT_APPID = ""
    settings.WECHAT_SECRET = ""
    assert auth.code_to_openid("openid_abc") == "openid_abc"


def test_selector_uses_wechat_with_credentials(settings, monkeypatch):
    settings.WECHAT_APPID = "wxappid"
    settings.WECHAT_SECRET = "wxsecret"
    monkeypatch.setattr(auth, "wechat_code_to_openid", lambda code: f"wx::{code}")
    assert auth.code_to_openid("jscode") == "wx::jscode"


def test_session_roundtrip():
    req = _request_with_session()
    uid = auth.set_user_session(req, "openid_abc")
    assert uid == auth.hash_user_id("openid_abc")
    assert auth.current_user_id(req) == uid


def test_current_user_id_none_when_not_logged_in():
    req = _request_with_session()
    assert auth.current_user_id(req) is None


class _Resp:
    def __init__(self, payload):
        import json as _json
        self._p = _json.dumps(payload).encode()

    def read(self):
        return self._p

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_session_parses_openid_unionid(monkeypatch):
    monkeypatch.setattr(auth.urllib.request, "urlopen", lambda url, timeout=5: _Resp({"openid": "o1", "unionid": "u1"}))
    assert auth.wechat_code_to_session("c") == {"openid": "o1", "unionid": "u1"}


def test_session_unionid_absent_is_blank(monkeypatch):
    monkeypatch.setattr(auth.urllib.request, "urlopen", lambda url, timeout=5: _Resp({"openid": "o2"}))
    assert auth.wechat_code_to_session("c") == {"openid": "o2", "unionid": ""}


def test_session_no_openid_returns_none(monkeypatch):
    monkeypatch.setattr(auth.urllib.request, "urlopen", lambda url, timeout=5: _Resp({"errcode": 40029}))
    assert auth.wechat_code_to_session("c") is None


def test_wechat_code_to_openid_reuses_session(monkeypatch):
    monkeypatch.setattr(auth, "wechat_code_to_session", lambda code: {"openid": "ox", "unionid": ""})
    assert auth.wechat_code_to_openid("c") == "ox"
    monkeypatch.setattr(auth, "wechat_code_to_session", lambda code: None)
    assert auth.wechat_code_to_openid("c") is None
