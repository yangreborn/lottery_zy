import logging

from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils import make_response
from common.auth import current_user_id
from stats.models import AccessLog

logger = logging.getLogger(__name__)


class LogCreateView(APIView):
    """POST /api/openapi/log —— 埋点上报(免登录)。"""
    authentication_classes = []

    def post(self, request):
        path = request.data.get("path")
        if not path:
            return Response(make_response(code=1, msg="缺少 path"))
        AccessLog.objects.create(
            user_id=current_user_id(request) or "",
            path=path,
            lottery_code=request.data.get("lottery_code", "") or "",
            action=request.data.get("action", AccessLog.ACTION_VIEW) or AccessLog.ACTION_VIEW,
        )
        return Response(make_response(data={"logged": True}))
