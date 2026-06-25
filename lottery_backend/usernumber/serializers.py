from rest_framework import serializers
from usernumber.models import UserNumber, PurchaseRecord


class UserNumberSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="lottery.code", read_only=True)

    class Meta:
        model = UserNumber
        fields = ["id", "code", "numbers", "gen_type", "dan_numbers",
                  "note", "target_issue", "group_name", "created_at"]


class PurchaseRecordSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="lottery.code", read_only=True)

    class Meta:
        model = PurchaseRecord
        fields = ["id", "code", "issue", "numbers", "bet_count", "purchase_date", "created_at"]
