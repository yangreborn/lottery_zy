from django.contrib import admin
from guide.models import PlayGuide


@admin.register(PlayGuide)
class PlayGuideAdmin(admin.ModelAdmin):
    list_display = ("title", "type", "lottery", "is_active", "sort", "publish_at")
    list_filter = ("type", "is_active", "lottery")
    search_fields = ("title", "content")
    list_editable = ("is_active", "sort")
