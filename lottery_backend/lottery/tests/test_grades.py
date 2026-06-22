from lottery.grades import grade_label


def test_int_levels():
    assert grade_label(1) == "一等奖"
    assert grade_label(6) == "六等奖"


def test_string_level_passthrough():
    assert grade_label("一等奖") == "一等奖"


def test_unknown_int_fallback():
    assert grade_label(99) == "99等奖"
