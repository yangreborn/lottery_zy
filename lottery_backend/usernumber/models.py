from django.db import models
from lottery.models import Lottery


class UserNumber(models.Model):
    """用户记录的号码。user_id 存 hash，不暴露真实 openid。"""
    GEN_MANUAL = "manual"
    GEN_RANDOM = "random"
    GEN_DAN = "dan_random"
    GEN_CHOICES = [(GEN_MANUAL, "手动"), (GEN_RANDOM, "机选"), (GEN_DAN, "定胆随机")]

    user_id = models.CharField("用户哈希", max_length=64, db_index=True)
    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE,
                                related_name="user_numbers", verbose_name="彩种")
    numbers = models.JSONField("号码", default=dict)
    gen_type = models.CharField("生成方式", max_length=12, choices=GEN_CHOICES, default=GEN_MANUAL)
    dan_numbers = models.JSONField("胆码", default=dict, blank=True)
    note = models.CharField("备注", max_length=100, blank=True, default="")
    target_issue = models.CharField("目标期号", max_length=20, blank=True, default="")
    group_name = models.CharField("分组", max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户号码"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id[:8]} {self.lottery.code}"


class Feedback(models.Model):
    """用户反馈。user_id 存 hash，匿名时为空串。"""
    user_id = models.CharField("用户哈希", max_length=64, blank=True, default="", db_index=True)
    content = models.TextField("反馈内容")
    contact = models.CharField("联系方式", max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户反馈"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id[:8] or '匿名'} {self.content[:20]}"


class PurchaseRecord(models.Model):
    """用户实际购买记录，独立于 UserNumber(只选不买)。"""
    user_id = models.CharField("用户哈希", max_length=64, db_index=True)
    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE,
                                related_name="purchases", verbose_name="彩种")
    issue = models.CharField("期号", max_length=20)
    numbers = models.JSONField("号码", default=dict)
    bet_count = models.PositiveIntegerField("注数", default=1)
    purchase_date = models.DateField("购买日期")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "购买记录"
        ordering = ["-purchase_date", "-created_at"]

    def __str__(self):
        return f"{self.user_id[:8]} {self.lottery.code} {self.issue}"


class AppUser(models.Model):
    """登录用户档案。user_id 是 openid 的 hash(对外标识)，openid 仅后台留存。"""
    user_id = models.CharField("用户哈希", max_length=64, unique=True, db_index=True)
    openid = models.CharField("openid", max_length=128, unique=True)
    unionid = models.CharField("unionid", max_length=128, blank=True, default="", db_index=True)
    nickname = models.CharField("昵称", max_length=30, blank=True, default="")
    home_lotteries = models.JSONField("首页彩种", default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户"
        ordering = ["-created_at"]

    @property
    def short_id(self):
        return self.user_id[:8]

    def __str__(self):
        return f"#{self.id} {self.nickname or self.short_id}"


def get_or_create_app_user(user_id, openid):
    user, _ = AppUser.objects.get_or_create(user_id=user_id, defaults={"openid": openid})
    return user
