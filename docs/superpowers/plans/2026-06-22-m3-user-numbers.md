# M3 记录号码（后端）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 后端实现"记录自己的号码"模块：用户登录（可替换抽象 + 开发态 mock）、手动/机选/定胆随机选号、我的号码增删查、目标期号中奖比对。

**Architecture:** 新增 `usernumber` app 承载 UserNumber 模型 + 选号/比对接口；登录鉴权与微信 provider 放 `common/auth.py`（mock 与真实 code2session 为各自独立函数，selector 按是否配置 appid/secret 切换）。号码区规则与奖级判定规则统一读 `Lottery.rule_config`，加彩种不改代码。所有接口走 `common.utils.make_response`，session 存 user_id 的 hash，绝不下发真实 openid。

**Tech Stack:** Django 5.2 / Python 3.12 / DRF 3.16 / PostgreSQL 17（本地测试 Docker pg16）/ pytest + pytest-django。

## Global Constraints

- 日志用 `logging` 标准库（`logging.info/warning/error`），异常用 `exc_info=True`，**禁止 `print`**，不用 `logging.exception()`。
- 所有接口返回统一走 `common.utils.make_response(data=None, code=0, msg="ok", error=None)`：成功 `code=0`，应用级错误 `code=1` 且 HTTP 200，不裸返回 DRF 默认结构。
- `user_id` 一律存 **hash**（`hashlib.sha256((SECRET_KEY + openid))` 十六进制），接口不下发真实 openid。
- 号码区规则、奖级判定规则统一读 `Lottery.rule_config`（JSON），不写死红蓝球个数/范围/奖级。
- 密钥类（WECHAT_APPID / WECHAT_SECRET）只放环境变量（`.env` / `os.environ`），普通 URL 直接写代码。
- 微信登录用"可替换登录抽象 + 开发态 mock"：mock 与真实 code2session 各自独立函数，不合并成分发器；真实 provider 现在落地但默认不启用（无 appid/secret 时走 mock）。
- 本里程碑是后端 only。测试用 pytest，APIClient fixture **命名 `api_client`，不要叫 `client`**（避免遮蔽 pytest-django 内置）。
- 用户态接口设 `authentication_classes = []`，自己读 `request.session`，避免 DRF SessionAuthentication 带来的 CSRF 校验；登录态校验靠 `current_user_id(request)`。
- 测试 DB：Docker 容器 lottery_pg，127.0.0.1:5433，db=lottery user=postgres pw=lottery_dev（pytest.ini 已配 pythonpath=lottery_backend）。
- 运行测试统一在 `lottery_backend` 目录、激活 `.venv`（`source .venv/Scripts/activate`）后 `python -m pytest`。

---

## File Structure

新增/修改文件及职责：

- `lottery_backend/common/auth.py`（新建）：`hash_user_id(openid)`、`mock_code_to_openid(code)`、`wechat_code_to_openid(code)`、`code_to_openid(code)`（selector）、`set_user_session(request, openid)`、`current_user_id(request)`。
- `lottery_backend/common/tests/test_auth.py`（新建）：上述函数单测。
- `lottery_backend/usernumber/__init__.py`、`apps.py`（新建）：app 定义。
- `lottery_backend/usernumber/models.py`（新建）：`UserNumber` 模型。
- `lottery_backend/usernumber/migrations/`（生成）：模型迁移。
- `lottery_backend/usernumber/generator.py`（新建）：`random_numbers(rule_config)`、`dan_random_numbers(rule_config, dan_numbers)`。
- `lottery_backend/usernumber/judge.py`（新建）：`judge_prize(rule_config, draw_numbers, user_numbers)`。
- `lottery_backend/usernumber/serializers.py`（新建）：`UserNumberSerializer`。
- `lottery_backend/usernumber/views.py`（新建）：`LoginView`、`NumberCreateView`、`NumberListView`、`NumberDeleteView`、`NumberCheckView`。
- `lottery_backend/usernumber/urls.py`（新建）：`/api/user/*` 路由。
- `lottery_backend/usernumber/tests/`（新建）：各接口与算法测试。
- `lottery_backend/config/settings.py`（修改）：INSTALLED_APPS 追加 `usernumber`；新增 `WECHAT_APPID`/`WECHAT_SECRET`。
- `lottery_backend/config/urls.py`（修改）：追加 `path("api/user/", include("usernumber.urls"))`。
- `lottery_backend/lottery/management/commands/seed_lotteries.py`（修改）：ssq/dlt 的 rule_config 增加 `prize_rules`。

