import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from lottery.models import Lottery
from usernumber.models import PurchaseRecord
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


VALID = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}


def _make(openid, lottery, issue="2026073"):
    return PurchaseRecord.objects.create(
        user_id=hash_user_id(openid), lottery=lottery,
        issue=issue, numbers=VALID, purchase_date="2026-06-20",
    )


def test_purchase_create(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": VALID, "bet_count": 2, "purchase_date": "2026-06-20"},
        format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["issue"] == "2026073"
    assert body["data"]["bet_count"] == 2
    assert str(body["data"]["purchase_date"]) == "2026-06-20"
    assert body["data"]["code"] == "ssq"


def test_purchase_create_issue_required(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "  ", "numbers": VALID}, format="json")
    assert resp.json()["code"] == 1
    assert PurchaseRecord.objects.count() == 0


def test_purchase_create_invalid_numbers(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": {"red": [1], "blue": [7]}}, format="json")
    assert resp.json()["code"] == 1


def test_purchase_create_defaults(ssq, auth_client):
    resp = auth_client.post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": VALID}, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["bet_count"] == 1
    rec = PurchaseRecord.objects.get(id=body["data"]["id"])
    assert rec.purchase_date == timezone.now().date()


def test_purchase_create_unauthenticated(ssq):
    resp = APIClient().post("/api/user/purchase/create",
        {"code": "ssq", "issue": "2026073", "numbers": VALID}, format="json")
    assert resp.json()["code"] == 1


def test_purchase_list_only_own(ssq, auth_client):
    _make("tester-openid", ssq)
    _make("other-openid", ssq)
    resp = auth_client.get("/api/user/purchase/list")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) == 1


def test_purchase_delete_own(ssq, auth_client):
    rec = _make("tester-openid", ssq)
    resp = auth_client.delete(f"/api/user/purchase/{rec.id}")
    assert resp.json()["code"] == 0
    assert not PurchaseRecord.objects.filter(id=rec.id).exists()


def test_purchase_delete_other_forbidden(ssq, auth_client):
    rec = _make("other-openid", ssq)
    resp = auth_client.delete(f"/api/user/purchase/{rec.id}")
    assert resp.json()["code"] == 1
    assert PurchaseRecord.objects.filter(id=rec.id).exists()
