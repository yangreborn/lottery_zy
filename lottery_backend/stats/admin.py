from django.contrib import admin
from stats.models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("short_user", "path", "lottery_code", "action", "created_at")
    list_filter = ("action", "lottery_code")
    date_hierarchy = "created_at"

    def short_user(self, obj):
        return obj.user_id[:8] if obj.user_id else "(anon)"
    short_user.short_description = "用户"
