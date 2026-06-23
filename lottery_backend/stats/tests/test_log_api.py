import pytest
from rest_framework.test import APIClient
from stats.models import AccessLog


def test_log_with_header(db):
    c = APIClient()
    c.credentials(HTTP_X_USER_ID="tok123")
    resp = c.post("/api/openapi/log",
                  {"path": "draw/latest", "lottery_code": "ssq", "action": "view"}, format="json")
    assert resp.json()["code"] == 0
    log = AccessLog.objects.get()
    assert log.user_id == "tok123"
    assert log.path == "draw/latest"
    assert log.lottery_code == "ssq"
    assert log.action == "view"


def test_log_without_header(db):
    resp = APIClient().post("/api/openapi/log", {"path": "guide/index"}, format="json")
    assert resp.json()["code"] == 0
    log = AccessLog.objects.get()
    assert log.user_id == ""
    assert log.action == "view"


def test_log_missing_path(db):
    resp = APIClient().post("/api/openapi/log", {}, format="json")
    assert resp.json()["code"] == 1
    assert AccessLog.objects.count() == 0


def test_log_oversize_path_no_500(db):
    """超长 path（>100 字符）不应触发 500，应返回 code=1 且 HTTP 200，不写入记录。"""
    long_path = "x" * 200
    resp = APIClient().post("/api/openapi/log", {"path": long_path}, format="json")
    assert resp.status_code == 200, f"期望 HTTP 200，实际 {resp.status_code}"
    assert resp.json()["code"] == 1
    assert AccessLog.objects.count() == 0
