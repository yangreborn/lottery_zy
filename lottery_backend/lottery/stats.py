def compute_number_stats(rule_config, draws):
    """统计每个号码在窗口内的出现次数与遗漏值。

    draws: 从新到旧的号码列表 [{"red":[...], "blue":[...]}, ...]。
    返回 {"red": [{"number","count","miss"}, ...], "blue": [...]}，号码升序。
    miss = 距上次出现过去的期数(最新一期出现=0)；窗口内未出现=窗口期数。
    """
    window = len(draws)
    result = {}
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        lo, hi = rule.get("min"), rule.get("max")
        if lo is None or hi is None:
            continue
        zone_stats = []
        for number in range(lo, hi + 1):
            count = 0
            miss = window  # 默认: 从未出现
            first_seen = False
            for idx, draw in enumerate(draws):  # idx=0 是最新一期
                if number in draw.get(zone, []):
                    count += 1
                    if not first_seen:
                        miss = idx
                        first_seen = True
            zone_stats.append({"number": number, "count": count, "miss": miss})
        result[zone] = zone_stats
    return result
