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
