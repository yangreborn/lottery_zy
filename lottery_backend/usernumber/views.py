import logging

from rest_framework.views import APIView
from rest_framework.response import Response

from common.utils import make_response
from common.auth import code_to_openid, set_user_session, current_user_id
from lottery.views import _get_active_lottery
from lottery.validators import validate_numbers
from usernumber.models import UserNumber
from usernumber.generator import random_numbers, dan_random_numbers
from usernumber.serializers import UserNumberSerializer
from lottery.models import DrawResult
from usernumber.judge import judge_prize, judge_keno, judge_digit

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
        uid = set_user_session(request, openid)
        return Response(make_response(data={"logged_in": True, "token": uid}))


class NumberCreateView(APIView):
    """POST /api/user/number/create —— 保存一注号码(手动/机选/定胆随机)。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        code = request.data.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        gen_type = request.data.get("gen_type", UserNumber.GEN_MANUAL)
        dan_numbers = request.data.get("dan_numbers") or {}
        if not isinstance(dan_numbers, dict):
            return Response(make_response(code=1, msg="胆码非法", error="dan_numbers 应为字典格式"))
        if gen_type == UserNumber.GEN_RANDOM:
            provided = request.data.get("numbers")
            if provided:
                numbers = provided
                errors = validate_numbers(lottery.rule_config, numbers)
                if errors:
                    return Response(make_response(code=1, msg="号码非法", error="; ".join(errors)))
            else:
                numbers = random_numbers(lottery.rule_config)
        elif gen_type == UserNumber.GEN_DAN:
            try:
                numbers = dan_random_numbers(lottery.rule_config, dan_numbers)
            except ValueError as e:
                return Response(make_response(code=1, msg="胆码非法", error=str(e)))
        else:
            gen_type = UserNumber.GEN_MANUAL
            numbers = request.data.get("numbers") or {}
            errors = validate_numbers(lottery.rule_config, numbers)
            if errors:
                return Response(make_response(code=1, msg="号码非法", error="; ".join(errors)))
        rec = UserNumber.objects.create(
            user_id=uid, lottery=lottery, numbers=numbers, gen_type=gen_type,
            dan_numbers=dan_numbers if gen_type == UserNumber.GEN_DAN else {},
            note=request.data.get("note", "") or "",
            target_issue=request.data.get("target_issue", "") or "",
        )
        return Response(make_response(data=UserNumberSerializer(rec).data))


class NumberListView(APIView):
    """GET /api/user/number/list?code= —— 当前用户的号码记录。"""
    authentication_classes = []

    def get(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        qs = UserNumber.objects.filter(user_id=uid)
        code = request.query_params.get("code")
        if code:
            qs = qs.filter(lottery__code=code)
        return Response(make_response(data=UserNumberSerializer(qs, many=True).data))


class NumberDeleteView(APIView):
    """DELETE /api/user/number/<id> —— 删除自己的记录。"""
    authentication_classes = []

    def delete(self, request, pk):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        rec = UserNumber.objects.filter(id=pk, user_id=uid).first()
        if rec is None:
            return Response(make_response(code=1, msg="记录不存在"))
        rec.delete()
        return Response(make_response(data={"deleted": True}))


class NumberCheckView(APIView):
    """GET /api/user/number/check?id= —— 与目标期开奖比对，提示中几等奖(仅展示)。"""
    authentication_classes = []

    def get(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        raw_id = request.query_params.get("id")
        try:
            rec_id = int(raw_id)
        except (TypeError, ValueError):
            return Response(make_response(code=1, msg="参数非法", error=f"id={raw_id}"))
        rec = UserNumber.objects.filter(id=rec_id, user_id=uid).first()
        if rec is None:
            return Response(make_response(code=1, msg="记录不存在"))
        if not rec.target_issue:
            return Response(make_response(code=1, msg="未设置目标期号"))
        draw = (DrawResult.objects
                .filter(lottery=rec.lottery, issue=rec.target_issue,
                        status=DrawResult.STATUS_PUBLISHED).first())
        if draw is None:
            return Response(make_response(code=1, msg="目标期号暂未开奖"))
        rc = rec.lottery.rule_config
        if rc.get("play_type") == "digit":
            result = judge_digit(rc, draw.numbers, rec.numbers)
        elif rc.get("play_type") == "keno":
            result = judge_keno(rc, draw.numbers, rec.numbers)
        else:
            result = judge_prize(rc, draw.numbers, rec.numbers)
        return Response(make_response(data=result))


class NumberGenerateView(APIView):
    """POST /api/user/number/generate —— 机选预览(不写库)。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        code = request.data.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        try:
            count = int(request.data.get("count", 5))
        except (TypeError, ValueError):
            count = 5
        count = max(1, min(count, 10))
        picks = request.data.get("picks")
        if not isinstance(picks, dict):
            picks = None
        sets = [random_numbers(lottery.rule_config, picks) for _ in range(count)]
        return Response(make_response(data={"sets": sets}))


class NumberGroupView(APIView):
    """POST /api/user/number/group —— 给自己的记录设置/清除分组名。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        raw_id = request.data.get("id")
        try:
            rec_id = int(raw_id)
        except (TypeError, ValueError):
            return Response(make_response(code=1, msg="参数非法", error=f"id={raw_id}"))
        rec = UserNumber.objects.filter(id=rec_id, user_id=uid).first()
        if rec is None:
            return Response(make_response(code=1, msg="记录不存在"))
        group_name = str(request.data.get("group_name") or "").strip()[:50]
        rec.group_name = group_name
        rec.save(update_fields=["group_name"])
        return Response(make_response(data=UserNumberSerializer(rec).data))
