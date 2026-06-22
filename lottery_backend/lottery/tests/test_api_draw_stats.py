import pytest
from datetime import date
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def ssq(db):
    lot = Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                 rule_config={"red": {"count": 6, "min": 1, "max": 6},
                                              "blue": {"count": 1, "min": 1, "max": 3}},
                                 draw_days=[2, 4, 7])
    for i in range(3):
        DrawResult.objects.create(
            lottery=lot, issue=f"202606{i}", draw_date=date(2026, 6, i + 1),
            numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [i + 1]},
            status=DrawResult.STATUS_PUBLISHED)
    return lot


def test_stats_endpoint(client, ssq):
    resp = client.get("/api/openapi/draw/stats?code=ssq&periods=30")
    body = resp.json()
    assert body["code"] == 0
    red = {r["number"]: r for r in body["data"]["red"]}
    assert red[1]["count"] == 3 and red[1]["miss"] == 0
    blue = {b["number"]: b for b in body["data"]["blue"]}
    # 按日期倒序最新一期是 6/3(blue 3) → blue 3 miss=0; blue 1 在最旧的 6/1, miss=2
    assert blue[3]["count"] == 1 and blue[3]["miss"] == 0
    assert blue[1]["count"] == 1 and blue[1]["miss"] == 2
    assert body["data"]["periods"] == 3  # 实际参与统计的期数


def test_stats_unknown_code(client, db):
    assert client.get("/api/openapi/draw/stats?code=nope").json()["code"] == 1
