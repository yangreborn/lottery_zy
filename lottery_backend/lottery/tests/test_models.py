import pytest
from django.core.management import call_command
from django.db import IntegrityError
from lottery.models import Lottery


@pytest.mark.django_db
def test_create_lottery_and_unique_code():
    Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7], is_active=True,
    )
    assert Lottery.objects.get(code="ssq").name == "双色球"
    with pytest.raises(IntegrityError):
        Lottery.objects.create(
            code="ssq", name="重复", category="福彩",
            rule_config={}, draw_days=[],
        )


@pytest.mark.django_db
def test_seed_lotteries_idempotent():
    call_command("seed_lotteries")
    call_command("seed_lotteries")  # 再跑一次不应重复
    assert Lottery.objects.count() == 2
    dlt = Lottery.objects.get(code="dlt")
    assert dlt.rule_config["blue"]["count"] == 2
