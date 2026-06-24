import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery
from usernumber.models import UserNumber


@pytest.fixture
def lottery(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth(db):
    c = APIClient()
    r = c.post("/api/user/login", {"code": "grp-user"}, format="json")
    token = r.json()["data"]["token"]
    c.credentials(HTTP_X_USER_ID=token)
    return c, token


def _create(c):
    r = c.post("/api/user/number/create",
               {"code": "ssq", "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}},
               format="json")
    return r.json()["data"]["id"]


def test_group_sets_name_stripped(auth, lottery):
    c, _ = auth
    rec_id = _create(c)
    r = c.post("/api/user/number/group",
               {"id": rec_id, "group_name": "  周末跟号  "}, format="json")
    body = r.json()
    assert body["code"] == 0
    assert body["data"]["group_name"] == "周末跟号"


def test_group_truncates_50(auth, lottery):
    c, _ = auth
    rec_id = _create(c)
    r = c.post("/api/user/number/group",
               {"id": rec_id, "group_name": "x" * 80}, format="json")
    assert len(r.json()["data"]["group_name"]) == 50


def test_group_clear_with_empty(auth, lottery):
    c, _ = auth
    rec_id = _create(c)
    c.post("/api/user/number/group", {"id": rec_id, "group_name": "g"}, format="json")
    r = c.post("/api/user/number/group", {"id": rec_id, "group_name": ""}, format="json")
    assert r.json()["data"]["group_name"] == ""


def test_group_not_own_record(auth, lottery):
    c, _ = auth
    other = UserNumber.objects.create(
        user_id="someone-else", lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    r = c.post("/api/user/number/group",
               {"id": other.id, "group_name": "g"}, format="json")
    assert r.json()["code"] == 1


def test_group_unauthenticated(db, lottery):
    c = APIClient()
    rec = UserNumber.objects.create(
        user_id="x", lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    r = c.post("/api/user/number/group",
               {"id": rec.id, "group_name": "g"}, format="json")
    assert r.json()["code"] == 1
