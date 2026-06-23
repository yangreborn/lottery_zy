import pytest
from django.core.management import call_command
from lottery.models import Lottery
from guide.models import PlayGuide


@pytest.fixture
def seeded(db):
    Lottery.objects.create(code="ssq", name="双色球", category="福彩", rule_config={}, draw_days=[])
    Lottery.objects.create(code="dlt", name="大乐透", category="体彩", rule_config={}, draw_days=[])


def test_seed_creates(seeded):
    call_command("seed_sample_guides")
    assert PlayGuide.objects.filter(is_active=True).count() >= 5
    assert PlayGuide.objects.filter(lottery__isnull=True, type="activity").exists()


def test_seed_idempotent(seeded):
    call_command("seed_sample_guides")
    n = PlayGuide.objects.count()
    call_command("seed_sample_guides")
    assert PlayGuide.objects.count() == n
