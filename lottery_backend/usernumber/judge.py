from lottery.grades import grade_label


def judge_prize(rule_config, draw_numbers, user_numbers):
    """按 rule_config["prize_rules"] 判定中奖等级。命中多条取最小 level(最高奖)。"""
    red_hit = len(set(user_numbers.get("red", [])) & set(draw_numbers.get("red", [])))
    blue_hit = len(set(user_numbers.get("blue", [])) & set(draw_numbers.get("blue", [])))
    level = None
    for rule in rule_config.get("prize_rules", []):
        if rule.get("red") == red_hit and rule.get("blue") == blue_hit:
            if level is None or rule["level"] < level:
                level = rule["level"]
    label = grade_label(level) if level is not None else "未中奖"
    return {"red_hit": red_hit, "blue_hit": blue_hit, "level": level, "label": label}
