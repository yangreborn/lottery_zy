import logging

from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils import make_response
from common.auth import code_to_openid, set_user_session

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """POST /api/user/login —— 微信 code 换 session。"""
    authentication_classes = []

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(make_response(code=1, msg="缺少 code"))
        openid = code_to_openid(code)
        if not openid:
            return Response(make_response(code=1, msg="登录失败", error="code 无效"))
        set_user_session(request, openid)
        return Response(make_response(data={"logged_in": True}))
