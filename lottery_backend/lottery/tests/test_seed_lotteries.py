import pytest
from django.core.management import call_command
from lottery.models import Lottery
from lottery.zones import get_zones


@pytest.fixture
def seeded(db):
    call_command("seed_lotteries")


def test_ssq_zones_format(seeded):
    rc = Lottery.objects.get(code="ssq").rule_config
    zones = get_zones(rc)
    assert [z["key"] for z in zones] == ["red", "blue"]
    assert zones[0]["count"] == 6 and zones[1]["count"] == 1


def test_kl8_seeded(seeded):
    kl8 = Lottery.objects.get(code="kl8")
    rc = kl8.rule_config
    assert rc["play_type"] == "keno"
    z = get_zones(rc)[0]
    assert z["key"] == "main" and z["max"] == 80 and z["count"] == 20
    assert z["pick_min"] == 1 and z["pick_max"] == 10
    # 选十中十在奖表里
    assert any(r["pick"] == 10 and r["hit"] == 10 for r in rc["prize_rules"])
