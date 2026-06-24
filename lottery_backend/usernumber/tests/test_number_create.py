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


def test_create_dan_numbers_not_dict(ssq, auth_client):
    """dan_numbers 传 list 而非 dict 时应返回 code=1 而非 HTTP 500。"""
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "dan_random",
        "dan_numbers": [1, 2],
    }, format="json")
    assert resp.status_code == 200
    assert resp.json()["code"] == 1


def test_create_random_with_numbers_uses_provided(ssq, auth_client):
    nums = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}
    body = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random", "numbers": nums,
    }, format="json").json()
    assert body["code"] == 0
    assert body["data"]["gen_type"] == "random"
    assert body["data"]["numbers"] == nums


def test_create_random_with_invalid_numbers(ssq, auth_client):
    bad = {"red": [1, 2, 3], "blue": [7]}
    assert auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random", "numbers": bad,
    }, format="json").json()["code"] == 1


def test_create_random_without_numbers_generates(ssq, auth_client):
    body = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random",
    }, format="json").json()
    assert body["code"] == 0
    assert len(body["data"]["numbers"]["red"]) == 6
