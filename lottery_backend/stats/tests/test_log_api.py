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
