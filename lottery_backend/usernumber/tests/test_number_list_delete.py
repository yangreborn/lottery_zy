import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery
from usernumber.models import UserNumber
from common.auth import hash_user_id


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


def _make_record(user_openid, lottery):
    return UserNumber.objects.create(
        user_id=hash_user_id(user_openid), lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    )


def test_list_returns_only_own(ssq, auth_client):
    _make_record("tester-openid", ssq)
    _make_record("other-openid", ssq)
    resp = auth_client.get("/api/user/number/list")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) == 1


def test_list_filter_by_code(ssq, auth_client):
    _make_record("tester-openid", ssq)
    resp = auth_client.get("/api/user/number/list?code=dlt")
    assert resp.json()["data"] == []


def test_delete_own(ssq, auth_client):
    rec = _make_record("tester-openid", ssq)
    resp = auth_client.delete(f"/api/user/number/{rec.id}")
    assert resp.json()["code"] == 0
    assert not UserNumber.objects.filter(id=rec.id).exists()


def test_delete_other_forbidden(ssq, auth_client):
    rec = _make_record("other-openid", ssq)
    resp = auth_client.delete(f"/api/user/number/{rec.id}")
    assert resp.json()["code"] == 1
    assert UserNumber.objects.filter(id=rec.id).exists()


def test_list_unauthenticated(ssq):
    resp = APIClient().get("/api/user/number/list")
    assert resp.json()["code"] == 1
