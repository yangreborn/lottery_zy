from common.utils import make_response


def test_make_response_defaults():
    assert make_response() == {"code": 0, "msg": "ok", "data": None, "error": None}


def test_make_response_with_data_and_error():
    r = make_response(data={"a": 1}, code=1, msg="bad", error="boom")
    assert r == {"code": 1, "msg": "bad", "data": {"a": 1}, "error": "boom"}
