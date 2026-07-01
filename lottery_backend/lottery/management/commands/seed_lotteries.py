import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery

logger = logging.getLogger(__name__)

# 快乐8 选N中M 固定奖金表(官方)
KENO_PRIZES = [
    {"pick": 1, "hit": 1, "amount": 4.6, "label": "选一中一"},
    {"pick": 2, "hit": 2, "amount": 19, "label": "选二中二"},
    {"pick": 3, "hit": 3, "amount": 53, "label": "选三中三"},
    {"pick": 3, "hit": 2, "amount": 3, "label": "选三中二"},
    {"pick": 4, "hit": 4, "amount": 100, "label": "选四中四"},
    {"pick": 4, "hit": 3, "amount": 5, "label": "选四中三"},
    {"pick": 4, "hit": 2, "amount": 3, "label": "选四中二"},
    {"pick": 5, "hit": 5, "amount": 1000, "label": "选五中五"},
    {"pick": 5, "hit": 4, "amount": 21, "label": "选五中四"},
    {"pick": 5, "hit": 3, "amount": 3, "label": "选五中三"},
    {"pick": 6, "hit": 6, "amount": 3000, "label": "选六中六"},
    {"pick": 6, "hit": 5, "amount": 30, "label": "选六中五"},
    {"pick": 6, "hit": 4, "amount": 10, "label": "选六中四"},
    {"pick": 6, "hit": 3, "amount": 3, "label": "选六中三"},
    {"pick": 7, "hit": 7, "amount": 10000, "label": "选七中七"},
    {"pick": 7, "hit": 6, "amount": 288, "label": "选七中六"},
    {"pick": 7, "hit": 5, "amount": 28, "label": "选七中五"},
    {"pick": 7, "hit": 4, "amount": 4, "label": "选七中四"},
    {"pick": 7, "hit": 0, "amount": 2, "label": "选七中零"},
    {"pick": 8, "hit": 8, "amount": 50000, "label": "选八中八"},
    {"pick": 8, "hit": 7, "amount": 800, "label": "选八中七"},
    {"pick": 8, "hit": 6, "amount": 88, "label": "选八中六"},
    {"pick": 8, "hit": 5, "amount": 10, "label": "选八中五"},
    {"pick": 8, "hit": 4, "amount": 3, "label": "选八中四"},
    {"pick": 8, "hit": 0, "amount": 2, "label": "选八中零"},
    {"pick": 9, "hit": 9, "amount": 300000, "label": "选九中九"},
    {"pick": 9, "hit": 8, "amount": 2000, "label": "选九中八"},
    {"pick": 9, "hit": 7, "amount": 200, "label": "选九中七"},
    {"pick": 9, "hit": 6, "amount": 20, "label": "选九中六"},
    {"pick": 9, "hit": 5, "amount": 5, "label": "选九中五"},
    {"pick": 9, "hit": 4, "amount": 3, "label": "选九中四"},
    {"pick": 9, "hit": 0, "amount": 2, "label": "选九中零"},
    {"pick": 10, "hit": 10, "amount": 5000000, "label": "选十中十"},
    {"pick": 10, "hit": 9, "amount": 8000, "label": "选十中九"},
    {"pick": 10, "hit": 8, "amount": 800, "label": "选十中八"},
    {"pick": 10, "hit": 7, "amount": 80, "label": "选十中七"},
    {"pick": 10, "hit": 6, "amount": 5, "label": "选十中六"},
    {"pick": 10, "hit": 5, "amount": 3, "label": "选十中五"},
    {"pick": 10, "hit": 0, "amount": 2, "label": "选十中零"},
]

DIGIT_PRIZES = [
    {"type": "direct", "amount": 1040, "label": "直选"},
    {"type": "group3", "amount": 346, "label": "组选三"},
    {"type": "group6", "amount": 173, "label": "组选六"},
]

