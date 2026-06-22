import logging
from django.contrib import admin
from lottery.models import Lottery, DrawResult

logger = logging.getLogger(__name__)


@admin.register(Lottery)
class LotteryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("code", "name")


@admin.register(DrawResult)
class DrawResultAdmin(admin.ModelAdmin):
    list_display = ("lottery", "issue", "draw_date", "status", "source", "pool_amount")
    list_filter = ("lottery", "status", "source")
    search_fields = ("issue",)
    actions = ["publish_selected"]

    @admin.action(description="发布选中开奖记录")
    def publish_selected(self, request, queryset):
        username = getattr(getattr(request, "user", None), "username", "admin")
        updated = queryset.update(status=DrawResult.STATUS_PUBLISHED, updated_by=username)
        logger.info("published %s draw results by %s", updated, username)
