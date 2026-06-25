from rest_framework.test import APIClient


def _login(c):
    c.post("/api/user/login", {"code": "dev-prof"}, format="json")


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
