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


def test_numbers_is_list_not_dict():
    """numbers 是列表（而非字典）时不应抛 AttributeError，应返回非空错误列表。"""
    errs = validate_numbers(SSQ, [1, 2, 3])
    assert len(errs) > 0


def test_numbers_is_string_not_dict():
    """numbers 是字符串（而非字典）时不应抛 AttributeError，应返回非空错误列表。"""
    errs = validate_numbers(SSQ, "x")
    assert len(errs) > 0


KENO_RC = {"zones": [{"key": "main", "label": "号码", "min": 1, "max": 80,
                      "count": 20, "pick_min": 1, "pick_max": 10}], "play_type": "keno"}


def test_keno_pick_within_range_ok():
    assert validate_numbers(KENO_RC, {"main": [1, 2, 3, 4, 5]}, mode="pick") == []


def test_keno_pick_too_many():
    errs = validate_numbers(KENO_RC, {"main": list(range(1, 12))}, mode="pick")  # 11 个
    assert errs != []


def test_keno_draw_must_be_20():
    assert validate_numbers(KENO_RC, {"main": list(range(1, 21))}, mode="draw") == []
    assert validate_numbers(KENO_RC, {"main": [1, 2, 3]}, mode="draw") != []


def test_keno_pick_out_of_value_range():
    assert validate_numbers(KENO_RC, {"main": [99]}, mode="pick") != []


DIGIT_RC = {"play_type": "digit", "zones": [
    {"key": "digits", "label": "数字", "min": 0, "max": 9, "count": 3,
     "ordered": True, "allow_repeat": True}]}


def test_digit_allows_repeat():
    assert validate_numbers(DIGIT_RC, {"digits": [5, 5, 3]}, mode="pick") == []


def test_digit_count_must_be_3():
    assert validate_numbers(DIGIT_RC, {"digits": [1, 2]}, mode="pick") != []


def test_digit_out_of_range():
    assert validate_numbers(DIGIT_RC, {"digits": [1, 2, 10]}, mode="pick") != []