---

### Task 1: UserNumber 模型

**Files:**
- Create: `lottery_backend/usernumber/__init__.py`（空）
- Create: `lottery_backend/usernumber/apps.py`
- Create: `lottery_backend/usernumber/models.py`
- Create: `lottery_backend/usernumber/migrations/__init__.py`（空）
- Create: `lottery_backend/usernumber/tests/__init__.py`（空）
- Create: `lottery_backend/usernumber/tests/test_models.py`
- Modify: `lottery_backend/config/settings.py`（INSTALLED_APPS 追加 `usernumber`）

**Interfaces:**
- Consumes: `lottery.models.Lottery`
- Produces: `usernumber.models.UserNumber`，字段 `user_id, lottery(FK related_name="user_numbers"), numbers(JSON dict), gen_type, dan_numbers(JSON dict), note, target_issue, created_at`；常量 `GEN_MANUAL="manual"` / `GEN_RANDOM="random"` / `GEN_DAN="dan_random"`。

- [ ] **Step 1: 建 app 骨架与 settings 注册**

`lottery_backend/usernumber/apps.py`:
```python
from django.apps import AppConfig


class UsernumberConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usernumber"
```

`lottery_backend/config/settings.py` — INSTALLED_APPS 在 `"crawler",` 后追加一行：
```python
    "crawler",
    "usernumber",
]
```

`usernumber/__init__.py`、`usernumber/migrations/__init__.py`、`usernumber/tests/__init__.py` 均为空文件。

- [ ] **Step 2: 写失败测试**

`lottery_backend/usernumber/tests/test_models.py`:
```python
import pytest
from lottery.models import Lottery
from usernumber.models import UserNumber


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_create_user_number_defaults(ssq):
    rec = UserNumber.objects.create(
        user_id="hash_abc", lottery=ssq,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    )
    assert rec.gen_type == UserNumber.GEN_MANUAL
    assert rec.dan_numbers == {}
    assert rec.note == ""
    assert rec.target_issue == ""
    assert rec.created_at is not None


def test_gen_type_constants():
    assert UserNumber.GEN_MANUAL == "manual"
    assert UserNumber.GEN_RANDOM == "random"
    assert UserNumber.GEN_DAN == "dan_random"
```

- [ ] **Step 3: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_models.py -v`
Expected: FAIL（`ModuleNotFoundError: usernumber.models` / 模型未定义）

- [ ] **Step 4: 写模型**

`lottery_backend/usernumber/models.py`:
```python
from django.db import models
from lottery.models import Lottery


