import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from common.utils import make_response
from lottery.models import Lottery, DrawResult
from lottery.serializers import LotterySerializer, DrawResultSerializer

logger = logging.getLogger(__name__)


def _get_active_lottery(code):
    """按 code 取上架彩种, 不存在返回 None。"""
    if not code:
        return None
    return Lottery.objects.filter(code=code, is_active=True).first()


class DrawLatestView(APIView):
    """GET /api/openapi/draw/latest?code=ssq —— 最新一期已发布开奖。"""

    def get(self, request):
        code = request.query_params.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        draw = (DrawResult.objects
                .filter(lottery=lottery, status=DrawResult.STATUS_PUBLISHED)
                .order_by("-draw_date", "-issue").first())
        if draw is None:
            return Response(make_response(code=1, msg="暂无开奖数据", error=code))
        return Response(make_response(data=DrawResultSerializer(draw).data))


class LotteryListView(APIView):
    """GET /api/openapi/lottery/list —— 上架彩种列表（含号码规则）。"""

    def get(self, request):
        qs = Lottery.objects.filter(is_active=True).order_by("code")
        data = LotterySerializer(qs, many=True).data
        return Response(make_response(data=data))
