from usernumber.judge import judge_prize, judge_keno

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


KENO_RC = {"play_type": "keno", "zones": [{"key": "main", "min": 1, "max": 80, "count": 20}],
           "prize_rules": [
               {"pick": 5, "hit": 5, "level": 1, "label": "选五中五", "amount": 1000},
               {"pick": 5, "hit": 4, "level": 2, "label": "选五中四", "amount": 21},
               {"pick": 5, "hit": 3, "level": 3, "label": "选五中三", "amount": 3},
           ]}


def test_keno_hit_all():
    draw = {"main": [1, 2, 3, 4, 5] + list(range(10, 25))}  # 含 1-5
    r = judge_keno(KENO_RC, draw, {"main": [1, 2, 3, 4, 5]})
    assert r["pick"] == 5 and r["hit"] == 5
    assert r["label"] == "选五中五" and r["amount"] == 1000
    assert r["desc"] == "选5中5"


def test_keno_partial_hit():
    draw = {"main": [1, 2, 3] + list(range(30, 47))}  # 含 1,2,3 不含 4,5
    r = judge_keno(KENO_RC, draw, {"main": [1, 2, 3, 4, 5]})
    assert r["hit"] == 3 and r["label"] == "选五中三"


def test_keno_no_win():
    draw = {"main": list(range(40, 60))}  # 不含 1-5
    r = judge_keno(KENO_RC, draw, {"main": [1, 2, 3, 4, 5]})
    assert r["hit"] == 0 and r["label"] == "未中奖"


def test_prize_has_desc():
    rc = {"red": {"count": 6, "min": 1, "max": 33}, "blue": {"count": 1, "min": 1, "max": 16},
          "prize_rules": [{"level": 1, "red": 6, "blue": 1}]}
    r = judge_prize(rc, {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
                    {"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    assert r["level"] == 1 and r["desc"] == "命中 红6 蓝1"