class UserNumber(models.Model):
    """用户记录的号码。user_id 存 hash，不暴露真实 openid。"""
    GEN_MANUAL = "manual"
    GEN_RANDOM = "random"
    GEN_DAN = "dan_random"
    GEN_CHOICES = [(GEN_MANUAL, "手动"), (GEN_RANDOM, "机选"), (GEN_DAN, "定胆随机")]

    user_id = models.CharField("用户哈希", max_length=64, db_index=True)
    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE,
                                related_name="user_numbers", verbose_name="彩种")
    numbers = models.JSONField("号码", default=dict)
    gen_type = models.CharField("生成方式", max_length=12, choices=GEN_CHOICES, default=GEN_MANUAL)
    dan_numbers = models.JSONField("胆码", default=dict, blank=True)
    note = models.CharField("备注", max_length=100, blank=True, default="")
    target_issue = models.CharField("目标期号", max_length=20, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户号码"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id[:8]} {self.lottery.code}"
```

- [ ] **Step 5: 生成迁移**

Run: `python manage.py makemigrations usernumber`
Expected: 生成 `usernumber/migrations/0001_initial.py`

- [ ] **Step 6: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_models.py -v`
Expected: PASS（2 passed）

- [ ] **Step 7: 提交**

```bash
git add lottery_backend/usernumber lottery_backend/config/settings.py
git commit -m "feat: UserNumber 模型与 usernumber app"
```

---

### Task 2: 登录鉴权与微信 provider（common/auth.py）

**Files:**
- Create: `lottery_backend/common/auth.py`
- Create: `lottery_backend/common/tests/test_auth.py`
- Modify: `lottery_backend/config/settings.py`（新增 WECHAT_APPID / WECHAT_SECRET）

**Interfaces:**
- Consumes: `django.conf.settings.SECRET_KEY` / `settings.WECHAT_APPID` / `settings.WECHAT_SECRET`
- Produces:
  - `hash_user_id(openid: str) -> str`（64 位十六进制，确定性）
  - `mock_code_to_openid(code: str) -> str | None`（开发态：直接把 code 当 openid）
  - `wechat_code_to_openid(code: str) -> str | None`（真实 code2session，失败返回 None）
  - `code_to_openid(code: str) -> str | None`（selector：配置了 appid+secret 走微信，否则走 mock）
  - `set_user_session(request, openid: str) -> str`（写 session["uid"]=hash，返回 hash）
  - `current_user_id(request) -> str | None`（读 session["uid"]）

- [ ] **Step 1: settings 增加微信密钥位（来自环境变量）**

`lottery_backend/config/settings.py` 末尾追加：
```python
# 微信小程序登录（未注册主体前留空；留空时登录走开发态 mock）
WECHAT_APPID = os.environ.get("WECHAT_APPID", "")
WECHAT_SECRET = os.environ.get("WECHAT_SECRET", "")
```

- [ ] **Step 2: 写失败测试**

`lottery_backend/common/tests/test_auth.py`:
```python
import pytest
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from common import auth


def _request_with_session():
    req = RequestFactory().get("/")
    SessionMiddleware(lambda r: None).process_request(req)
    return req


def test_hash_user_id_deterministic_and_not_raw():
    h1 = auth.hash_user_id("openid_xyz")
    h2 = auth.hash_user_id("openid_xyz")
    assert h1 == h2
    assert h1 != "openid_xyz"
    assert len(h1) == 64


def test_mock_returns_code_as_openid():
    assert auth.mock_code_to_openid("openid_abc") == "openid_abc"
    assert auth.mock_code_to_openid("") is None


def test_selector_uses_mock_without_credentials(settings):
    settings.WECHAT_APPID = ""
    settings.WECHAT_SECRET = ""
    assert auth.code_to_openid("openid_abc") == "openid_abc"


def test_selector_uses_wechat_with_credentials(settings, monkeypatch):
    settings.WECHAT_APPID = "wxappid"
    settings.WECHAT_SECRET = "wxsecret"
    monkeypatch.setattr(auth, "wechat_code_to_openid", lambda code: f"wx::{code}")
    assert auth.code_to_openid("jscode") == "wx::jscode"


def test_session_roundtrip():
    req = _request_with_session()
    uid = auth.set_user_session(req, "openid_abc")
    assert uid == auth.hash_user_id("openid_abc")
    assert auth.current_user_id(req) == uid


def test_current_user_id_none_when_not_logged_in():
    req = _request_with_session()
    assert auth.current_user_id(req) is None
```

- [ ] **Step 3: 跑测试确认失败**

Run: `python -m pytest common/tests/test_auth.py -v`
Expected: FAIL（`ModuleNotFoundError: common.auth`）

- [ ] **Step 4: 写实现**

`lottery_backend/common/auth.py`:
```python
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
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest common/tests/test_auth.py -v`
Expected: PASS（6 passed）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/common/auth.py lottery_backend/common/tests/test_auth.py lottery_backend/config/settings.py
git commit -m "feat: 登录鉴权与微信 provider(可替换抽象+开发态mock)"
```

---

### Task 3: 登录接口 LoginView

**Files:**
- Create: `lottery_backend/usernumber/views.py`
- Create: `lottery_backend/usernumber/urls.py`
- Create: `lottery_backend/usernumber/tests/test_login.py`
- Modify: `lottery_backend/config/urls.py`（追加 `api/user/` include）

**Interfaces:**
- Consumes: `common.auth.code_to_openid`、`common.auth.set_user_session`、`common.utils.make_response`
- Produces: `POST /api/user/login`（body `{code}`）→ 成功 `{code:0, data:{logged_in:true}}` 且写 session；缺 code 或换取失败 → `code=1`。后续任务在同一 `views.py`/`urls.py` 追加视图与路由。

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_login.py`:
```python
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


def test_login_success_sets_session(db, api_client):
    resp = api_client.post("/api/user/login", {"code": "openid_abc"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["code"] == 0
    assert resp.json()["data"]["logged_in"] is True
    assert api_client.session.get("uid")


def test_login_missing_code(db, api_client):
    resp = api_client.post("/api/user/login", {}, format="json")
    assert resp.status_code == 200
    assert resp.json()["code"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_login.py -v`
Expected: FAIL（404 / 路由与视图未定义）

- [ ] **Step 3: 写视图与路由**

`lottery_backend/usernumber/views.py`:
```python
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
```

`lottery_backend/usernumber/urls.py`:
```python
from django.urls import path
from usernumber import views

urlpatterns = [
    path("login", views.LoginView.as_view(), name="user-login"),
]
```

`lottery_backend/config/urls.py` — urlpatterns 追加一行：
```python
    path("api/openapi/", include("lottery.urls")),
    path("api/user/", include("usernumber.urls")),
]
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_login.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_login.py lottery_backend/config/urls.py
git commit -m "feat: 用户登录接口 /api/user/login"
```

---

### Task 4: 选号生成 generator（机选 / 定胆随机）

**Files:**
- Create: `lottery_backend/usernumber/generator.py`
- Create: `lottery_backend/usernumber/tests/test_generator.py`

**Interfaces:**
- Consumes: `Lottery.rule_config`（`{red:{count,min,max}, blue:{...}}`）
- Produces:
  - `random_numbers(rule_config) -> {"red":[...升序], "blue":[...升序]}`
  - `dan_random_numbers(rule_config, dan_numbers) -> {"red":[...], "blue":[...]}`，胆码必含；胆码越界/数量超区时 `raise ValueError`

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_generator.py`:
```python
import pytest
from usernumber.generator import random_numbers, dan_random_numbers

RULE = {"red": {"count": 6, "min": 1, "max": 33},
        "blue": {"count": 1, "min": 1, "max": 16}}


def test_random_numbers_shape_and_range():
    nums = random_numbers(RULE)
    assert len(nums["red"]) == 6
    assert len(set(nums["red"])) == 6
    assert nums["red"] == sorted(nums["red"])
    assert all(1 <= n <= 33 for n in nums["red"])
    assert len(nums["blue"]) == 1
    assert 1 <= nums["blue"][0] <= 16


def test_dan_random_includes_dan_and_fills():
    nums = dan_random_numbers(RULE, {"red": [7, 8], "blue": []})
    assert 7 in nums["red"] and 8 in nums["red"]
    assert len(nums["red"]) == 6
    assert len(set(nums["red"])) == 6
    assert nums["red"] == sorted(nums["red"])
    assert len(nums["blue"]) == 1


def test_dan_out_of_range_raises():
    with pytest.raises(ValueError):
        dan_random_numbers(RULE, {"red": [99], "blue": []})


def test_dan_too_many_raises():
    with pytest.raises(ValueError):
        dan_random_numbers(RULE, {"red": [1, 2, 3, 4, 5, 6, 7], "blue": []})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_generator.py -v`
Expected: FAIL（`ModuleNotFoundError: usernumber.generator`）

- [ ] **Step 3: 写实现**

`lottery_backend/usernumber/generator.py`:
```python
import random


def random_numbers(rule_config):
    """按 rule_config 机选，每区取 count 个不重复号码，升序返回。"""
    result = {}
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        picks = random.sample(range(rule["min"], rule["max"] + 1), rule["count"])
        result[zone] = sorted(picks)
    return result


def dan_random_numbers(rule_config, dan_numbers):
    """定胆随机：锁定胆码，剩余位从未选号码池随机补全；胆码非法抛 ValueError。"""
    result = {}
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        dans = list(dict.fromkeys(dan_numbers.get(zone, [])))  # 去重保序
        count = rule["count"]
        for d in dans:
            if not (rule["min"] <= d <= rule["max"]):
                raise ValueError(f"{zone} 胆码 {d} 超出范围 [{rule['min']},{rule['max']}]")
        if len(dans) > count:
            raise ValueError(f"{zone} 胆码数量 {len(dans)} 超过该区号码数 {count}")
        pool = [n for n in range(rule["min"], rule["max"] + 1) if n not in dans]
        picks = dans + random.sample(pool, count - len(dans))
        result[zone] = sorted(picks)
    return result
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_generator.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/usernumber/generator.py lottery_backend/usernumber/tests/test_generator.py
git commit -m "feat: 机选与定胆随机选号算法"
```

---

### Task 5: 记录创建接口 NumberCreateView

**Files:**
- Create: `lottery_backend/usernumber/serializers.py`
- Modify: `lottery_backend/usernumber/views.py`（追加 `NumberCreateView`）
- Modify: `lottery_backend/usernumber/urls.py`（追加 `number/create`）
- Create: `lottery_backend/usernumber/tests/test_number_create.py`

**Interfaces:**
- Consumes: `current_user_id`、`lottery.views._get_active_lottery`、`lottery.validators.validate_numbers`、`generator.random_numbers` / `dan_random_numbers`、`UserNumber`、`make_response`
- Produces: `POST /api/user/number/create`（body `{code, gen_type, numbers?, dan_numbers?, note?, target_issue?}`）→ 成功 `code=0, data=UserNumberSerializer`；未登录/未知彩种/号码非法/胆码非法 → `code=1`。`UserNumberSerializer.fields = ["id","code","numbers","gen_type","dan_numbers","note","target_issue","created_at"]`，`code` 来自 `lottery.code`。

- [ ] **Step 1: 写 serializer**

`lottery_backend/usernumber/serializers.py`:
```python
from rest_framework import serializers
from usernumber.models import UserNumber


class UserNumberSerializer(serializers.ModelSerializer):
    code = serializers.CharField(source="lottery.code", read_only=True)

    class Meta:
        model = UserNumber
        fields = ["id", "code", "numbers", "gen_type", "dan_numbers",
                  "note", "target_issue", "created_at"]
```

- [ ] **Step 2: 写失败测试**

`lottery_backend/usernumber/tests/test_number_create.py`:
```python
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


def test_create_manual_valid(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
        "note": "test",
    }, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["numbers"]["blue"] == [7]
    assert body["data"]["note"] == "test"


def test_create_manual_invalid(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "manual",
        "numbers": {"red": [1, 2, 3], "blue": [7]},
    }, format="json")
    assert resp.json()["code"] == 1


