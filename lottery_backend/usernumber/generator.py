import random


def random_numbers(rule_config):
    """按 rule_config 机选，每区取 count 个不重复号码，升序返回。"""
    result = {}
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        picks = random.sample(range(rule["min"], rule["max"] + 1), rule["count"])
        result[zone] = sorted(picks)
    return result


def dan_random_numbers(rule_config, dan_numbers):
    """定胆随机：锁定胆码，剩余位从未选号码池随机补全；胆码非法抛 ValueError。"""
    result = {}
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        dans = list(dict.fromkeys(dan_numbers.get(zone, [])))  # 去重保序
        count = rule["count"]
        for d in dans:
            if not (rule["min"] <= d <= rule["max"]):
                raise ValueError(f"{zone} 胆码 {d} 超出范围 [{rule['min']},{rule['max']}]")
        if len(dans) > count:
            raise ValueError(f"{zone} 胆码数量 {len(dans)} 超过该区号码数 {count}")
        pool = [n for n in range(rule["min"], rule["max"] + 1) if n not in dans]
        picks = dans + random.sample(pool, count - len(dans))
        result[zone] = sorted(picks)
    return result
