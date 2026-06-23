import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery
from guide.models import PlayGuide

logger = logging.getLogger(__name__)

GUIDES = [
    {"code": "ssq", "type": PlayGuide.TYPE_INTRO, "title": "双色球玩法说明", "sort": 1,
     "content": "<p>双色球每注由 6 个红球(1-33)和 1 个蓝球(1-16)组成。</p>"},
    {"code": "ssq", "type": PlayGuide.TYPE_RULE, "title": "双色球奖级规则", "sort": 2,
     "content": "<p>一等奖：6 红 + 1 蓝。</p><p>二等奖：命中 6 红。</p>"},
    {"code": "dlt", "type": PlayGuide.TYPE_INTRO, "title": "大乐透玩法说明", "sort": 1,
     "content": "<p>超级大乐透每注由 5 个前区号(1-35)和 2 个后区号(1-12)组成。</p>"},
    {"code": "dlt", "type": PlayGuide.TYPE_RULE, "title": "大乐透奖级规则", "sort": 2,
     "content": "<p>一等奖：5 前区 + 2 后区。</p>"},
    {"code": None, "type": PlayGuide.TYPE_ACTIVITY, "title": "平台公告", "sort": 1,
     "content": "<p>本平台仅提供开奖查询与号码记录，所有功能免费。</p>"},
]


class Command(BaseCommand):
    help = "插入示例玩法/奖级/活动内容（开发演示用，幂等）"

    def handle(self, *args, **options):
        for g in GUIDES:
            lottery = Lottery.objects.filter(code=g["code"]).first() if g["code"] else None
            obj, created = PlayGuide.objects.update_or_create(
                title=g["title"], type=g["type"],
                defaults={"lottery": lottery, "sort": g["sort"],
                          "content": g["content"], "is_active": True},
            )
            logger.info("seed guide %s %s", g["title"], "created" if created else "updated")