def test_create_random(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random",
    }, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["numbers"]["red"]) == 6


def test_create_dan_random(ssq, auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "ssq", "gen_type": "dan_random",
        "dan_numbers": {"red": [7, 8], "blue": []},
    }, format="json")
    body = resp.json()
    assert body["code"] == 0
    assert 7 in body["data"]["numbers"]["red"]


def test_create_unauthenticated(ssq):
    resp = APIClient().post("/api/user/number/create", {
        "code": "ssq", "gen_type": "random",
    }, format="json")
    assert resp.json()["code"] == 1


def test_create_unknown_code(auth_client):
    resp = auth_client.post("/api/user/number/create", {
        "code": "nope", "gen_type": "random",
    }, format="json")
    assert resp.json()["code"] == 1
```

- [ ] **Step 3: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_number_create.py -v`
Expected: FAIL（404 / NumberCreateView 未定义）

- [ ] **Step 4: 写视图与路由**

`lottery_backend/usernumber/views.py` — 顶部 import 区把原 `from common.auth import code_to_openid, set_user_session` 整行替换为：
```python
from common.auth import code_to_openid, set_user_session, current_user_id
from lottery.views import _get_active_lottery
from lottery.validators import validate_numbers
from usernumber.models import UserNumber
from usernumber.generator import random_numbers, dan_random_numbers
from usernumber.serializers import UserNumberSerializer
```

