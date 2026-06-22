import pytest
from datetime import date
from django.db import IntegrityError
from lottery.models import Lottery, DrawResult


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_create_drawresult(ssq):
    d = DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22),
        numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
        pool_amount="1500000000", prize_grades=[{"level": 1, "count": 5, "amount": "8000000"}],
        source=DrawResult.SOURCE_CRAWLER, status=DrawResult.STATUS_DRAFT,
    )
    assert d.status == "draft"
    assert d.numbers["blue"] == [8]


def test_unique_lottery_issue(ssq):
    DrawResult.objects.create(lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22), numbers={})
    with pytest.raises(IntegrityError):
        DrawResult.objects.create(lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22), numbers={})
