from lottery.zones import get_zones


def validate_numbers(rule_config, numbers, mode="pick"):
    """按 rule_config 校验 numbers，返回错误信息列表，空列表=合法。
    mode='draw' 校验开奖号(个数==count)；mode='pick' 校验用户选号(可变区用 pick_min/pick_max)。"""
    if not isinstance(numbers, dict):
        return ["号码格式应为字典"]
    errors = []
    for zone in get_zones(rule_config):
        key = zone["key"]
        nums = numbers.get(key, [])
        if not isinstance(nums, list):
            errors.append(f"{key} 号码格式应为列表")
            continue
        if mode == "pick" and "pick_min" in zone and "pick_max" in zone:
            if not (zone["pick_min"] <= len(nums) <= zone["pick_max"]):
                errors.append(f"{key} 选号个数应为 {zone['pick_min']}-{zone['pick_max']}，实际 {len(nums)}")
        elif len(nums) != zone["count"]:
            errors.append(f"{key} 号码个数应为 {zone['count']}，实际 {len(nums)}")
        if not zone.get("allow_repeat") and len(set(nums)) != len(nums):
            errors.append(f"{key} 号码有重复")
        for n in nums:
            if not (zone["min"] <= n <= zone["max"]):
                errors.append(f"{key} 号码 {n} 超出范围 [{zone['min']},{zone['max']}]")
    return errors
