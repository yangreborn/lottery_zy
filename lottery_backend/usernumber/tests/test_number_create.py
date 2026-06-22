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


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


def test_create_manual_valid(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
        "note": "test",
    }, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["numbers"]["blue"] == [7]
    assert body["data"]["note"] == "test"


def test_create_manual_invalid(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3], "blue": [7]},
    }, format="json")
    assert resp.json()["code"] == 1


def test_create_random(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random",
    }, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["numbers"]["red"]) == 6


def test_create_dan_random(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "dan_random",
        "dan_numbers": {"red": [7, 8], "blue": []},
    }, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert 7 in body["data"]["numbers"]["red"]


def test_create_unauthenticated(ssq):
    resp = APIClient().post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random",
    }, format="json")
    assert resp.json()["code"] == 1


def test_create_unknown_code(auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "nope", "gen_type": "random",
    }, format="json")
    assert resp.json()["code"] == 1
