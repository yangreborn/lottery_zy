import datetime
import pytest
from django.core.management import call_command
from lottery.models import Lottery, DrawResult
from crawler import registry


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


class _FakeSsq:
    lottery_code = "ssq"

    def run(self, count=1):
        return [
            {"issue": "2026070", "draw_date": datetime.date(2026, 6, 20),
             "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
             "sales_amount": "100", "pool_amount": "200",
             "prize_grades": [{"level": 1, "count": 1, "amount": "1000"}]},
            {"issue": "2026071", "draw_date": datetime.date(2026, 6, 23),
             "numbers": {"red": [2, 3, 4, 5, 6, 7], "blue": [8]},
             "sales_amount": "110", "pool_amount": "210", "prize_grades": []},
        ]


def test_load_history_persists_and_publishes(ssq, monkeypatch):
    monkeypatch.setitem(registry.SPIDERS, "ssq", _FakeSsq)
    call_command("load_history", "--code", "ssq", "--count", "2")
    qs = DrawResult.objects.filter(lottery__code="ssq", status=DrawResult.STATUS_PUBLISHED)
    assert qs.count() == 2
    assert set(qs.values_list("issue", flat=True)) == {"2026070", "2026071"}


def test_load_history_idempotent(ssq, monkeypatch):
    monkeypatch.setitem(registry.SPIDERS, "ssq", _FakeSsq)
    call_command("load_history", "--code", "ssq", "--count", "2")
    call_command("load_history", "--code", "ssq", "--count", "2")
    assert DrawResult.objects.filter(lottery__code="ssq").count() == 2


def test_load_history_run_exception_skips(ssq, monkeypatch):
    class _Boom:
        lottery_code = "ssq"

        def run(self, count=1):
            raise RuntimeError("network down")

    monkeypatch.setitem(registry.SPIDERS, "ssq", _Boom)
    call_command("load_history", "--code", "ssq", "--count", "2")  # 不抛
    assert DrawResult.objects.filter(lottery__code="ssq").count() == 0
