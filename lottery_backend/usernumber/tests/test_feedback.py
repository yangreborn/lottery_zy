import pytest
from rest_framework.test import APIClient
from usernumber.models import Feedback


@pytest.fixture
def api_client():
    return APIClient()


def test_feedback_create_anonymous(db, api_client):
    resp = api_client.post("/api/user/feedback", {"content": "界面建议调大字体"}, format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["id"]
    rec = Feedback.objects.get(id=body["data"]["id"])
    assert rec.user_id == ""
    assert rec.content == "界面建议调大字体"


def test_feedback_empty_content_rejected(db, api_client):
    resp = api_client.post("/api/user/feedback", {"content": "   "}, format="json")
    assert resp.json()["code"] == 1
    assert Feedback.objects.count() == 0


def test_feedback_too_long_rejected(db, api_client):
    resp = api_client.post("/api/user/feedback", {"content": "x" * 501}, format="json")
    assert resp.json()["code"] == 1
    assert Feedback.objects.count() == 0
