import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery, DrawResult
from crawler.registry import SPIDERS
from crawler.persist import persist_draw

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "抓取最近 N 期真实开奖并发布(bootstrap 历史数据)。--count 期数 --code 彩种(缺省全部)。"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=160)
        parser.add_argument("--code", default=None)

    def handle(self, *args, **options):
        count = options["count"]
        codes = [options["code"]] if options["code"] else list(SPIDERS.keys())
        for code in codes:
            spider_cls = SPIDERS.get(code)
            if spider_cls is None:
                logger.warning("未注册的彩种: %s", code)
                continue
            try:
                lottery = Lottery.objects.get(code=code)
            except Lottery.DoesNotExist:
                logger.warning("彩种配置不存在，请先 seed_lotteries: %s", code)
                continue
            try:
                items = spider_cls().run(count)
            except Exception:
                logger.error("抓取 %s 失败", code, exc_info=True)
                continue
            published = 0
            for item in items:
                try:
                    obj, errors = persist_draw(lottery, item)
                    if obj is not None:
                        obj.status = DrawResult.STATUS_PUBLISHED
                        obj.save(update_fields=["status"])
                        published += 1
                except Exception:
                    logger.error("persist %s %s 失败", code, item.get("issue"), exc_info=True)
            logger.info("load_history %s 发布 %d 期", code, published)
