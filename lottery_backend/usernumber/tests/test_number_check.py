import datetime
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult
from usernumber.models import UserNumber
from common.auth import hash_user_id

PRIZE_RULES = [
    {"level": 1, "red": 6, "blue": 1},
    {"level": 6, "red": 0, "blue": 1},
]


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16},
                     "prize_rules": PRIZE_RULES},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


def _published_draw(lottery, issue, numbers):
    return DrawResult.objects.create(
        lottery=lottery, issue=issue, draw_date=datetime.date(2026, 6, 20),
        numbers=numbers, status=DrawResult.STATUS_PUBLISHED,
    )


def _record(lottery, issue, numbers):
    return UserNumber.objects.create(
        user_id=hash_user_id("tester-openid"), lottery=lottery,
        numbers=numbers, target_issue=issue,
    )


def test_check_first_prize(ssq, auth_client):
    nums = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}
    _published_draw(ssq, "2026073", nums)
    rec = _record(ssq, "2026073", nums)
    resp = auth_client.get(f"/api/user/number/check?id={rec.id}")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["level"] == 1
    assert body["data"]["label"] == "一等奖"


def test_check_draw_not_published_yet(ssq, auth_client):
    rec = _record(ssq, "2026099", {"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    resp = auth_client.get(f"/api/user/number/check?id={rec.id}")
    assert resp.json()["code"] == 1


def test_check_record_not_own(ssq, auth_client):
    rec = UserNumber.objects.create(
        user_id=hash_user_id("other-openid"), lottery=ssq,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]}, target_issue="2026073",
    )
    resp = auth_client.get(f"/api/user/number/check?id={rec.id}")
    assert resp.json()["code"] == 1


def test_check_unauthenticated(ssq):
    resp = APIClient().get("/api/user/number/check?id=1")
    assert resp.json()["code"] == 1


def test_check_invalid_id(ssq, auth_client):
    """传非整数 id 应返回 code=1 而非 HTTP 500。"""
    resp = auth_client.get("/api/user/number/check?id=abc")
    assert resp.status_code == 200
    assert resp.json()["code"] == 1
