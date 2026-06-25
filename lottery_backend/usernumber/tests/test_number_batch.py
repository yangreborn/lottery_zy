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


def _make_record(user_openid, lottery, group_name=""):
    return UserNumber.objects.create(
        user_id=hash_user_id(user_openid), lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]}, group_name=group_name,
    )


def test_batch_delete_own_skip_others(ssq, auth_client):
    r1 = _make_record("tester-openid", ssq)
    r2 = _make_record("tester-openid", ssq)
    other = _make_record("other-openid", ssq)
    resp = auth_client.post("/api/user/number/batch_delete",
                            {"ids": [r1.id, r2.id, other.id]}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["deleted"] == 2
    assert not UserNumber.objects.filter(id__in=[r1.id, r2.id]).exists()
    assert UserNumber.objects.filter(id=other.id).exists()


def test_batch_delete_empty_ids(ssq, auth_client):
    resp = auth_client.post("/api/user/number/batch_delete", {"ids": []}, format="json")
    assert resp.json()["code"] == 1


def test_batch_delete_unauthenticated(ssq):
    resp = APIClient().post("/api/user/number/batch_delete", {"ids": [1]}, format="json")
    assert resp.json()["code"] == 1


def test_batch_group_set_skip_others(ssq, auth_client):
    r1 = _make_record("tester-openid", ssq)
    r2 = _make_record("tester-openid", ssq)
    other = _make_record("other-openid", ssq)
    resp = auth_client.post("/api/user/number/batch_group",
                            {"ids": [r1.id, r2.id, other.id], "group_name": "甲组"}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["updated"] == 2
    r1.refresh_from_db(); r2.refresh_from_db(); other.refresh_from_db()
    assert r1.group_name == "甲组"
    assert r2.group_name == "甲组"
    assert other.group_name == ""


def test_batch_group_clear(ssq, auth_client):
    r1 = _make_record("tester-openid", ssq, group_name="旧组")
    resp = auth_client.post("/api/user/number/batch_group",
                            {"ids": [r1.id], "group_name": ""}, format="json")
    assert resp.json()["code"] == 0
    r1.refresh_from_db()
    assert r1.group_name == ""
