from datetime import timedelta

from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate

from stats.models import AccessLog


def compute_dashboard(days=7):
    """近 days 天访问聚合：pv/uv/每日 dau/热门彩种/功能分布。"""
    since = timezone.now() - timedelta(days=days)
    qs = AccessLog.objects.filter(created_at__gte=since)

    pv = qs.count()
    uv = qs.exclude(user_id="").values("user_id").distinct().count()

    dau_rows = (qs.exclude(user_id="")
                .annotate(date=TruncDate("created_at"))
                .values("date")
                .annotate(count=Count("user_id", distinct=True))
                .order_by("-date"))
    dau = [{"date": str(r["date"]), "count": r["count"]} for r in dau_rows]

    top_lotteries = [
        {"lottery_code": r["lottery_code"], "count": r["count"]}
        for r in (qs.exclude(lottery_code="")
                  .values("lottery_code")
                  .annotate(count=Count("id"))
                  .order_by("-count"))
    ]

    actions = [
        {"action": r["action"], "count": r["count"]}
        for r in (qs.values("action").annotate(count=Count("id")).order_by("-count"))
    ]

    return {"pv": pv, "uv": uv, "dau": dau,
            "top_lotteries": top_lotteries, "actions": actions, "days": days}
