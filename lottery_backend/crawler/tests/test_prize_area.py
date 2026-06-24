import datetime
import pytest
from lottery.models import Lottery, DrawResult
from lottery.serializers import DrawResultSerializer
from crawler.persist import persist_draw


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"zones": [
            {"key": "red", "label": "红球", "min": 1, "max": 33, "count": 6},
            {"key": "blue", "label": "蓝球", "min": 1, "max": 16, "count": 1}]},
        draw_days=[2, 4, 7])


def test_persist_stores_prize_area(ssq):
    item = {
        "issue": "2026071", "draw_date": datetime.date(2026, 6, 23),
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
        "prize_grades": [], "prize_area": "一等奖中奖情况：北京1注、广东3注，共4注",
    }
    obj, errors = persist_draw(ssq, item)
    assert errors == []
    assert obj.prize_area == "一等奖中奖情况：北京1注、广东3注，共4注"


def test_serializer_exposes_prize_area(ssq):
    obj = DrawResult.objects.create(
        lottery=ssq, issue="2026072", draw_date=datetime.date(2026, 6, 25),
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
        prize_area="北京1注")
    data = DrawResultSerializer(obj).data
    assert data["prize_area"] == "北京1注"


def test_prize_area_defaults_empty(ssq):
    obj = DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=datetime.date(2026, 6, 27),
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    assert obj.prize_area == ""
