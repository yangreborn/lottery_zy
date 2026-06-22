import json
import pytest
from pathlib import Path
from unittest import mock
from django.core.management import call_command
from lottery.models import Lottery, DrawResult

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_crawl_draw_ssq(ssq):
    raw = json.loads((FIXTURES / "ssq_sample.json").read_text(encoding="utf-8"))
    with mock.patch("crawler.spiders.ssq.SsqSpider.fetch", return_value=raw):
        call_command("crawl_draw", "--code=ssq")
    d = DrawResult.objects.get(lottery=ssq, issue="2026073")
    assert d.status == DrawResult.STATUS_DRAFT
    assert d.numbers["red"] == [1, 5, 12, 20, 28, 33]
