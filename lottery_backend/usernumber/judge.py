from lottery.grades import grade_label


def judge_prize(rule_config, draw_numbers, user_numbers):
    """红蓝判奖：各区命中数按 prize_rules {red,blue} 匹配，取最小 level(最高奖)。"""
    red_hit = len(set(user_numbers.get("red", [])) & set(draw_numbers.get("red", [])))
    blue_hit = len(set(user_numbers.get("blue", [])) & set(draw_numbers.get("blue", [])))
    level = None
    for rule in rule_config.get("prize_rules", []):
        if rule.get("red") == red_hit and rule.get("blue") == blue_hit:
            if level is None or rule["level"] < level:
                level = rule["level"]
    label = grade_label(level) if level is not None else "未中奖"
    return {"red_hit": red_hit, "blue_hit": blue_hit, "level": level, "label": label,
            "desc": f"命中 红{red_hit} 蓝{blue_hit}"}


def judge_keno(rule_config, draw_numbers, user_numbers):
    """快乐8判奖：选 N 中 M，按 prize_rules {pick,hit} 匹配固定奖。"""
    zones = rule_config.get("zones") or []
    main_key = zones[0]["key"] if zones else "main"
    user = user_numbers.get(main_key, [])
    drawn = draw_numbers.get(main_key, [])
    pick = len(user)
    hit = len(set(user) & set(drawn))
    matched = None
    for rule in rule_config.get("prize_rules", []):
        if rule.get("pick") == pick and rule.get("hit") == hit:
            matched = rule
            break
    label = matched["label"] if matched else "未中奖"
    amount = matched.get("amount", 0) if matched else 0
    level = matched.get("level") if matched else None
    return {"hit": hit, "pick": pick, "level": level, "label": label, "amount": amount,
            "desc": f"选{pick}中{hit}"}


def judge_digit(rule_config, draw_numbers, user_numbers):
    """3D/排列三判奖：直选(完全一致)/组选(集合相同,开奖有重复=组三 否则组六)。"""
    zones = rule_config.get("zones") or []
    key = zones[0]["key"] if zones else "digits"
    user = list(user_numbers.get(key, []))
    drawn = list(draw_numbers.get(key, []))
    rules = {r.get("type"): r for r in rule_config.get("prize_rules", [])}
    matched = None
    if user and user == drawn:
        matched = rules.get("direct")
    elif user and sorted(user) == sorted(drawn):
        matched = rules.get("group3") if len(set(drawn)) < len(drawn) else rules.get("group6")
    label = matched["label"] if matched else "未中奖"
    amount = matched.get("amount", 0) if matched else 0
    hit_type = matched.get("type") if matched else None
    desc = f"{label}命中" if matched else "未中奖"
    return {"hit_type": hit_type, "label": label, "amount": amount, "desc": desc}
