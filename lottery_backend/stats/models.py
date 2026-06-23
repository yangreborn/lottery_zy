from django.db import models


class AccessLog(models.Model):
    """访问埋点。user_id 匿名 hash(可空)；仅记路径/彩种/动作/时间。"""
    ACTION_VIEW = "view"
    ACTION_SAVE = "save_number"
    ACTION_CHECK = "check_number"

    user_id = models.CharField("用户哈希", max_length=64, blank=True, default="", db_index=True)
    path = models.CharField("路径", max_length=100)
    lottery_code = models.CharField("彩种", max_length=20, blank=True, default="")
    action = models.CharField("动作", max_length=20, default=ACTION_VIEW)
    created_at = models.DateTimeField("时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = verbose_name_plural = "访问日志"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.path}"
