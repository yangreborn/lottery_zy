import datetime
import pytest
from rest_framework.test import APIClient
from django.utils import timezone
from lottery.models import Lottery
from guide.models import PlayGuide


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                  rule_config={}, draw_days=[2, 4, 7])


def test_list_code_includes_common(ssq):
    PlayGuide.objects.create(lottery=ssq, type="intro", title="双色球玩法")
    PlayGuide.objects.create(lottery=None, type="activity", title="通用活动")
    dlt = Lottery.objects.create(code="dlt", name="大乐透", category="体彩",
                                 rule_config={}, draw_days=[1, 3, 6])
    PlayGuide.objects.create(lottery=dlt, type="intro", title="大乐透玩法")
    titles = [g["title"] for g in APIClient().get("/api/openapi/guide/list?code=ssq").json()["data"]]
    assert "双色球玩法" in titles
    assert "通用活动" in titles
    assert "大乐透玩法" not in titles


def test_list_type_filter(ssq):
    PlayGuide.objects.create(lottery=ssq, type="intro", title="玩法")
    PlayGuide.objects.create(lottery=ssq, type="rule", title="奖级")
    titles = [g["title"] for g in APIClient().get("/api/openapi/guide/list?code=ssq&type=rule").json()["data"]]
    assert titles == ["奖级"]


def test_list_excludes_inactive_and_future(ssq):
    PlayGuide.objects.create(lottery=ssq, type="intro", title="上架")
    PlayGuide.objects.create(lottery=ssq, type="intro", title="下架", is_active=False)
    PlayGuide.objects.create(lottery=ssq, type="intro", title="未来",
                             publish_at=timezone.now() + datetime.timedelta(days=1))
    titles = [g["title"] for g in APIClient().get("/api/openapi/guide/list?code=ssq").json()["data"]]
    assert "上架" in titles
    assert "下架" not in titles
    assert "未来" not in titles


def test_list_no_content_field(ssq):
    PlayGuide.objects.create(lottery=ssq, type="intro", title="玩法", content="<p>hi</p>")
    data = APIClient().get("/api/openapi/guide/list?code=ssq").json()["data"]
    assert "content" not in data[0]
    assert data[0]["type_label"] == "玩法说明"


def test_detail_returns_content(ssq):
    g = PlayGuide.objects.create(lottery=ssq, type="intro", title="玩法", content="<p>规则</p>")
    body = APIClient().get(f"/api/openapi/guide/detail?id={g.id}").json()
    assert body["code"] == 0
    assert body["data"]["content"] == "<p>规则</p>"


def test_detail_missing(ssq):
    assert APIClient().get("/api/openapi/guide/detail?id=99999").json()["code"] == 1


def test_detail_invalid_id(ssq):
    assert APIClient().get("/api/openapi/guide/detail?id=abc").json()["code"] == 1
