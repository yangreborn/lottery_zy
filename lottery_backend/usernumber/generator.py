import random
from lottery.zones import get_zones


def _pick_count(zone, picks):
    if "pick_min" in zone and "pick_max" in zone:
        n = (picks or {}).get(zone["key"], zone["pick_max"])
        return max(zone["pick_min"], min(n, zone["pick_max"]))
    return zone["count"]


def random_numbers(rule_config, picks=None):
    """按 rule_config 机选。picks={zone_key:n} 指定可变区选几(缺省 pick_max)。
    allow_repeat 区可重复(choices)否则不重复(sample)；ordered 区不排序否则升序。"""
    result = {}
    for zone in get_zones(rule_config):
        n = _pick_count(zone, picks)
        pool = list(range(zone["min"], zone["max"] + 1))
        if zone.get("allow_repeat"):
            nums = random.choices(pool, k=n)
        else:
            nums = random.sample(pool, n)
        result[zone["key"]] = nums if zone.get("ordered") else sorted(nums)
    return result


def dan_random_numbers(rule_config, dan_numbers):
    """定胆随机：锁定胆码，剩余位从未选号码池随机补全；胆码非法抛 ValueError。"""
    result = {}
    for zone in get_zones(rule_config):
        key = zone["key"]
        dans = list(dict.fromkeys(dan_numbers.get(key, [])))  # 去重保序
        count = zone["count"]
        for d in dans:
            if not (zone["min"] <= d <= zone["max"]):
                raise ValueError(f"{key} 胆码 {d} 超出范围 [{zone['min']},{zone['max']}]")
        if len(dans) > count:
            raise ValueError(f"{key} 胆码数量 {len(dans)} 超过该区号码数 {count}")
        pool = [n for n in range(zone["min"], zone["max"] + 1) if n not in dans]
        picks = dans + random.sample(pool, count - len(dans))
        result[key] = sorted(picks)
    return result
