_LEGACY_LABELS = {"red": "红球", "blue": "蓝球"}


def get_zones(rule_config):
    """返回标准化区列表 [{key,label,min,max,count,...}]。
    新格式直读 rule_config['zones']；老格式(red/blue 顶层键)自动转换。"""
    zones = rule_config.get("zones")
    if isinstance(zones, list):
        return zones
    result = []
    for key in ("red", "blue"):
        rule = rule_config.get(key)
        if rule is None:
            continue
        zone = dict(rule)
        zone["key"] = key
        zone.setdefault("label", _LEGACY_LABELS[key])
        result.append(zone)
    return result