在文件末尾追加：
```python
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
        if gen_type == UserNumber.GEN_RANDOM:
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
```

`lottery_backend/usernumber/urls.py` — urlpatterns 追加：
```python
    path("number/create", views.NumberCreateView.as_view(), name="user-number-create"),
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_number_create.py -v`
Expected: PASS（6 passed）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/serializers.py lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_number_create.py
git commit -m "feat: 记录号码创建接口 /api/user/number/create"
```

---

### Task 6: 我的号码列表与删除

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（追加 `NumberListView`、`NumberDeleteView`）
- Modify: `lottery_backend/usernumber/urls.py`（追加 `number/list`、`number/<int:pk>`）
- Create: `lottery_backend/usernumber/tests/test_number_list_delete.py`

**Interfaces:**
- Consumes: `current_user_id`、`UserNumber`、`UserNumberSerializer`、`make_response`
- Produces:
  - `GET /api/user/number/list?code=` → 当前用户的记录（可按 code 过滤），`data` 为列表
  - `DELETE /api/user/number/<id>` → 删自己的记录；非自己/不存在 → `code=1`

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_number_list_delete.py`:
```python
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery
from usernumber.models import UserNumber
from common.auth import hash_user_id


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


def _make_record(user_openid, lottery):
    return UserNumber.objects.create(
        user_id=hash_user_id(user_openid), lottery=lottery,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
    )


def test_list_returns_only_own(ssq, auth_client):
    _make_record("tester-openid", ssq)
    _make_record("other-openid", ssq)
    resp = auth_client.get("/api/user/number/list")
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) == 1


def test_list_filter_by_code(ssq, auth_client):
    _make_record("tester-openid", ssq)
    resp = auth_client.get("/api/user/number/list?code=dlt")
    assert resp.json()["data"] == []


def test_delete_own(ssq, auth_client):
    rec = _make_record("tester-openid", ssq)
    resp = auth_client.delete(f"/api/user/number/{rec.id}")
    assert resp.json()["code"] == 0
    assert not UserNumber.objects.filter(id=rec.id).exists()


def test_delete_other_forbidden(ssq, auth_client):
    rec = _make_record("other-openid", ssq)
    resp = auth_client.delete(f"/api/user/number/{rec.id}")
    assert resp.json()["code"] == 1
    assert UserNumber.objects.filter(id=rec.id).exists()


def test_list_unauthenticated(ssq):
    resp = APIClient().get("/api/user/number/list")
    assert resp.json()["code"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_number_list_delete.py -v`
