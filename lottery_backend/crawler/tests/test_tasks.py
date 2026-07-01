import pytest
from datetime import date
from lottery.models import Lottery, DrawResult
from crawler import tasks


class _FakeSpider:
    def run(self, *args):
        return [{
            "issue": "2026073", "draw_date": date(2026, 6, 22),
            "numbers": {"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
            "sales_amount": "", "pool_amount": "", "prize_grades": [], "prize_area": "",
        }]


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7], draw_time="21:15",
    )


@pytest.mark.django_db
def test_poll_persists_and_publishes(ssq, monkeypatch):
    monkeypatch.setitem(tasks.SPIDERS, "ssq", _FakeSpider)
    tasks.poll_lottery("ssq")
    d = DrawResult.objects.get(lottery=ssq, issue="2026073")
    assert d.status == DrawResult.STATUS_PUBLISHED


@pytest.mark.django_db
def test_poll_idempotent(ssq, monkeypatch):
    monkeypatch.setitem(tasks.SPIDERS, "ssq", _FakeSpider)
    tasks.poll_lottery("ssq")
    tasks.poll_lottery("ssq")
    assert DrawResult.objects.filter(lottery=ssq, issue="2026073").count() == 1


@pytest.mark.django_db
def test_poll_unknown_code_no_raise(db):
    tasks.poll_lottery("nope")  # 未注册彩种，不抛出


@pytest.mark.django_db
def test_poll_spider_error_no_raise(ssq, monkeypatch):
    class _Boom:
        def run(self, *args):
            raise RuntimeError("net down")
    monkeypatch.setitem(tasks.SPIDERS, "ssq", _Boom)
    tasks.poll_lottery("ssq")  # 抓取异常被吞，不抛出
    assert not DrawResult.objects.filter(issue="2026073").exists()
