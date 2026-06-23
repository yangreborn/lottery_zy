import logging
import datetime
from django.core.management.base import BaseCommand
from lottery.models import Lottery, DrawResult

logger = logging.getLogger(__name__)

# 示例开奖（合理示例值，号码均符合各自 rule_config）
SAMPLES = {
    "ssq": [
        {"issue": "2026060", "draw_date": "2026-06-01",
         "numbers": {"red": [3, 8, 15, 22, 27, 31], "blue": [5]},
         "pool_amount": "1532000000",
         "prize_grades": [{"level": 1, "count": 6, "amount": "8500000"},
                          {"level": 2, "count": 120, "amount": "180000"}]},
        {"issue": "2026061", "draw_date": "2026-06-04",
         "numbers": {"red": [1, 9, 12, 20, 28, 33], "blue": [11]},
         "pool_amount": "1488000000",
         "prize_grades": [{"level": 1, "count": 4, "amount": "9200000"},
                          {"level": 2, "count": 98, "amount": "210000"}]},
        {"issue": "2026062", "draw_date": "2026-06-06",
         "numbers": {"red": [6, 11, 17, 24, 29, 32], "blue": [2]},
         "pool_amount": "1605000000",
         "prize_grades": [{"level": 1, "count": 7, "amount": "7800000"},
                          {"level": 2, "count": 130, "amount": "165000"}]},
    ],
    "dlt": [
        {"issue": "2026060", "draw_date": "2026-06-02",
         "numbers": {"red": [4, 13, 21, 28, 34], "blue": [3, 9]},
         "pool_amount": "980000000",
         "prize_grades": [{"level": 1, "count": 3, "amount": "10000000"},
                          {"level": 2, "count": 50, "amount": "250000"}]},
        {"issue": "2026061", "draw_date": "2026-06-04",
         "numbers": {"red": [7, 16, 22, 30, 35], "blue": [1, 12]},
         "pool_amount": "1020000000",
         "prize_grades": [{"level": 1, "count": 2, "amount": "11000000"},
                          {"level": 2, "count": 44, "amount": "270000"}]},
        {"issue": "2026062", "draw_date": "2026-06-07",
         "numbers": {"red": [2, 10, 19, 26, 33], "blue": [5, 8]},
         "pool_amount": "1055000000",
         "prize_grades": [{"level": 1, "count": 5, "amount": "9000000"},
                          {"level": 2, "count": 61, "amount": "230000"}]},
    ],
}


class Command(BaseCommand):
    help = "插入双色球/大乐透示例已发布开奖（开发演示用，幂等）"

    def handle(self, *args, **options):
        for code, draws in SAMPLES.items():
            lottery = Lottery.objects.filter(code=code).first()
            if lottery is None:
                logger.warning("彩种 %s 不存在，先跑 seed_lotteries", code)
                continue
            for d in draws:
                obj, created = DrawResult.objects.update_or_create(
                    lottery=lottery, issue=d["issue"],
                    defaults={
                        "draw_date": datetime.date.fromisoformat(d["draw_date"]),
                        "numbers": d["numbers"],
                        "pool_amount": d["pool_amount"],
                        "prize_grades": d["prize_grades"],
                        "source": DrawResult.SOURCE_MANUAL,
                        "status": DrawResult.STATUS_PUBLISHED,
                    },
                )
                logger.info("sample draw %s %s %s", code, d["issue"],
                            "created" if created else "updated")