Expected: FAIL（404 / 视图未定义）

- [ ] **Step 3: 写视图与路由**

`lottery_backend/usernumber/views.py` 末尾追加：
```python
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
```

`lottery_backend/usernumber/urls.py` — urlpatterns 追加（`number/<int:pk>` 放最后，避免吃掉 list/create/check）：
```python
    path("number/list", views.NumberListView.as_view(), name="user-number-list"),
    path("number/<int:pk>", views.NumberDeleteView.as_view(), name="user-number-delete"),
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_number_list_delete.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_number_list_delete.py
git commit -m "feat: 我的号码列表与删除接口"
```

---

### Task 7: 奖级判定 judge + prize_rules 种子

**Files:**
- Create: `lottery_backend/usernumber/judge.py`
- Create: `lottery_backend/usernumber/tests/test_judge.py`
- Modify: `lottery_backend/lottery/management/commands/seed_lotteries.py`（ssq/dlt rule_config 增加 `prize_rules`）

**Interfaces:**
- Consumes: `lottery.grades.grade_label`；`rule_config["prize_rules"]`（`[{level:int, red:int, blue:int}, ...]`）
- Produces: `judge_prize(rule_config, draw_numbers, user_numbers) -> {"red_hit":int, "blue_hit":int, "level":int|None, "label":str}`；命中多条取最小 level（最高奖），无命中 `level=None`、`label="未中奖"`。

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_judge.py`:
```python
from usernumber.judge import judge_prize

SSQ_RULE = {
    "red": {"count": 6, "min": 1, "max": 33},
    "blue": {"count": 1, "min": 1, "max": 16},
    "prize_rules": [
        {"level": 1, "red": 6, "blue": 1},
        {"level": 2, "red": 6, "blue": 0},
        {"level": 3, "red": 5, "blue": 1},
        {"level": 4, "red": 5, "blue": 0},
        {"level": 4, "red": 4, "blue": 1},
        {"level": 5, "red": 4, "blue": 0},
        {"level": 5, "red": 3, "blue": 1},
        {"level": 6, "red": 2, "blue": 1},
        {"level": 6, "red": 1, "blue": 1},
        {"level": 6, "red": 0, "blue": 1},
    ],
}
DRAW = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}


def test_first_prize():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    assert r["red_hit"] == 6 and r["blue_hit"] == 1
    assert r["level"] == 1
    assert r["label"] == "一等奖"


def test_second_prize():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [1, 2, 3, 4, 5, 6], "blue": [16]})
    assert r["level"] == 2
    assert r["label"] == "二等奖"


def test_sixth_prize_blue_only():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [8, 9, 10, 11, 12, 13], "blue": [7]})
    assert r["red_hit"] == 0 and r["blue_hit"] == 1
    assert r["level"] == 6


def test_no_prize():
    r = judge_prize(SSQ_RULE, DRAW, {"red": [8, 9, 10, 11, 12, 13], "blue": [16]})
    assert r["level"] is None
    assert r["label"] == "未中奖"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_judge.py -v`
Expected: FAIL（`ModuleNotFoundError: usernumber.judge`）

- [ ] **Step 3: 写实现**

`lottery_backend/usernumber/judge.py`:
```python
from lottery.grades import grade_label


def judge_prize(rule_config, draw_numbers, user_numbers):
    """按 rule_config["prize_rules"] 判定中奖等级。命中多条取最小 level(最高奖)。"""
    red_hit = len(set(user_numbers.get("red", [])) & set(draw_numbers.get("red", [])))
    blue_hit = len(set(user_numbers.get("blue", [])) & set(draw_numbers.get("blue", [])))
    level = None
    for rule in rule_config.get("prize_rules", []):
        if rule.get("red") == red_hit and rule.get("blue") == blue_hit:
            if level is None or rule["level"] < level:
                level = rule["level"]
    label = grade_label(level) if level is not None else "未中奖"
    return {"red_hit": red_hit, "blue_hit": blue_hit, "level": level, "label": label}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_judge.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 给种子加 prize_rules**