DIGIT_ZONE = {"key": "digits", "label": "数字", "min": 0, "max": 9, "count": 3,
              "ordered": True, "allow_repeat": True, "color": "#43a047"}

SEEDS = [
    {
        "code": "ssq", "name": "双色球", "category": "福彩",
        "rule_config": {
            "zones": [
                {"key": "red", "label": "红球", "min": 1, "max": 33, "count": 6, "color": "#e53935"},
                {"key": "blue", "label": "蓝球", "min": 1, "max": 16, "count": 1, "color": "#1e88e5"},
            ],
            "prize_rules": [
                {"level": 1, "red": 6, "blue": 1}, {"level": 2, "red": 6, "blue": 0},
                {"level": 3, "red": 5, "blue": 1}, {"level": 4, "red": 5, "blue": 0},
                {"level": 4, "red": 4, "blue": 1}, {"level": 5, "red": 4, "blue": 0},
                {"level": 5, "red": 3, "blue": 1}, {"level": 6, "red": 2, "blue": 1},
                {"level": 6, "red": 1, "blue": 1}, {"level": 6, "red": 0, "blue": 1},
            ],
        },
        "draw_days": [2, 4, 7],
        "draw_time": "21:15",
    },
    {
        "code": "dlt", "name": "超级大乐透", "category": "体彩",
        "rule_config": {
            "zones": [
                {"key": "red", "label": "前区", "min": 1, "max": 35, "count": 5, "color": "#e53935"},
                {"key": "blue", "label": "后区", "min": 1, "max": 12, "count": 2, "color": "#1e88e5"},
            ],
            "prize_rules": [
                {"level": 1, "red": 5, "blue": 2}, {"level": 2, "red": 5, "blue": 1},
                {"level": 3, "red": 5, "blue": 0}, {"level": 4, "red": 4, "blue": 2},
                {"level": 5, "red": 4, "blue": 1}, {"level": 6, "red": 3, "blue": 2},
                {"level": 7, "red": 4, "blue": 0}, {"level": 8, "red": 3, "blue": 1},
                {"level": 8, "red": 2, "blue": 2}, {"level": 9, "red": 3, "blue": 0},
                {"level": 9, "red": 1, "blue": 2}, {"level": 9, "red": 2, "blue": 1},
                {"level": 9, "red": 0, "blue": 2},
            ],
        },
        "draw_days": [1, 3, 6],
        "draw_time": "21:25",
    },
    {
        "code": "kl8", "name": "快乐8", "category": "福彩",
        "rule_config": {
            "play_type": "keno",
            "zones": [
                {"key": "main", "label": "号码", "min": 1, "max": 80, "count": 20,
                 "pick_min": 1, "pick_max": 10, "color": "#fb8c00"},
            ],
            "prize_rules": KENO_PRIZES,
        },
        "draw_days": [1, 2, 3, 4, 5, 6, 7],
        "draw_time": "21:30",
    },
    {
        "code": "3d", "name": "福彩3D", "category": "福彩",
        "rule_config": {"play_type": "digit", "zones": [DIGIT_ZONE], "prize_rules": DIGIT_PRIZES},
        "draw_days": [1, 2, 3, 4, 5, 6, 7],
        "draw_time": "20:30",
    },
    {
        "code": "pl3", "name": "排列三", "category": "体彩",
        "rule_config": {"play_type": "digit", "zones": [DIGIT_ZONE], "prize_rules": DIGIT_PRIZES},
        "draw_days": [1, 2, 3, 4, 5, 6, 7],
        "draw_time": "20:30",
    },
]


class Command(BaseCommand):
    help = "插入/更新双色球、大乐透、快乐8 彩种配置(zones 格式)"

    def handle(self, *args, **options):
        for s in SEEDS:
            defaults = {k: v for k, v in s.items() if k != "code"}
            obj, created = Lottery.objects.update_or_create(code=s["code"], defaults=defaults)
            logger.info("seed lottery %s %s", s["code"], "created" if created else "updated")
