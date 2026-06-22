from lottery.stats import compute_number_stats

RULE = {"red": {"count": 6, "min": 1, "max": 6}, "blue": {"count": 1, "min": 1, "max": 3}}


def test_count_and_miss():
    # 从新到旧 3 期
    draws = [
        {"red": [1, 2, 3, 4, 5, 6], "blue": [1]},  # 最新
        {"red": [1, 2, 3, 4, 5, 6], "blue": [2]},
        {"red": [1, 2, 3, 4, 5, 6], "blue": [3]},  # 最旧
    ]
    res = compute_number_stats(RULE, draws)
    red = {r["number"]: r for r in res["red"]}
    # 红球 1 每期都出, count=3, 最新一期出现 miss=0
    assert red[1]["count"] == 3
    assert red[1]["miss"] == 0
    blue = {b["number"]: b for b in res["blue"]}
    # 蓝球 1 只在最新一期出现: count=1, miss=0
    assert blue[1]["count"] == 1 and blue[1]["miss"] == 0
    # 蓝球 3 只在最旧一期出现: count=1, miss=2 (隔了 2 期没出)
    assert blue[3]["count"] == 1 and blue[3]["miss"] == 2


def test_never_appeared_miss_equals_window():
    draws = [{"red": [1, 2, 3, 4, 5, 6], "blue": [1]}]  # 窗口 1 期
    res = compute_number_stats(RULE, draws)
    blue = {b["number"]: b for b in res["blue"]}
    # 蓝球 2 从未出现: count=0, miss=1 (=窗口期数)
    assert blue[2]["count"] == 0 and blue[2]["miss"] == 1


def test_covers_full_range_sorted():
    res = compute_number_stats(RULE, [{"red": [1, 2, 3, 4, 5, 6], "blue": [1]}])
    assert [r["number"] for r in res["red"]] == [1, 2, 3, 4, 5, 6]
    assert [b["number"] for b in res["blue"]] == [1, 2, 3]
