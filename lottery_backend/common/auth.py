import hashlib
import json
import logging
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

WECHAT_CODE2SESSION_URL = "https://api.weixin.qq.com/sns/jscode2session"


def hash_user_id(openid):
    """openid -> 确定性 hash，作为对外 user_id，不暴露真实 openid。"""
    raw = f"{settings.SECRET_KEY}:{openid}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def mock_code_to_openid(code):
    """开发态：直接把前端传来的 code 当作 openid。"""
    if not code:
        return None
    return code


def wechat_code_to_openid(code):
    """真实微信 code2session，换取 openid；失败返回 None。"""
    params = urllib.parse.urlencode({
        "appid": settings.WECHAT_APPID,
        "secret": settings.WECHAT_SECRET,
        "js_code": code,
        "grant_type": "authorization_code",
    })
    url = f"{WECHAT_CODE2SESSION_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception:
        logger.error("微信 code2session 请求失败", exc_info=True)
        return None
    openid = data.get("openid")
    if not openid:
        logger.warning("微信 code2session 未返回 openid: %s", data)
    return openid


def code_to_openid(code):
    """登录 provider selector：配置了 appid+secret 走微信，否则走开发态 mock。"""
    if settings.WECHAT_APPID and settings.WECHAT_SECRET:
        return wechat_code_to_openid(code)
    return mock_code_to_openid(code)


def set_user_session(request, openid):
    """登录成功后把 user_id hash 写入 session，返回该 hash。"""
    uid = hash_user_id(openid)
    request.session["uid"] = uid
    return uid


def current_user_id(request):
    """从 session 读取当前用户 hash，未登录返回 None。"""
    return request.session.get("uid")
