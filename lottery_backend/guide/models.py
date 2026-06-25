from django.db import models
from lottery.models import Lottery


class PlayGuide(models.Model):
    """玩法说明 / 奖级规则 / 活动公告。lottery 为空 = 通用。"""
    TYPE_INTRO = "intro"
    TYPE_RULE = "rule"
    TYPE_ACTIVITY = "activity"
    TYPE_NOTICE = "notice"
    TYPE_CHOICES = [(TYPE_INTRO, "玩法说明"), (TYPE_RULE, "奖级规则"),
                    (TYPE_ACTIVITY, "活动公告"), (TYPE_NOTICE, "通知公告")]

    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE, null=True, blank=True,
                                related_name="guides", verbose_name="彩种")
    type = models.CharField("类型", max_length=12, choices=TYPE_CHOICES, default=TYPE_INTRO)
    title = models.CharField("标题", max_length=100)
    content = models.TextField("内容", blank=True, default="")
    sort = models.IntegerField("排序", default=0)
    is_active = models.BooleanField("是否上架", default=True)
    is_important = models.BooleanField("重要通知", default=False)
    publish_at = models.DateTimeField("发布时间", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "玩法说明"
        ordering = ["sort", "-publish_at"]

    def __str__(self):
        return f"{self.get_type_display()} {self.title}"
