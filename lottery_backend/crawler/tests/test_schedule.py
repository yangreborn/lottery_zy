import pytest
from datetime import datetime, date, timedelta
from lottery.models import Lottery, DrawResult
from crawler.schedule import due_codes


def _weekday_on_or_after(iso, base=date(2026, 6, 1)):
    d = base
    while d.isoweekday() != iso:
        d += timedelta(days=1)
    return d


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩", rule_config={},
        draw_days=[2, 4, 7], draw_time="21:15",
    )


@pytest.mark.django_db
def test_in_window_no_result_today_is_due(ssq):
    d = _weekday_on_or_after(2)  # 周二，开奖日
    now = datetime(d.year, d.month, d.day, 21, 20)  # 21:15~22:45 窗口内
    assert "ssq" in due_codes(now)


@pytest.mark.django_db
def test_before_window_not_due(ssq):
    d = _weekday_on_or_after(2)
    now = datetime(d.year, d.month, d.day, 21, 0)  # 早于 21:15
    assert "ssq" not in due_codes(now)


@pytest.mark.django_db
def test_after_window_not_due(ssq):
    d = _weekday_on_or_after(2)
    now = datetime(d.year, d.month, d.day, 23, 0)  # 晚于 22:45
    assert "ssq" not in due_codes(now)


@pytest.mark.django_db
def test_not_draw_day_not_due(ssq):
    d = _weekday_on_or_after(1)  # 周一，不在 [2,4,7]
    now = datetime(d.year, d.month, d.day, 21, 20)
    assert "ssq" not in due_codes(now)


@pytest.mark.django_db
def test_already_out_today_not_due(ssq):
    d = _weekday_on_or_after(2)
    now = datetime(d.year, d.month, d.day, 21, 20)
    DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=d, numbers={},
        status=DrawResult.STATUS_PUBLISHED,
    )
    assert "ssq" not in due_codes(now)


@pytest.mark.django_db
def test_draft_today_still_due(ssq):
    """今日只有草稿(未发布)时，仍应继续抓取直到发布。"""
    d = _weekday_on_or_after(2)
    now = datetime(d.year, d.month, d.day, 21, 20)
    DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=d, numbers={},
        status=DrawResult.STATUS_DRAFT,
    )
    assert "ssq" in due_codes(now)


@pytest.mark.django_db
def test_empty_draw_time_excluded(db):
    Lottery.objects.create(
        code="kl8", name="快乐8", category="福彩", rule_config={},
        draw_days=[2], draw_time="",
    )
    d = _weekday_on_or_after(2)
    now = datetime(d.year, d.month, d.day, 21, 20)
    assert "kl8" not in due_codes(now)