`lottery_backend/lottery/management/commands/seed_lotteries.py` — ssq 的 rule_config 改为：
```python
        "rule_config": {"red": {"count": 6, "min": 1, "max": 33},
                        "blue": {"count": 1, "min": 1, "max": 16},
                        "prize_rules": [
                            {"level": 1, "red": 6, "blue": 1},
                            {"level": 2, "red": 6, "blue": 0},
                            {"level": 3, "red": 5, "blue": 1},
                            {"level": 4, "red": 5, "blue": 0},
                            {"level": 4, "red": 4, "blue": 1},
                            {"level": 5, "red": 4, "blue": 0},
                            {"level": 5, "red": 3, "blue": 1},
                            {"level": 6, "red": 2, "blue": 1},
                            {"level": 6, "red": 1, "blue": 1},
                            {"level": 6, "red": 0, "blue": 1},
                        ]},
```
dlt 的 rule_config 改为：
```python
        "rule_config": {"red": {"count": 5, "min": 1, "max": 35},
                        "blue": {"count": 2, "min": 1, "max": 12},
                        "prize_rules": [
                            {"level": 1, "red": 5, "blue": 2},
                            {"level": 2, "red": 5, "blue": 1},
                            {"level": 3, "red": 5, "blue": 0},
                            {"level": 4, "red": 4, "blue": 2},
                            {"level": 5, "red": 4, "blue": 1},
                            {"level": 6, "red": 3, "blue": 2},
                            {"level": 7, "red": 4, "blue": 0},
                            {"level": 8, "red": 3, "blue": 1},
                            {"level": 8, "red": 2, "blue": 2},
                            {"level": 9, "red": 3, "blue": 0},
                            {"level": 9, "red": 1, "blue": 2},
                            {"level": 9, "red": 2, "blue": 1},
                            {"level": 9, "red": 0, "blue": 2},
                        ]},
```

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/judge.py lottery_backend/usernumber/tests/test_judge.py lottery_backend/lottery/management/commands/seed_lotteries.py
git commit -m "feat: 奖级判定 judge_prize 与 prize_rules 种子"
```

---

### Task 8: 中奖比对接口 NumberCheckView

**Files:**
- Modify: `lottery_backend/usernumber/views.py`（追加 `NumberCheckView`，import `DrawResult`、`judge_prize`）
- Modify: `lottery_backend/usernumber/urls.py`（追加 `number/check`）
- Create: `lottery_backend/usernumber/tests/test_number_check.py`

**Interfaces:**
- Consumes: `current_user_id`、`UserNumber`、`DrawResult`、`judge.judge_prize`、`make_response`
- Produces: `GET /api/user/number/check?id=` → 比对该记录与其 `target_issue` 的已发布开奖，返回 `judge_prize` 结果；未登录/记录不存在/未设目标期号/目标期未开奖 → `code=1`。

- [ ] **Step 1: 写失败测试**

`lottery_backend/usernumber/tests/test_number_check.py`:
```python
import datetime
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult
from usernumber.models import UserNumber
from common.auth import hash_user_id

PRIZE_RULES = [
    {"level": 1, "red": 6, "blue": 1},
    {"level": 6, "red": 0, "blue": 1},
]


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16},
                     "prize_rules": PRIZE_RULES},
        draw_days=[2, 4, 7],
    )


@pytest.fixture
def auth_client(db):
    c = APIClient()
    c.post("/api/user/login", {"code": "tester-openid"}, format="json")
    return c


def _published_draw(lottery, issue, numbers):
    return DrawResult.objects.create(
        lottery=lottery, issue=issue, draw_date=datetime.date(2026, 6, 20),
        numbers=numbers, status=DrawResult.STATUS_PUBLISHED,
    )


def _record(lottery, issue, numbers):
    return UserNumber.objects.create(
        user_id=hash_user_id("tester-openid"), lottery=lottery,
        numbers=numbers, target_issue=issue,
    )


def test_check_first_prize(ssq, auth_client):
    nums = {"red": [1, 2, 3, 4, 5, 6], "blue": [7]}
    _published_draw(ssq, "2026073", nums)
    rec = _record(ssq, "2026073", nums)
    resp = auth_client.get(f"/api/user/number/check?id={rec.id}")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["level"] == 1
    assert body["data"]["label"] == "一等奖"


