import pytest
from usernumber.generator import random_numbers, dan_random_numbers

RULE = {"red": {"count": 6, "min": 1, "max": 33},
        "blue": {"count": 1, "min": 1, "max": 16}}


def test_random_numbers_shape_and_range():
    nums = random_numbers(RULE)
    assert len(nums["red"]) == 6
    assert len(set(nums["red"])) == 6
    assert nums["red"] == sorted(nums["red"])
    assert all(1 <= n <= 33 for n in nums["red"])
    assert len(nums["blue"]) == 1
    assert 1 <= nums["blue"][0] <= 16


def test_dan_random_includes_dan_and_fills():
    nums = dan_random_numbers(RULE, {"red": [7, 8], "blue": []})
    assert 7 in nums["red"] and 8 in nums["red"]
    assert len(nums["red"]) == 6
    assert len(set(nums["red"])) == 6
    assert nums["red"] == sorted(nums["red"])
    assert len(nums["blue"]) == 1


def test_dan_out_of_range_raises():
    with pytest.raises(ValueError):
        dan_random_numbers(RULE, {"red": [99], "blue": []})


def test_dan_too_many_raises():
    with pytest.raises(ValueError):
        dan_random_numbers(RULE, {"red": [1, 2, 3, 4, 5, 6, 7], "blue": []})


KENO_RC = {"zones": [{"key": "main", "min": 1, "max": 80, "count": 20,
                      "pick_min": 1, "pick_max": 10}], "play_type": "keno"}


def test_random_keno_uses_picks():
    r = random_numbers(KENO_RC, picks={"main": 5})
    assert len(r["main"]) == 5
    assert all(1 <= n <= 80 for n in r["main"])
    assert len(set(r["main"])) == 5  # 不重复


def test_random_keno_default_pick_max():
    r = random_numbers(KENO_RC)  # 不传 picks → pick_max=10
    assert len(r["main"]) == 10


def test_random_keno_clamps():
    assert len(random_numbers(KENO_RC, picks={"main": 99})["main"]) == 10  # 夹到 pick_max
    assert len(random_numbers(KENO_RC, picks={"main": 0})["main"]) == 1    # 夹到 pick_min


def test_random_ssq_legacy_unchanged():
    rc = {"red": {"count": 6, "min": 1, "max": 33}, "blue": {"count": 1, "min": 1, "max": 16}}
    r = random_numbers(rc)
    assert len(r["red"]) == 6 and len(r["blue"]) == 1
