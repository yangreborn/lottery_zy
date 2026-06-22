import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def lotteries(db):
    Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                           rule_config={"red": {"count": 6, "min": 1, "max": 33},
                                        "blue": {"count": 1, "min": 1, "max": 16}},
                           draw_days=[2, 4, 7], is_active=True)
    Lottery.objects.create(code="dlt", name="超级大乐透", category="体彩",
                           rule_config={"red": {"count": 5, "min": 1, "max": 35},
                                        "blue": {"count": 2, "min": 1, "max": 12}},
                           draw_days=[1, 3, 6], is_active=True)
    Lottery.objects.create(code="off", name="下架彩种", category="福彩",
                           rule_config={}, draw_days=[], is_active=False)


def test_lottery_list_returns_active_only(client, lotteries):
    resp = client.get("/api/openapi/lottery/list")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    codes = [item["code"] for item in body["data"]]
    assert codes == ["dlt", "ssq"]  # 升序, 不含 off
    ssq = next(i for i in body["data"] if i["code"] == "ssq")
    assert ssq["rule_config"]["red"]["count"] == 6
    assert ssq["draw_days"] == [2, 4, 7]
