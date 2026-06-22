import pytest
from datetime import date
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                  rule_config={"red": {"count": 6, "min": 1, "max": 33},
                                               "blue": {"count": 1, "min": 1, "max": 16}},
                                  draw_days=[2, 4, 7])


def _mk(ssq, issue, d, status):
    return DrawResult.objects.create(
        lottery=ssq, issue=issue, draw_date=d,
        numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
        pool_amount="1500000000", status=status)


def test_latest_returns_newest_published(client, ssq):
    _mk(ssq, "2026070", date(2026, 6, 18), DrawResult.STATUS_PUBLISHED)
    _mk(ssq, "2026071", date(2026, 6, 20), DrawResult.STATUS_PUBLISHED)
    # 更新的一期还是 draft, 不应被返回
    _mk(ssq, "2026072", date(2026, 6, 22), DrawResult.STATUS_DRAFT)
    resp = client.get("/api/openapi/draw/latest?code=ssq")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["issue"] == "2026071"
    assert body["data"]["pool_amount"] == "1500000000"


def test_latest_unknown_code(client, db):
    resp = client.get("/api/openapi/draw/latest?code=nope")
    assert resp.json()["code"] == 1


def test_latest_missing_code_param(client, db):
    resp = client.get("/api/openapi/draw/latest")
    assert resp.json()["code"] == 1
