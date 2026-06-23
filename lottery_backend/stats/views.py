import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils import make_response
from common.auth import current_user_id
from stats.aggregate import compute_dashboard
from stats.models import AccessLog

logger = logging.getLogger(__name__)


class LogCreateView(APIView):
    """POST /api/openapi/log —— 埋点上报(免登录)。"""
    authentication_classes = []

    def post(self, request):
        path = request.data.get("path")
        if not path:
            return Response(make_response(code=1, msg="缺少 path"))
        try:
            with transaction.atomic():
                AccessLog.objects.create(
                    user_id=current_user_id(request) or "",
                    path=path,
                    lottery_code=request.data.get("lottery_code", "") or "",
                    action=request.data.get("action", AccessLog.ACTION_VIEW) or AccessLog.ACTION_VIEW,
                )
        except Exception:
            logger.error("埋点写入失败", exc_info=True)
            return Response(make_response(code=1, msg="记录失败"))
        return Response(make_response(data={"logged": True}))


@staff_member_required
def dashboard_view(request):
    """GET /dashboard/ —— staff 运营看板(服务端渲染)。"""
    data = compute_dashboard(7)
    return render(request, "stats/dashboard.html", {"data": data})
