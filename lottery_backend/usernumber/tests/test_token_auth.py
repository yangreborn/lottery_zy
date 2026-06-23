import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_login_returns_token(db):
    resp = APIClient().post("/api/user/login", {"code": "dev-abc"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["logged_in"] is True
    assert isinstance(body["data"]["token"], str) and len(body["data"]["token"]) == 64


def test_header_token_identifies_user(ssq):
    # 无 session，仅靠 X-User-Id 头识别身份
    c = APIClient()
    c.credentials(HTTP_X_USER_ID="tokenAAA")
    c.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    }, format="json")
    resp = c.get("/api/user/number/list")
    assert resp.json()["code"] == 0
    assert len(resp.json()["data"]) == 1


def test_header_token_isolates_users(ssq):
    a = APIClient(); a.credentials(HTTP_X_USER_ID="tokenAAA")
    a.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    }, format="json")
    b = APIClient(); b.credentials(HTTP_X_USER_ID="tokenBBB")
    assert b.get("/api/user/number/list").json()["data"] == []


def test_no_token_no_session_unauthenticated(ssq):
    resp = APIClient().get("/api/user/number/list")
    assert resp.json()["code"] == 1
