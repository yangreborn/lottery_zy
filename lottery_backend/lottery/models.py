from django.db import models


class Lottery(models.Model):
    """彩种配置。号码区规则放 rule_config，加新彩种只插一条数据。"""
    CATEGORY_CHOICES = [("福彩", "福彩"), ("体彩", "体彩")]

    code = models.CharField("彩种标识", max_length=20, unique=True)
    name = models.CharField("名称", max_length=50)
    category = models.CharField("类别", max_length=10, choices=CATEGORY_CHOICES)
    rule_config = models.JSONField("号码规则", default=dict)
    draw_days = models.JSONField("开奖星期", default=list)
    is_active = models.BooleanField("是否上架", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "彩种"

    def __str__(self):
        return f"{self.name}({self.code})"


class DrawResult(models.Model):
    SOURCE_CRAWLER = "crawler"
    SOURCE_MANUAL = "manual"
    SOURCE_CHOICES = [(SOURCE_CRAWLER, "爬虫"), (SOURCE_MANUAL, "人工")]

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [(STATUS_DRAFT, "草稿"), (STATUS_PUBLISHED, "已发布")]

    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE, related_name="draws", verbose_name="彩种")
    issue = models.CharField("期号", max_length=20)
    draw_date = models.DateField("开奖日期")
    numbers = models.JSONField("开奖号码", default=dict)
    sales_amount = models.CharField("销售额", max_length=30, blank=True, default="")
    pool_amount = models.CharField("奖池金额", max_length=30, blank=True, default="")
    prize_grades = models.JSONField("各奖级", default=list)
    prize_area = models.TextField("一等奖分省", blank=True, default="")
    source = models.CharField("来源", max_length=10, choices=SOURCE_CHOICES, default=SOURCE_CRAWLER)
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    updated_by = models.CharField("最后修改人", max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "开奖结果"
        unique_together = ("lottery", "issue")
        ordering = ["-draw_date", "-issue"]

    def __str__(self):
        return f"{self.lottery.code} {self.issue}"
