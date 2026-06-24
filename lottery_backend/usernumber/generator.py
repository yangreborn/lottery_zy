import random
from lottery.zones import get_zones


def _pick_count(zone, picks):
    if "pick_min" in zone and "pick_max" in zone:
        n = (picks or {}).get(zone["key"], zone["pick_max"])
        return max(zone["pick_min"], min(n, zone["pick_max"]))
    return zone["count"]


def random_numbers(rule_config, picks=None):
    """按 rule_config 机选，每区取若干不重复号码升序返回。
    picks: 可选 {zone_key: n}，指定可变区(pick_min/pick_max)选几;缺省取 pick_max。固定区用 count。"""
    result = {}
    for zone in get_zones(rule_config):
        n = _pick_count(zone, picks)
        result[zone["key"]] = sorted(random.sample(range(zone["min"], zone["max"] + 1), n))
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
