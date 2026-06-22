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


def test_detail_with_level_label(client, ssq):
    DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22),
        numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
        prize_grades=[{"level": 1, "count": "5", "amount": "8000000"}],
        status=DrawResult.STATUS_PUBLISHED)
    resp = client.get("/api/openapi/draw/detail?code=ssq&issue=2026073")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["issue"] == "2026073"
    g = body["data"]["prize_grades"][0]
    assert g["level"] == 1
    assert g["level_label"] == "一等奖"
    assert g["amount"] == "8000000"


def test_detail_draft_not_found(client, ssq):
    DrawResult.objects.create(lottery=ssq, issue="2026074", draw_date=date(2026, 6, 24),
                              numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
                              status=DrawResult.STATUS_DRAFT)
    assert client.get("/api/openapi/draw/detail?code=ssq&issue=2026074").json()["code"] == 1


def test_detail_unknown(client, ssq):
    assert client.get("/api/openapi/draw/detail?code=ssq&issue=9999999").json()["code"] == 1
