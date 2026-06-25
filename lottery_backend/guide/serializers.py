from rest_framework import serializers
from guide.models import PlayGuide


class GuideListSerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = PlayGuide
        fields = ["id", "type", "type_label", "title", "sort", "publish_at", "is_important"]


class GuideDetailSerializer(serializers.ModelSerializer):
    type_label = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = PlayGuide
        fields = ["id", "type", "type_label", "title", "content", "sort", "publish_at", "is_important"]
