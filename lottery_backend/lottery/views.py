import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from common.utils import make_response
from lottery.models import Lottery, DrawResult
from lottery.serializers import LotterySerializer, DrawResultSerializer, DrawDetailSerializer
from lottery.pagination import parse_page_params, paginate

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


class DrawHistoryView(APIView):
    """GET /api/openapi/draw/history —— 历史开奖, 倒序, 分页, 可按日期区间筛选。"""

    def get(self, request):
        code = request.query_params.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        qs = (DrawResult.objects
              .filter(lottery=lottery, status=DrawResult.STATUS_PUBLISHED)
              .order_by("-draw_date", "-issue"))
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(draw_date__gte=date_from)
        if date_to:
            qs = qs.filter(draw_date__lte=date_to)
        page, page_size = parse_page_params(request.query_params)
        items, total = paginate(qs, page, page_size)
        return Response(make_response(data={
            "results": DrawResultSerializer(items, many=True).data,
            "total": total, "page": page, "page_size": page_size,
        }))


class DrawDetailView(APIView):
    """GET /api/openapi/draw/detail?code=ssq&issue=2026073 —— 单期详情(含奖级文字)。"""

    def get(self, request):
        code = request.query_params.get("code")
        issue = request.query_params.get("issue")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        draw = (DrawResult.objects
                .filter(lottery=lottery, issue=issue,
                        status=DrawResult.STATUS_PUBLISHED).first())
        if draw is None:
            return Response(make_response(code=1, msg="期号不存在或未发布", error=str(issue)))
        return Response(make_response(data=DrawDetailSerializer(draw).data))
