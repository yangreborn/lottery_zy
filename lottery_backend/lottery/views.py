import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from common.utils import make_response
from lottery.models import Lottery
from lottery.serializers import LotterySerializer

logger = logging.getLogger(__name__)


class LotteryListView(APIView):
    """GET /api/openapi/lottery/list —— 上架彩种列表（含号码规则）。"""

    def get(self, request):
        qs = Lottery.objects.filter(is_active=True).order_by("code")
        data = LotterySerializer(qs, many=True).data
        return Response(make_response(data=data))
