import logging
from lottery.models import Lottery, DrawResult
from crawler.registry import SPIDERS
from crawler.persist import persist_draw

logger = logging.getLogger(__name__)


def poll_lottery(code):
    """抓取单个彩种最新开奖并发布(RQ 任务入口)。

    复用现有 spider 与 persist_draw；写入后置为已发布(抓到即发布)。
    幂等:persist_draw 用 update_or_create，重复抓不产生重复记录。
    任何异常只记日志、不抛出，交由下一次巡检重试。
    """
    spider_cls = SPIDERS.get(code)
    if spider_cls is None:
        logger.warning("poll_lottery 未注册彩种: %s", code)
        return
    try:
        lottery = Lottery.objects.get(code=code)
    except Lottery.DoesNotExist:
        logger.warning("poll_lottery 彩种配置不存在: %s", code)
        return
    try:
        items = spider_cls().run()
    except Exception:
        logger.error("poll_lottery 抓取 %s 失败", code, exc_info=True)
        return
    for item in items:
        try:
            obj, errors = persist_draw(lottery, item)
            if obj is not None:
                obj.status = DrawResult.STATUS_PUBLISHED
                obj.save(update_fields=["status"])
                logger.info("poll_lottery 发布 %s %s", code, item.get("issue"))
        except Exception:
            logger.error("poll_lottery persist %s %s 失败", code, item.get("issue"), exc_info=True)
