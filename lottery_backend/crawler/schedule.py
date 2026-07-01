import logging
from django.conf import settings
from lottery.models import Lottery, DrawResult

logger = logging.getLogger(__name__)


def _minutes(hhmm):
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def due_codes(now):
    """返回当前应入队抓取的彩种 code 列表。

    命中条件(全部满足):
      - 今天是该彩种开奖日(isoweekday 在 draw_days 内)
      - 当前在 [draw_time, draw_time + POLL_WINDOW_MINUTES] 窗口内
      - 该彩种今日尚无「已发布」开奖记录
    now 为本地时间 datetime(naive/aware 均可)。
    """
    today = now.date()
    weekday = now.isoweekday()
    now_min = now.hour * 60 + now.minute
    window = settings.POLL_WINDOW_MINUTES
    codes = []
    for lot in Lottery.objects.filter(is_active=True).exclude(draw_time=""):
        if weekday not in (lot.draw_days or []):
            continue
        try:
            start = _minutes(lot.draw_time)
        except (ValueError, AttributeError):
            logger.warning("彩种 %s draw_time 非法: %r", lot.code, lot.draw_time)
            continue
        if not (start <= now_min <= start + window):
            continue
        if DrawResult.objects.filter(
            lottery=lot, status=DrawResult.STATUS_PUBLISHED, draw_date=today
        ).exists():
            continue
        codes.append(lot.code)
    return codes


def dispatch_due_polls():
    """rqscheduler 每分钟触发:把当前应抓的彩种入队到 default 队列。"""
    import django_rq
    from django.utils import timezone
    from crawler.tasks import poll_lottery

    q = django_rq.get_queue("default")
    for code in due_codes(timezone.localtime()):
        q.enqueue(poll_lottery, code)
        logger.info("dispatch 入队抓取 %s", code)
