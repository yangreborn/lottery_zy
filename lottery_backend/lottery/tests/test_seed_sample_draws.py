import pytest
from django.core.management import call_command
from lottery.models import Lottery, DrawResult
from lottery.validators import validate_numbers


@pytest.fixture
def seeded(db):
    call_command("seed_lotteries")


def test_creates_published_draws_for_both(seeded):
    call_command("seed_sample_draws")
    for code in ("ssq", "dlt"):
        qs = DrawResult.objects.filter(lottery__code=code,
                                       status=DrawResult.STATUS_PUBLISHED)
        assert qs.count() >= 3


def test_sample_numbers_are_valid(seeded):
    call_command("seed_sample_draws")
    for draw in DrawResult.objects.select_related("lottery"):
        errors = validate_numbers(draw.lottery.rule_config, draw.numbers)
        assert errors == []


def test_idempotent(seeded):
    call_command("seed_sample_draws")
    call_command("seed_sample_draws")
    # 第二次不应重复插入（按 lottery+issue 唯一）
    assert DrawResult.objects.filter(lottery__code="ssq").count() == \
        DrawResult.objects.filter(lottery__code="ssq", status=DrawResult.STATUS_PUBLISHED).count()
