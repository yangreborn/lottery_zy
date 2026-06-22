import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery
from crawler.registry import SPIDERS
from crawler.persist import persist_draw

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "抓取开奖数据并写入 draft。--code 指定彩种，缺省抓全部。"

    def add_arguments(self, parser):
        parser.add_argument("--code", default=None)

    def handle(self, *args, **options):
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
                items = spider_cls().run()
            except Exception:
                logger.error("抓取 %s 失败", code, exc_info=True)
                continue
            for item in items:
                persist_draw(lottery, item)
