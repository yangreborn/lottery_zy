from lottery.validators import validate_numbers

SSQ = {"red": {"count": 6, "min": 1, "max": 33},
       "blue": {"count": 1, "min": 1, "max": 16}}


def test_valid_ssq():
    assert validate_numbers(SSQ, {"red": [1, 5, 12, 20, 28, 33], "blue": [8]}) == []


def test_wrong_count():
    errs = validate_numbers(SSQ, {"red": [1, 5, 12], "blue": [8]})
    assert any("red" in e and "个数" in e for e in errs)


def test_out_of_range():
    errs = validate_numbers(SSQ, {"red": [1, 5, 12, 20, 28, 99], "blue": [8]})
    assert any("范围" in e for e in errs)


def test_duplicate_numbers():
    errs = validate_numbers(SSQ, {"red": [1, 1, 12, 20, 28, 33], "blue": [8]})
    assert any("重复" in e for e in errs)


def test_numbers_zone_not_list():
    """numbers[zone] 为非列表（如 int）时不应抛异常，应返回错误列表。"""
    errs = validate_numbers(SSQ, {"red": 5, "blue": [7]})
    assert len(errs) > 0
