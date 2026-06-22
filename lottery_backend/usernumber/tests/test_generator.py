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
