def validate_numbers(rule_config, numbers):
    """按 rule_config 校验 numbers，返回错误信息列表，空列表=合法。"""
    if not isinstance(numbers, dict):
        return ["号码格式应为字典"]
    errors = []
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        nums = numbers.get(zone, [])
        if not isinstance(nums, list):
            errors.append(f"{zone} 号码格式应为列表")
            continue
        if len(nums) != rule["count"]:
            errors.append(f"{zone} 号码个数应为 {rule['count']}，实际 {len(nums)}")
        if len(set(nums)) != len(nums):
            errors.append(f"{zone} 号码有重复")
        for n in nums:
            if not (rule["min"] <= n <= rule["max"]):
                errors.append(f"{zone} 号码 {n} 超出范围 [{rule['min']},{rule['max']}]")
    return errors