def test_check_draw_not_published_yet(ssq, auth_client):
    rec = _record(ssq, "2026099", {"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    resp = auth_client.get(f"/api/user/number/check?id={rec.id}")
    assert resp.json()["code"] == 1


def test_check_record_not_own(ssq, auth_client):
    rec = UserNumber.objects.create(
        user_id=hash_user_id("other-openid"), lottery=ssq,
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]}, target_issue="2026073",
    )
    resp = auth_client.get(f"/api/user/number/check?id={rec.id}")
    assert resp.json()["code"] == 1


def test_check_unauthenticated(ssq):
    resp = APIClient().get("/api/user/number/check?id=1")
    assert resp.json()["code"] == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_number_check.py -v`
Expected: FAIL（404 / NumberCheckView 未定义）

- [ ] **Step 3: 写视图与路由**

`lottery_backend/usernumber/views.py` — import 区追加：
```python
from lottery.models import DrawResult
from usernumber.judge import judge_prize
```
文件末尾追加：
```python
class NumberCheckView(APIView):
    """GET /api/user/number/check?id= —— 与目标期开奖比对，提示中几等奖(仅展示)。"""
    authentication_classes = []

    def get(self, request):
        uid = current_user_id(request)
        if not uid:
            return Response(make_response(code=1, msg="未登录"))
        rec = UserNumber.objects.filter(id=request.query_params.get("id"), user_id=uid).first()
        if rec is None:
            return Response(make_response(code=1, msg="记录不存在"))
        if not rec.target_issue:
            return Response(make_response(code=1, msg="未设置目标期号"))
        draw = (DrawResult.objects
                .filter(lottery=rec.lottery, issue=rec.target_issue,
                        status=DrawResult.STATUS_PUBLISHED).first())
        if draw is None:
            return Response(make_response(code=1, msg="目标期号暂未开奖"))
        result = judge_prize(rec.lottery.rule_config, draw.numbers, rec.numbers)
        return Response(make_response(data=result))
```

`lottery_backend/usernumber/urls.py` — 在 `number/<int:pk>` **之前**追加：
```python
    path("number/check", views.NumberCheckView.as_view(), name="user-number-check"),
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest usernumber/tests/test_number_check.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 全量回归**

Run: `python -m pytest -q`
Expected: PASS（M2a 44 + M3 新增，全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/views.py lottery_backend/usernumber/urls.py lottery_backend/usernumber/tests/test_number_check.py
git commit -m "feat: 中奖比对接口 /api/user/number/check"
```

---

## 计划自检

**1. Spec 覆盖（设计文档模块二 + API 列表）：**
- `POST /api/user/login` → Task 3 ✓
- `POST /api/user/number/create`（手动/机选/定胆随机，含 note/target_issue）→ Task 5 ✓
- `GET /api/user/number/list?code=` → Task 6 ✓
- `DELETE /api/user/number/{id}` → Task 6 ✓
- `GET /api/user/number/check?id=`（中奖比对，仅展示不兑奖）→ Task 8 ✓
- 选号器读 rule_config、随机/定胆随机算法放后端 → Task 4 ✓
- user_id hash 存储 → Task 1（字段）+ Task 2（hash_user_id）✓
- 奖级判定放 rule_config → Task 7 ✓
- 登录可替换抽象 + 开发态 mock → Task 2 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每个代码步骤含完整代码。

**3. 类型/签名一致性：**
- `UserNumber.GEN_MANUAL/GEN_RANDOM/GEN_DAN` 在 Task 1 定义，Task 5 引用一致。
- `current_user_id` / `code_to_openid` / `set_user_session` / `hash_user_id` Task 2 定义，Task 3/5/6/8 引用一致。
- `random_numbers` / `dan_random_numbers` Task 4 定义，Task 5 引用一致。
- `judge_prize` 返回 `{red_hit, blue_hit, level, label}` Task 7 定义，Task 8 测试断言一致。
- `UserNumberSerializer.fields` Task 5 定义，含 `code`（source=lottery.code），Task 5/6 测试只断言 numbers/note 等字段。
- `_get_active_lottery` 复用自 `lottery/views.py`，Task 5/8 import 一致。

**4. 注意点（给执行者）：**
- APIClient fixture 一律命名 `api_client`/`auth_client`，**不要叫 `client`**（M2a 评审已记 Minor）。
- 用户态视图 `authentication_classes = []`，自管 session，避免 CSRF。
- `usernumber/urls.py` 中 `number/<int:pk>` 必须排在 `number/create`、`number/list`、`number/check` 之后。
- Task 5 替换 import 行时勿重复 `from common.auth import ...`。
