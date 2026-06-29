import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_date

from common.utils import make_response
from common.auth import mock_code_to_openid, wechat_code_to_session, set_user_session, current_user_id
from lottery.views import _get_active_lottery
from lottery.validators import validate_numbers
from usernumber.models import UserNumber, Feedback, PurchaseRecord, AppUser, get_or_create_app_user
from usernumber.generator import random_numbers, dan_random_numbers
from usernumber.serializers import UserNumberSerializer, PurchaseRecordSerializer
from lottery.models import DrawResult, Lottery
from usernumber.judge import judge_prize, judge_keno, judge_digit

logger = logging.getLogger(__name__)


class LoginView(APIView):
    """POST /api/user/login —— 匿名登录（device code 当 openid，不走 code2session）。"""
    authentication_classes = []

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(make_response(code=1, msg="缺少 code"))
        openid = mock_code_to_openid(code)
        if not openid:
            return Response(make_response(code=1, msg="登录失败", error="code 无效"))
        uid = set_user_session(request, openid)
        get_or_create_app_user(uid, openid)
        return Response(make_response(data={"logged_in": True, "token": uid}))


class ProfileView(APIView):
    """GET/POST /api/user/profile —— 读取/设置当前用户昵称。"""
    authentication_classes = []

    def get(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        user = AppUser.objects.filter(user_id=uid).first()
        nickname = user.nickname if user else ""
        home = user.home_lotteries if user else []
        return Response(make_response(data={"nickname": nickname, "short_id": uid[:8], "home_lotteries": home}))

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        # 不在此建档：档案只在登录时创建，避免写入以 hash 兜底的脏 openid
        user = AppUser.objects.filter(user_id=uid).first()
        if user is None:
            return Response(make_response(code=1, msg="请先登录", error="用户档案不存在"))
        # 昵称(可选)
        if "nickname" in request.data:
            nickname = (request.data.get("nickname") or "").strip()
            if len(nickname) > 30:
                return Response(make_response(code=1, msg="昵称过长", error="昵称不超过 30 字符"))
            user.nickname = nickname
            user.save(update_fields=["nickname", "updated_at"])
        # 首页彩种(可选)：过滤掉非上架彩种 code
        if "home_lotteries" in request.data:
            codes = request.data.get("home_lotteries")
            if not isinstance(codes, list):
                return Response(make_response(code=1, msg="参数非法", error="home_lotteries 应为数组"))
            valid = set(Lottery.objects.filter(is_active=True).values_list("code", flat=True))
            user.home_lotteries = [c for c in codes if c in valid]
            user.save(update_fields=["home_lotteries", "updated_at"])
        return Response(make_response(data={
            "nickname": user.nickname,
            "short_id": user.short_id,
            "home_lotteries": user.home_lotteries,
        }))


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


class FeedbackCreateView(APIView):
    """POST /api/user/feedback —— 提交用户反馈(匿名可提交)。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request) or ""
        content = (request.data.get("content") or "").strip()
        if not content:
            return Response(make_response(code=1, msg="请填写反馈内容"))
        if len(content) > 500:
            return Response(make_response(code=1, msg="反馈内容过长"))
        contact = (request.data.get("contact") or "").strip()
        try:
            rec = Feedback.objects.create(user_id=uid, content=content, contact=contact)
        except Exception:
            logger.error("Feedback 创建失败", exc_info=True)
            return Response(make_response(code=1, msg="提交失败，请稍后再试"))
        return Response(make_response(data={"id": rec.id}))


class BatchDeleteView(APIView):
    """POST /api/user/number/batch_delete —— 批量删除自己的记录。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not ids:
            return Response(make_response(code=1, msg="请选择记录"))
        n, _ = UserNumber.objects.filter(id__in=ids, user_id=uid).delete()
        return Response(make_response(data={"deleted": n}))


class BatchGroupView(APIView):
    """POST /api/user/number/batch_group —— 批量设置/清除分组。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        ids = request.data.get("ids")
        if not isinstance(ids, list) or not ids:
            return Response(make_response(code=1, msg="请选择记录"))
        group_name = str(request.data.get("group_name") or "").strip()[:50]
        n = UserNumber.objects.filter(id__in=ids, user_id=uid).update(group_name=group_name)
        return Response(make_response(data={"updated": n}))


class PurchaseCreateView(APIView):
    """POST /api/user/purchase/create —— 记录一条实际购买。"""
    authentication_classes = []

    def post(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        code = request.data.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        issue = str(request.data.get("issue") or "").strip()
        if not issue:
            return Response(make_response(code=1, msg="请填写期号"))
        numbers = request.data.get("numbers") or {}
        errors = validate_numbers(lottery.rule_config, numbers)
        if errors:
            return Response(make_response(code=1, msg="号码非法", error="; ".join(errors)))
        try:
            bet_count = int(request.data.get("bet_count", 1))
        except (TypeError, ValueError):
            bet_count = 1
        if bet_count < 1:
            bet_count = 1
        raw_date = request.data.get("purchase_date")
        if raw_date:
            parsed = parse_date(str(raw_date))
            if parsed is None:
                return Response(make_response(code=1, msg="购买日期非法"))
            purchase_date = parsed
        else:
            purchase_date = timezone.now().date()
        rec = PurchaseRecord.objects.create(
            user_id=uid, lottery=lottery, issue=issue, numbers=numbers,
            bet_count=bet_count, purchase_date=purchase_date,
        )
        return Response(make_response(data=PurchaseRecordSerializer(rec).data))


class PurchaseListView(APIView):
    """GET /api/user/purchase/list?code= —— 当前用户购买记录。"""
    authentication_classes = []

    def get(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        qs = PurchaseRecord.objects.filter(user_id=uid)
        code = request.query_params.get("code")
        if code:
            qs = qs.filter(lottery__code=code)
        return Response(make_response(data=PurchaseRecordSerializer(qs, many=True).data))


class PurchaseDeleteView(APIView):
    """DELETE /api/user/purchase/<id> —— 删除自己的购买记录。"""
    authentication_classes = []

    def delete(self, request, pk):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        rec = PurchaseRecord.objects.filter(id=pk, user_id=uid).first()
        if rec is None:
            return Response(make_response(code=1, msg="记录不存在"))
        rec.delete()
        return Response(make_response(data={"deleted": True}))


class WechatLoginView(APIView):
    """POST /api/user/login/wechat —— 真实微信 code2session 登录。"""
    authentication_classes = []

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response(make_response(code=1, msg="缺少 code"))
        if not settings.WECHAT_APPID or not settings.WECHAT_SECRET:
            return Response(make_response(code=1, msg="微信登录未配置",
                                          error="后端缺少 WECHAT_APPID/WECHAT_SECRET"))
        session = wechat_code_to_session(code)
        if not session:
            return Response(make_response(code=1, msg="微信登录失败", error="code 无效或已过期"))
        openid = session["openid"]
        uid = set_user_session(request, openid)
        user = get_or_create_app_user(uid, openid)
        unionid = session.get("unionid") or ""
        if unionid and user.unionid != unionid:
            user.unionid = unionid
            user.save(update_fields=["unionid", "updated_at"])
        return Response(make_response(data={"logged_in": True, "token": uid}))
