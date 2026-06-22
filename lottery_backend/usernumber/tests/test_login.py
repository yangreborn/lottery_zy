import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


def test_login_success_sets_session(db, api_client):
    resp = api_client.post("/api/user/login", {"code": "openid_abc"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["logged_in"] is True
    assert api_client.session.get("uid")


def test_login_missing_code(db, api_client):
    resp = api_client.post("/api/user/login", {}, format="json")
    assert resp.status_code == 200
    assert resp.json()["code"] == 1
