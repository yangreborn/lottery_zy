from rest_framework import serializers
from lottery.models import Lottery, DrawResult


class LotterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lottery
        fields = ("code", "name", "category", "rule_config", "draw_days")


class DrawResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawResult
        fields = ("issue", "draw_date", "numbers", "sales_amount",
                  "pool_amount", "prize_grades")
