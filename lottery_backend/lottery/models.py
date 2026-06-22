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
