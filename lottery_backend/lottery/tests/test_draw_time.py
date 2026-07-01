import pytest
from django.core.management import call_command
from lottery.models import Lottery

EXPECTED = {"ssq": "21:15", "dlt": "21:25", "kl8": "21:30", "3d": "20:30", "pl3": "20:30"}


@pytest.mark.django_db
def test_seed_sets_draw_time():
    call_command("seed_lotteries")
    for code, t in EXPECTED.items():
        assert Lottery.objects.get(code=code).draw_time == t
