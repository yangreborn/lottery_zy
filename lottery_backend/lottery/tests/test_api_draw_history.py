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
                                 rule_config={"red": {"count": 6, "min": 1, "max": 33},
                                              "blue": {"count": 1, "min": 1, "max": 16}},
                                 draw_days=[2, 4, 7])
    for i in range(5):  # 2026060..2026064, 日期 6/1..6/5
        DrawResult.objects.create(
            lottery=lot, issue=f"202606{i}", draw_date=date(2026, 6, i + 1),
            numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [i + 1]},
            status=DrawResult.STATUS_PUBLISHED)
    # 一条 draft, 不应出现
    DrawResult.objects.create(lottery=lot, issue="2026099", draw_date=date(2026, 6, 9),
                              numbers={"red": [2, 3, 4, 5, 6, 7], "blue": [1]},
                              status=DrawResult.STATUS_DRAFT)
    return lot


def test_history_pagination(client, ssq):
    resp = client.get("/api/openapi/draw/history?code=ssq&page=1&page_size=2")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 5          # 不含 draft
    assert body["data"]["page_size"] == 2
    assert len(body["data"]["results"]) == 2
    # 倒序: 最新 6/5 的 2026064 在前
    assert body["data"]["results"][0]["issue"] == "2026064"


def test_history_date_filter(client, ssq):
    resp = client.get("/api/openapi/draw/history?code=ssq&date_from=2026-06-02&date_to=2026-06-03")
    body = resp.json()
    issues = [r["issue"] for r in body["data"]["results"]]
    assert issues == ["2026062", "2026061"]


def test_history_unknown_code(client, db):
    resp = client.get("/api/openapi/draw/history?code=nope")
    assert resp.json()["code"] == 1


def test_history_invalid_date_from_returns_code1(client, ssq):
    """非法 date_from 应返回 code=1，不得触发 500。"""
    resp = client.get("/api/openapi/draw/history?code=ssq&date_from=abc")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 1
    assert "日期" in body.get("msg", "")


def test_history_invalid_date_to_returns_code1(client, ssq):
    """非法 date_to 应返回 code=1，不得触发 500。"""
    resp = client.get("/api/openapi/draw/history?code=ssq&date_to=2026-13-99")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 1
    assert "日期" in body.get("msg", "")


def test_history_valid_date_range_still_works(client, ssq):
    """合法日期区间仍正常过滤，回归保证。"""
    resp = client.get("/api/openapi/draw/history?code=ssq&date_from=2026-06-02&date_to=2026-06-03")
    body = resp.json()
    assert body["code"] == 0
    issues = [r["issue"] for r in body["data"]["results"]]
    assert "2026061" in issues
    assert "2026062" in issues
