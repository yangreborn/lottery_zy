_CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
           6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}


def grade_label(level):
    """奖级文字归一: int → 中文序号奖级; str → 原样返回。"""
    if isinstance(level, bool):  # bool 是 int 子类, 单独挡掉
        return str(level)
    if isinstance(level, int):
        return f"{_CN_NUM.get(level, str(level))}等奖"
    return str(level)
