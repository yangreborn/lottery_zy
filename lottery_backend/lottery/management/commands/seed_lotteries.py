import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery

logger = logging.getLogger(__name__)

SEEDS = [
    {
        "code": "ssq", "name": "双色球", "category": "福彩",
        "rule_config": {"red": {"count": 6, "min": 1, "max": 33},
                        "blue": {"count": 1, "min": 1, "max": 16}},
        "draw_days": [2, 4, 7],
    },
    {
        "code": "dlt", "name": "超级大乐透", "category": "体彩",
        "rule_config": {"red": {"count": 5, "min": 1, "max": 35},
                        "blue": {"count": 2, "min": 1, "max": 12}},
        "draw_days": [1, 3, 6],
    },
]


class Command(BaseCommand):
    help = "插入/更新双色球、大乐透彩种配置"

    def handle(self, *args, **options):
        for s in SEEDS:
            defaults = {k: v for k, v in s.items() if k != "code"}
            obj, created = Lottery.objects.update_or_create(code=s["code"], defaults=defaults)
            logger.info("seed lottery %s %s", s["code"], "created" if created else "updated")
