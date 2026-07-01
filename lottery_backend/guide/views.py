import logging

from django.db.models import Q
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils import make_response
from guide.models import PlayGuide
from guide.serializers import GuideListSerializer, GuideDetailSerializer

logger = logging.getLogger(__name__)


def _visible_qs():
    """上架且已发布(publish_at 为空或已过)的条目。"""
    now = timezone.now()
    return (PlayGuide.objects.filter(is_active=True)
            .filter(Q(publish_at__isnull=True) | Q(publish_at__lte=now)))


class GuideListView(APIView):
    """GET /api/openapi/guide/list?code=&type= —— 玩法/奖级/活动列表(不含 content)。"""

    def get(self, request):
        qs = _visible_qs()
        code = request.query_params.get("code")
        if code:
            qs = qs.filter(Q(lottery__code=code) | Q(lottery__isnull=True))
        gtype = request.query_params.get("type")
        if gtype:
            types = [t for t in gtype.split(",") if t]
            if types:
                qs = qs.filter(type__in=types)
        if request.query_params.get("important") == "1":
            qs = qs.filter(is_important=True)
        # 重点(is_important)排最前，再按人工排序、发布时间倒序
        qs = qs.order_by("-is_important", "sort", "-publish_at")
        return Response(make_response(data=GuideListSerializer(qs, many=True).data))


class GuideDetailView(APIView):
    """GET /api/openapi/guide/detail?id= —— 单条详情(含 content)。"""

    def get(self, request):
        raw_id = request.query_params.get("id")
        try:
            gid = int(raw_id)
        except (TypeError, ValueError):
            return Response(make_response(code=1, msg="参数非法", error=f"id={raw_id}"))
        guide = _visible_qs().filter(id=gid).first()
        if guide is None:
            return Response(make_response(code=1, msg="内容不存在或未发布", error=str(raw_id)))
        return Response(make_response(data=GuideDetailSerializer(guide).data))
