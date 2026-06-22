import pytest
from datetime import date
from lottery.models import Lottery, DrawResult
from crawler.persist import persist_draw


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_persist_valid_creates_draft(ssq):
    item = {"issue": "2026073", "draw_date": date(2026, 6, 22),
            "numbers": {"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
            "sales_amount": "300000000", "pool_amount": "1500000000",
            "prize_grades": [{"level": 1, "count": 5, "amount": "8000000"}]}
    obj, errs = persist_draw(ssq, item)
    assert errs == []
    assert obj.status == DrawResult.STATUS_DRAFT
    assert obj.source == DrawResult.SOURCE_CRAWLER


def test_persist_invalid_skips(ssq):
    item = {"issue": "2026074", "draw_date": date(2026, 6, 24),
            "numbers": {"red": [1, 5, 12], "blue": [8]}, "prize_grades": []}
    obj, errs = persist_draw(ssq, item)
    assert obj is None
    assert errs
    assert DrawResult.objects.filter(issue="2026074").count() == 0
