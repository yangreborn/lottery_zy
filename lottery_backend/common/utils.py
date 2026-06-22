def make_response(data=None, code=0, msg="ok", error=None):
    """统一 API 返回结构 {code, msg, data, error}。"""
    return {"code": code, "msg": msg, "data": data, "error": error}
