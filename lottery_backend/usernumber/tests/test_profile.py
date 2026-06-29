from rest_framework.test import APIClient

from lottery.models import Lottery


def _login(c):
    c.post("/api/user/login", {"code": "dev-prof"}, format="json")


def _mk_lotteries():
    Lottery.objects.create(code="ssq", name="双色球", category="福彩")
    Lottery.objects.create(code="dlt", name="大乐透", category="体彩")


def test_profile_requires_login(db):
    assert APIClient().get("/api/user/profile").json()["code"] == 1


def test_set_and_get_nickname(db):
    c = APIClient()
    _login(c)
    r = c.post("/api/user/profile", {"nickname": " 小红 "}, format="json").json()
    assert r["code"] == 0
    assert r["data"]["nickname"] == "小红"
    g = c.get("/api/user/profile").json()
    assert g["data"]["nickname"] == "小红"
    assert len(g["data"]["short_id"]) == 8


def test_nickname_too_long(db):
    c = APIClient()
    _login(c)
    r = c.post("/api/user/profile", {"nickname": "x" * 31}, format="json").json()
    assert r["code"] == 1


def test_set_nickname_without_appuser_record(db):
    # 持有合法 uid(头)但从未登录建档 → profile 不建档，拒绝
    body = APIClient().post("/api/user/profile", {"nickname": "x"},
                            HTTP_X_USER_ID="ab" * 32, format="json").json()
    assert body["code"] == 1


def test_home_lotteries_default_empty(db):
    c = APIClient()
    _login(c)
    g = c.get("/api/user/profile").json()
    assert g["data"]["home_lotteries"] == []


def test_home_lotteries_set_and_get(db):
    _mk_lotteries()
    c = APIClient()
    _login(c)
    # 含非上架 code "xyz"，应被过滤；顺序保留请求顺序
    r = c.post("/api/user/profile", {"home_lotteries": ["dlt", "ssq", "xyz"]}, format="json").json()
    assert r["code"] == 0
    assert r["data"]["home_lotteries"] == ["dlt", "ssq"]
    g = c.get("/api/user/profile").json()
    assert g["data"]["home_lotteries"] == ["dlt", "ssq"]


def test_home_lotteries_invalid_type(db):
    c = APIClient()
    _login(c)
    r = c.post("/api/user/profile", {"home_lotteries": "ssq"}, format="json").json()
    assert r["code"] == 1


def test_nickname_only_keeps_home_lotteries(db):
    _mk_lotteries()
    c = APIClient()
    _login(c)
    c.post("/api/user/profile", {"home_lotteries": ["ssq"]}, format="json")
    # 只传 nickname 不应清空 home_lotteries（向后兼容）
    c.post("/api/user/profile", {"nickname": "小明"}, format="json")
    g = c.get("/api/user/profile").json()
    assert g["data"]["home_lotteries"] == ["ssq"]
    assert g["data"]["nickname"] == "小明"
