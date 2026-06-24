import logging
from lottery.models import DrawResult
from lottery.validators import validate_numbers

logger = logging.getLogger(__name__)


def persist_draw(lottery, item):
    """校验 item 号码，合法则写 draft(crawler)，失败则不入库。返回 (obj|None, errors)。"""
    errors = validate_numbers(lottery.rule_config, item.get("numbers", {}), mode="draw")
    if errors:
        logger.warning("draw %s %s 校验失败，不入库: %s", lottery.code, item.get("issue"), errors)
        return None, errors
    obj, created = DrawResult.objects.update_or_create(
        lottery=lottery, issue=item["issue"],
        defaults={
            "draw_date": item["draw_date"],
            "numbers": item["numbers"],
            "sales_amount": item.get("sales_amount", ""),
            "pool_amount": item.get("pool_amount", ""),
            "prize_grades": item.get("prize_grades", []),
            "source": DrawResult.SOURCE_CRAWLER,
            "status": DrawResult.STATUS_DRAFT,
        },
    )
    logger.info("draw %s %s %s", lottery.code, item["issue"], "created" if created else "updated")
    return obj, []
