from django.contrib import admin

from usernumber.models import UserNumber, Feedback, PurchaseRecord, AppUser


@admin.register(AppUser)
class AppUserAdmin(admin.ModelAdmin):
    list_display = ("id", "nickname", "short_id", "openid", "created_at")
    search_fields = ("nickname", "user_id", "openid")
    readonly_fields = ("user_id", "openid", "created_at", "updated_at")

    def short_id(self, obj):
        return obj.short_id
    short_id.short_description = "短ID"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "short_content", "contact", "short_uid", "created_at")
    search_fields = ("content", "contact", "user_id")
    readonly_fields = ("user_id", "content", "contact", "created_at")

    def short_content(self, obj):
        return obj.content[:30]
    short_content.short_description = "反馈内容"

    def short_uid(self, obj):
        return obj.user_id[:8] or "匿名"
    short_uid.short_description = "用户"


@admin.register(UserNumber)
class UserNumberAdmin(admin.ModelAdmin):
    list_display = ("id", "short_uid", "lottery", "gen_type", "group_name", "created_at")
    list_filter = ("gen_type", "lottery")
    search_fields = ("user_id", "note")

    def short_uid(self, obj):
        return obj.user_id[:8]
    short_uid.short_description = "用户"


@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "short_uid", "lottery", "issue", "bet_count", "purchase_date", "created_at")
    list_filter = ("lottery",)
    search_fields = ("user_id", "issue")

    def short_uid(self, obj):
        return obj.user_id[:8]
    short_uid.short_description = "用户"
