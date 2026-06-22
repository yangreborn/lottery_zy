from usernumber.judge import judge_prize

SSQ_RULE = {
    "red": {"count": 6, "min": 1, "max": 33},
    "blue": {"count": 1, "min": 1, "max": 16},
    "prize_rules": [
        {"level": 1, "red": 6, "blue": 1},
        {"level": 2, "red": 6, "blue": 0},
        {"level": 3, "red": 5, "blue": 1},
        {"level": 4, "red": 5, "blue": 0},
        {"level": 4, "red": 4, "blue": 1},
        {"level": 5, "red": 4, "blue": 0},
        {"level": 5, "red": 3, "blue": 1},
        {"level": 6, "red": 2, "blue": 1},
        {"level": 6, "red": 1, "blue": 1},
        {"level": 6, "red": 0, "blue": 1},
    ],
}
DRAW = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}


def test_first_prize():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    assert r["red_hit"] == 6 and r["blue_hit"] == 1
    assert r["level"] == 1
    assert r["label"] == "一等奖"


def test_second_prize():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [1, 2, 3, 4, 5, 6], "blue": [16]})
    assert r["level"] == 2
    assert r["label"] == "二等奖"


def test_sixth_prize_blue_only():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [8, 9, 10, 11, 12, 13], "blue": [7]})
    assert r["red_hit"] == 0 and r["blue_hit"] == 1
    assert r["level"] == 6


def test_no_prize():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [8, 9, 10, 11, 12, 13], "blue": [16]})
    assert r["level"] is None
    assert r["label"] == "未中奖"
