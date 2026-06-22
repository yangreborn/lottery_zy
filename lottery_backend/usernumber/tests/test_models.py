import pytest
from lottery.models import Lottery
from usernumber.models import UserNumber


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_create_user_number_defaults(ssq):
    rec = UserNumber.objects.create(
        user_id="hash_abc", lottery=ssq,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    )
    assert rec.gen_type == UserNumber.GEN_MANUAL
    assert rec.dan_numbers == {}
    assert rec.note == ""
    assert rec.target_issue == ""
    assert rec.created_at is not None


def test_gen_type_constants():
    assert UserNumber.GEN_MANUAL == "manual"
    assert UserNumber.GEN_RANDOM == "random"
    assert UserNumber.GEN_DAN == "dan_random"
