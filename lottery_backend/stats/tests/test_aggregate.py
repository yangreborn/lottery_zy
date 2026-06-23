import datetime
import pytest
from django.utils import timezone
from stats.models import AccessLog
from stats.aggregate import compute_dashboard


@pytest.fixture
def logs(db):
    AccessLog.objects.create(user_id="A", path="draw/latest", lottery_code="ssq", action="view")
    AccessLog.objects.create(user_id="A", path="draw/stats", lottery_code="ssq", action="view")
    AccessLog.objects.create(user_id="B", path="guide/index", lottery_code="dlt", action="view")
    AccessLog.objects.create(user_id="", path="draw/latest", lottery_code="ssq", action="view")
    AccessLog.objects.create(user_id="A", path="mine/create", lottery_code="ssq", action="save_number")


def test_pv_uv(logs):
    d = compute_dashboard(7)
    assert d["pv"] == 5
    assert d["uv"] == 2  # A,B；空 user_id 排除


def test_top_lotteries(logs):
    d = compute_dashboard(7)
    top = {r["lottery_code"]: r["count"] for r in d["top_lotteries"]}
    assert top["ssq"] == 4
    assert top["dlt"] == 1


def test_actions(logs):
    d = compute_dashboard(7)
    acts = {r["action"]: r["count"] for r in d["actions"]}
    assert acts["view"] == 4
    assert acts["save_number"] == 1


def test_excludes_old(logs):
    old = AccessLog.objects.create(user_id="C", path="x", lottery_code="ssq", action="view")
    AccessLog.objects.filter(id=old.id).update(
        created_at=timezone.now() - datetime.timedelta(days=30))
    d = compute_dashboard(7)
    assert d["uv"] == 2  # C 超出近 7 天不计


def test_dau_has_today(logs):
    d = compute_dashboard(7)
    assert len(d["dau"]) >= 1
    assert d["dau"][0]["count"] == 2  # 今日 distinct user A,B
