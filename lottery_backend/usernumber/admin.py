from django.contrib import admin

from usernumber.models import UserNumber, Feedback, PurchaseRecord


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "short_content", "contact", "user_id", "created_at")
    search_fields = ("content", "contact")
    readonly_fields = ("user_id", "content", "contact", "created_at")

    def short_content(self, obj):
        return obj.content[:30]
    short_content.short_description = "反馈内容"


@admin.register(UserNumber)
class UserNumberAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "lottery", "gen_type", "group_name", "created_at")
    list_filter = ("gen_type", "lottery")
    search_fields = ("user_id", "note")


@admin.register(PurchaseRecord)
class PurchaseRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "lottery", "issue", "bet_count", "purchase_date", "created_at")
    list_filter = ("lottery",)
    search_fields = ("user_id", "issue")
