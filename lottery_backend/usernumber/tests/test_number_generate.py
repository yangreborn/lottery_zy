import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery
from lottery.validators import validate_numbers
from usernumber.models import UserNumber


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


def test_generate_returns_count_valid_sets(ssq, auth_client):
    body = auth_client.post("/api/user/number/generate",
                            {"code": "ssq", "count": 5}, format="json").json()
    assert body["code"] == 0
    sets = body["data"]["sets"]
    assert len(sets) == 5
    for s in sets:
        assert validate_numbers(ssq.rule_config, s) == []


def test_generate_no_db_write(ssq, auth_client):
    auth_client.post("/api/user/number/generate", {"code": "ssq", "count": 5}, format="json")
    assert UserNumber.objects.count() == 0


def test_generate_count_clamp(ssq, auth_client):
    big = auth_client.post("/api/user/number/generate", {"code": "ssq", "count": 99}, format="json").json()
    assert len(big["data"]["sets"]) == 10
    zero = auth_client.post("/api/user/number/generate", {"code": "ssq", "count": 0}, format="json").json()
    assert len(zero["data"]["sets"]) == 1
    bad = auth_client.post("/api/user/number/generate", {"code": "ssq", "count": "x"}, format="json").json()
    assert len(bad["data"]["sets"]) == 5


def test_generate_unknown_code(auth_client):
    assert auth_client.post("/api/user/number/generate",
                            {"code": "nope", "count": 5}, format="json").json()["code"] == 1


def test_generate_unauthenticated(ssq):
    assert APIClient().post("/api/user/number/generate",
                            {"code": "ssq", "count": 5}, format="json").json()["code"] == 1


def test_generate_keno_uses_picks(db, client):
    from lottery.models import Lottery
    Lottery.objects.create(
        code="kl8", name="快乐8", category="福彩",
        rule_config={"play_type": "keno", "zones": [
            {"key": "main", "label": "号码", "min": 1, "max": 80, "count": 20,
             "pick_min": 1, "pick_max": 10}]},
        draw_days=[1, 2, 3, 4, 5, 6, 7])
    login = client.post("/api/user/login", {"code": "gen-keno"},
                        content_type="application/json").json()
    token = login["data"]["token"]
    res = client.post("/api/user/number/generate",
                      data={"code": "kl8", "count": 2, "picks": {"main": 5}},
                      content_type="application/json",
                      HTTP_X_USER_ID=token).json()
    assert res["code"] == 0
    sets = res["data"]["sets"]
    assert len(sets) == 2
    assert all(len(s["main"]) == 5 for s in sets)
