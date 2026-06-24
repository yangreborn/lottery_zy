from rest_framework import serializers
from lottery.models import Lottery, DrawResult
from lottery.grades import grade_label


class LotterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lottery
        fields = ("code", "name", "category", "rule_config", "draw_days")


class DrawResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawResult
        fields = ("issue", "draw_date", "numbers", "sales_amount",
                  "pool_amount", "prize_grades", "prize_area")


class DrawDetailSerializer(DrawResultSerializer):
    prize_grades = serializers.SerializerMethodField()

    def get_prize_grades(self, obj):
        return [{**g, "level_label": grade_label(g.get("level"))}
                for g in (obj.prize_grades or [])]
