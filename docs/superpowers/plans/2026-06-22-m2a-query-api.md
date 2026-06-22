# M2a 对外只读查询 API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 M1 数据底座之上，提供一组无需登录的只读查询 API：彩种列表、当期开奖、历史开奖（分页+日期筛选）、开奖详情（含统一奖级文字）、号码出现/遗漏统计。

**Architecture:** 复用现有 `lottery` app，新增 DRF APIView 层（serializers/views/urls）+ 两个纯计算模块（`grades.py` 奖级文字、`stats.py` 号码统计）。所有接口只返回 `status=published` 的开奖数据，统一用 `common.make_response` 包成 `{code,msg,data,error}`。前端（uni-app）属后续 M2b，不在本计划。

**Tech Stack:** Django 5.2 / djangorestframework / PostgreSQL / pytest + pytest-django + DRF APIClient

## Global Constraints

- Python 3.12，Django 5.2 LTS，PostgreSQL（本地测试库 Docker pg16，连接 `127.0.0.1:5433` / db `lottery` / user `postgres` / pw `lottery_dev`，已在 `lottery_backend/.env` 配好）。
- 所有 API 返回统一 `{code, msg, data, error}`，用 `common.make_response(data=..., code=..., msg=..., error=...)`；成功 `code=0`，应用级错误（未知彩种/期号不存在/参数非法）`code=1` 且 HTTP 200。
- 查询接口**只返回 `DrawResult.status == "published"`** 的数据（draft 不对外）。
- 日志用 `logging` 标准库（`logger.info/warning/error`），异常用 `exc_info=True`，禁止 `print`。
- 不做收费会员 / 付费 / 支付逻辑。
- 统计功能仅作数据陈列（出现次数 / 遗漏），**不得**输出"推荐/预测"。
- 测试用 pytest + pytest-django，测试文件放 `lottery/tests/`，HTTP 测试用 `rest_framework.test.APIClient`。
- 接口路径统一前缀 `/api/openapi/`。

---

### Task 1: DRF 路由接入 + 彩种列表接口

**Files:**
- Create: `lottery_backend/lottery/serializers.py`
- Create: `lottery_backend/lottery/views.py`
- Create: `lottery_backend/lottery/urls.py`
- Modify: `lottery_backend/config/urls.py`
- Test: `lottery_backend/lottery/tests/test_api_lottery_list.py`

**Interfaces:**
- Produces: `lottery.serializers.LotterySerializer`（字段 `code,name,category,rule_config,draw_days`）。
- Produces: URL name `openapi-lottery-list` → `GET /api/openapi/lottery/list`，返回 `make_response(data=[{code,name,category,rule_config,draw_days}, ...])`，仅 `is_active=True`，按 `code` 升序。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_api_lottery_list.py`:
```python
import pytest
from rest_framework.test import APIClient
from lottery.models import Lottery


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def lotteries(db):
    Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                           rule_config={"red": {"count": 6, "min": 1, "max": 33},
                                        "blue": {"count": 1, "min": 1, "max": 16}},
                           draw_days=[2, 4, 7], is_active=True)
    Lottery.objects.create(code="dlt", name="超级大乐透", category="体彩",
                           rule_config={"red": {"count": 5, "min": 1, "max": 35},
                                        "blue": {"count": 2, "min": 1, "max": 12}},
                           draw_days=[1, 3, 6], is_active=True)
    Lottery.objects.create(code="off", name="下架彩种", category="福彩",
                           rule_config={}, draw_days=[], is_active=False)


def test_lottery_list_returns_active_only(client, lotteries):
    resp = client.get("/api/openapi/lottery/list")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    codes = [item["code"] for item in body["data"]]
    assert codes == ["dlt", "ssq"]  # 升序, 不含 off
    ssq = next(i for i in body["data"] if i["code"] == "ssq")
    assert ssq["rule_config"]["red"]["count"] == 6
    assert ssq["draw_days"] == [2, 4, 7]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_api_lottery_list.py -v`
Expected: FAIL（404，url 未配置）

- [ ] **Step 3: 写 serializer**

`lottery_backend/lottery/serializers.py`:
```python
from rest_framework import serializers
from lottery.models import Lottery, DrawResult


class LotterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Lottery
        fields = ("code", "name", "category", "rule_config", "draw_days")


class DrawResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = DrawResult
        fields = ("issue", "draw_date", "numbers", "sales_amount",
                  "pool_amount", "prize_grades")
```

- [ ] **Step 4: 写 view**

`lottery_backend/lottery/views.py`:
```python
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
```

- [ ] **Step 5: 写 urls 并接入 config**

`lottery_backend/lottery/urls.py`:
```python
from django.urls import path
from lottery import views

urlpatterns = [
    path("lottery/list", views.LotteryListView.as_view(), name="openapi-lottery-list"),
]
```
在 `lottery_backend/config/urls.py` 的 `urlpatterns` 中加入（保留已有 admin 行）：
```python
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/openapi/", include("lottery.urls")),
]
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_api_lottery_list.py -v`
Expected: PASS，1 passed

- [ ] **Step 7: Commit**

```bash
git add lottery_backend/lottery/serializers.py lottery_backend/lottery/views.py lottery_backend/lottery/urls.py lottery_backend/config/urls.py lottery_backend/lottery/tests/test_api_lottery_list.py
git commit -m "feat: 彩种列表只读接口 + DRF 路由接入"
```

---

### Task 2: 当期开奖接口

**Files:**
- Modify: `lottery_backend/lottery/views.py`（追加 DrawLatestView）
- Modify: `lottery_backend/lottery/urls.py`（追加路由）
- Test: `lottery_backend/lottery/tests/test_api_draw_latest.py`

**Interfaces:**
- Consumes: `DrawResultSerializer`（Task 1），`Lottery`/`DrawResult`（M1）。
- Produces: URL name `openapi-draw-latest` → `GET /api/openapi/draw/latest?code=ssq`，返回最新一期 **published** 开奖 `make_response(data={issue,draw_date,numbers,sales_amount,pool_amount,prize_grades})`；未知 code 或无数据返回 `code=1`。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_api_draw_latest.py`:
```python
import pytest
from datetime import date
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                  rule_config={"red": {"count": 6, "min": 1, "max": 33},
                                               "blue": {"count": 1, "min": 1, "max": 16}},
                                  draw_days=[2, 4, 7])


def _mk(ssq, issue, d, status):
    return DrawResult.objects.create(
        lottery=ssq, issue=issue, draw_date=d,
        numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
        pool_amount="1500000000", status=status)


def test_latest_returns_newest_published(client, ssq):
    _mk(ssq, "2026070", date(2026, 6, 18), DrawResult.STATUS_PUBLISHED)
    _mk(ssq, "2026071", date(2026, 6, 20), DrawResult.STATUS_PUBLISHED)
    # 更新的一期还是 draft, 不应被返回
    _mk(ssq, "2026072", date(2026, 6, 22), DrawResult.STATUS_DRAFT)
    resp = client.get("/api/openapi/draw/latest?code=ssq")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["issue"] == "2026071"
    assert body["data"]["pool_amount"] == "1500000000"


def test_latest_unknown_code(client, db):
    resp = client.get("/api/openapi/draw/latest?code=nope")
    assert resp.json()["code"] == 1


def test_latest_missing_code_param(client, db):
    resp = client.get("/api/openapi/draw/latest")
    assert resp.json()["code"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_api_draw_latest.py -v`
Expected: FAIL（404）

- [ ] **Step 3: 追加 DrawLatestView**

在 `lottery_backend/lottery/views.py` 顶部 import 处补充：
```python
from lottery.models import Lottery, DrawResult
from lottery.serializers import LotterySerializer, DrawResultSerializer
```
（替换原来只导入 `Lottery` / `LotterySerializer` 的两行）

追加视图：
```python
def _get_active_lottery(code):
    """按 code 取上架彩种, 不存在返回 None。"""
    if not code:
        return None
    return Lottery.objects.filter(code=code, is_active=True).first()


class DrawLatestView(APIView):
    """GET /api/openapi/draw/latest?code=ssq —— 最新一期已发布开奖。"""

    def get(self, request):
        code = request.query_params.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        draw = (DrawResult.objects
                .filter(lottery=lottery, status=DrawResult.STATUS_PUBLISHED)
                .order_by("-draw_date", "-issue").first())
        if draw is None:
            return Response(make_response(code=1, msg="暂无开奖数据", error=code))
        return Response(make_response(data=DrawResultSerializer(draw).data))
```

- [ ] **Step 4: 追加路由**

`lottery_backend/lottery/urls.py` 的 `urlpatterns` 追加：
```python
    path("draw/latest", views.DrawLatestView.as_view(), name="openapi-draw-latest"),
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_api_draw_latest.py -v`
Expected: PASS，3 passed

- [ ] **Step 6: Commit**

```bash
git add lottery_backend/lottery/views.py lottery_backend/lottery/urls.py lottery_backend/lottery/tests/test_api_draw_latest.py
git commit -m "feat: 当期开奖只读接口"
```

---

### Task 3: 历史开奖接口（分页 + 日期筛选）

**Files:**
- Create: `lottery_backend/lottery/pagination.py`
- Modify: `lottery_backend/lottery/views.py`（追加 DrawHistoryView）
- Modify: `lottery_backend/lottery/urls.py`
- Test: `lottery_backend/lottery/tests/test_api_draw_history.py`

**Interfaces:**
- Consumes: `_get_active_lottery`（Task 2），`DrawResultSerializer`。
- Produces: `lottery.pagination.paginate(qs, page, page_size) -> (items_qs, total, page, page_size)`，`page` 默认 1，`page_size` 默认 20、上限 100。
- Produces: URL name `openapi-draw-history` → `GET /api/openapi/draw/history?code=ssq&page=&page_size=&date_from=&date_to=`，返回 `make_response(data={results:[...], total, page, page_size})`，倒序（draw_date desc, issue desc），仅 published。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_api_draw_history.py`:
```python
import pytest
from datetime import date
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def ssq(db):
    lot = Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                 rule_config={"red": {"count": 6, "min": 1, "max": 33},
                                              "blue": {"count": 1, "min": 1, "max": 16}},
                                 draw_days=[2, 4, 7])
    for i in range(5):  # 2026060..2026064, 日期 6/1..6/5
        DrawResult.objects.create(
            lottery=lot, issue=f"202606{i}", draw_date=date(2026, 6, i + 1),
            numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [i + 1]},
            status=DrawResult.STATUS_PUBLISHED)
    # 一条 draft, 不应出现
    DrawResult.objects.create(lottery=lot, issue="2026099", draw_date=date(2026, 6, 9),
                              numbers={"red": [2, 3, 4, 5, 6, 7], "blue": [1]},
                              status=DrawResult.STATUS_DRAFT)
    return lot


def test_history_pagination(client, ssq):
    resp = client.get("/api/openapi/draw/history?code=ssq&page=1&page_size=2")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["total"] == 5          # 不含 draft
    assert body["data"]["page_size"] == 2
    assert len(body["data"]["results"]) == 2
    # 倒序: 最新 6/5 的 2026064 在前
    assert body["data"]["results"][0]["issue"] == "2026064"


def test_history_date_filter(client, ssq):
    resp = client.get("/api/openapi/draw/history?code=ssq&date_from=2026-06-02&date_to=2026-06-03")
    body = resp.json()
    issues = [r["issue"] for r in body["data"]["results"]]
    assert issues == ["2026062", "2026061"]


def test_history_unknown_code(client, db):
    resp = client.get("/api/openapi/draw/history?code=nope")
    assert resp.json()["code"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_api_draw_history.py -v`
Expected: FAIL（404）

- [ ] **Step 3: 写分页工具**

`lottery_backend/lottery/pagination.py`:
```python
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


def parse_page_params(query_params):
    """从 query 解析 (page, page_size)，非法值回落到默认，page_size 上限 100。"""
    try:
        page = int(query_params.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = int(query_params.get("page_size", DEFAULT_PAGE_SIZE))
    except (TypeError, ValueError):
        page_size = DEFAULT_PAGE_SIZE
    page = max(page, 1)
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    return page, page_size


def paginate(qs, page, page_size):
    """返回 (当前页 queryset 切片, total)。"""
    total = qs.count()
    start = (page - 1) * page_size
    return qs[start:start + page_size], total
```

- [ ] **Step 4: 追加 DrawHistoryView**

在 `lottery_backend/lottery/views.py` 追加 import 与视图：
```python
from lottery.pagination import parse_page_params, paginate
```
```python
class DrawHistoryView(APIView):
    """GET /api/openapi/draw/history —— 历史开奖, 倒序, 分页, 可按日期区间筛选。"""

    def get(self, request):
        code = request.query_params.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        qs = (DrawResult.objects
              .filter(lottery=lottery, status=DrawResult.STATUS_PUBLISHED)
              .order_by("-draw_date", "-issue"))
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(draw_date__gte=date_from)
        if date_to:
            qs = qs.filter(draw_date__lte=date_to)
        page, page_size = parse_page_params(request.query_params)
        items, total = paginate(qs, page, page_size)
        return Response(make_response(data={
            "results": DrawResultSerializer(items, many=True).data,
            "total": total, "page": page, "page_size": page_size,
        }))
```

- [ ] **Step 5: 追加路由**

`lottery_backend/lottery/urls.py` 的 `urlpatterns` 追加：
```python
    path("draw/history", views.DrawHistoryView.as_view(), name="openapi-draw-history"),
```

- [ ] **Step 6: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_api_draw_history.py -v`
Expected: PASS，3 passed

- [ ] **Step 7: Commit**

```bash
git add lottery_backend/lottery/pagination.py lottery_backend/lottery/views.py lottery_backend/lottery/urls.py lottery_backend/lottery/tests/test_api_draw_history.py
git commit -m "feat: 历史开奖只读接口(分页+日期筛选)"
```

---

### Task 4: 奖级文字归一 + 开奖详情接口

**Files:**
- Create: `lottery_backend/lottery/grades.py`
- Modify: `lottery_backend/lottery/serializers.py`（追加 DrawDetailSerializer）
- Modify: `lottery_backend/lottery/views.py`（追加 DrawDetailView）
- Modify: `lottery_backend/lottery/urls.py`
- Test: `lottery_backend/lottery/tests/test_grades.py`
- Test: `lottery_backend/lottery/tests/test_api_draw_detail.py`

**Interfaces:**
- Produces: `lottery.grades.grade_label(level) -> str`：int → 中文序号奖级（1→"一等奖"…），str → 原样返回。
- Produces: `lottery.serializers.DrawDetailSerializer`：在 DrawResult 基础上，把 `prize_grades` 每项补一个 `level_label` 字段（保留原 `level`）。
- Produces: URL name `openapi-draw-detail` → `GET /api/openapi/draw/detail?code=ssq&issue=2026073`，返回单期 published 详情；未知 code 或期号不存在返回 `code=1`。

- [ ] **Step 1: 写 grade_label 失败测试**

`lottery_backend/lottery/tests/test_grades.py`:
```python
from lottery.grades import grade_label


def test_int_levels():
    assert grade_label(1) == "一等奖"
    assert grade_label(6) == "六等奖"


def test_string_level_passthrough():
    assert grade_label("一等奖") == "一等奖"


def test_unknown_int_fallback():
    assert grade_label(99) == "99等奖"
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_grades.py -v`
Expected: FAIL（ModuleNotFoundError: lottery.grades）

- [ ] **Step 3: 实现 grade_label**

`lottery_backend/lottery/grades.py`:
```python
_CN_NUM = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
           6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}


def grade_label(level):
    """奖级文字归一: int → 中文序号奖级; str → 原样返回。"""
    if isinstance(level, bool):  # bool 是 int 子类, 单独挡掉
        return str(level)
    if isinstance(level, int):
        return f"{_CN_NUM.get(level, str(level))}等奖"
    return str(level)
```

- [ ] **Step 4: 运行 grade_label 测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_grades.py -v`
Expected: PASS，3 passed

- [ ] **Step 5: 写详情接口失败测试**

`lottery_backend/lottery/tests/test_api_draw_detail.py`:
```python
import pytest
from datetime import date
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                  rule_config={"red": {"count": 6, "min": 1, "max": 33},
                                               "blue": {"count": 1, "min": 1, "max": 16}},
                                  draw_days=[2, 4, 7])


def test_detail_with_level_label(client, ssq):
    DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22),
        numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
        prize_grades=[{"level": 1, "count": "5", "amount": "8000000"}],
        status=DrawResult.STATUS_PUBLISHED)
    resp = client.get("/api/openapi/draw/detail?code=ssq&issue=2026073")
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["issue"] == "2026073"
    g = body["data"]["prize_grades"][0]
    assert g["level"] == 1
    assert g["level_label"] == "一等奖"
    assert g["amount"] == "8000000"


def test_detail_draft_not_found(client, ssq):
    DrawResult.objects.create(lottery=ssq, issue="2026074", draw_date=date(2026, 6, 24),
                              numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
                              status=DrawResult.STATUS_DRAFT)
    assert client.get("/api/openapi/draw/detail?code=ssq&issue=2026074").json()["code"] == 1


def test_detail_unknown(client, ssq):
    assert client.get("/api/openapi/draw/detail?code=ssq&issue=9999999").json()["code"] == 1
```

- [ ] **Step 6: 追加 DrawDetailSerializer**

`lottery_backend/lottery/serializers.py` 追加（顶部补 `from lottery.grades import grade_label`）：
```python
class DrawDetailSerializer(DrawResultSerializer):
    prize_grades = serializers.SerializerMethodField()

    def get_prize_grades(self, obj):
        return [{**g, "level_label": grade_label(g.get("level"))}
                for g in (obj.prize_grades or [])]
```

- [ ] **Step 7: 追加 DrawDetailView + 路由**

`lottery_backend/lottery/views.py` 追加 import 与视图：
```python
from lottery.serializers import LotterySerializer, DrawResultSerializer, DrawDetailSerializer
```
（替换原 import 行）
```python
class DrawDetailView(APIView):
    """GET /api/openapi/draw/detail?code=ssq&issue=2026073 —— 单期详情(含奖级文字)。"""

    def get(self, request):
        code = request.query_params.get("code")
        issue = request.query_params.get("issue")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        draw = (DrawResult.objects
                .filter(lottery=lottery, issue=issue,
                        status=DrawResult.STATUS_PUBLISHED).first())
        if draw is None:
            return Response(make_response(code=1, msg="期号不存在或未发布", error=str(issue)))
        return Response(make_response(data=DrawDetailSerializer(draw).data))
```
`lottery_backend/lottery/urls.py` 追加：
```python
    path("draw/detail", views.DrawDetailView.as_view(), name="openapi-draw-detail"),
```

- [ ] **Step 8: 运行全部相关测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_grades.py lottery/tests/test_api_draw_detail.py -v`
Expected: PASS，6 passed

- [ ] **Step 9: Commit**

```bash
git add lottery_backend/lottery/grades.py lottery_backend/lottery/serializers.py lottery_backend/lottery/views.py lottery_backend/lottery/urls.py lottery_backend/lottery/tests/test_grades.py lottery_backend/lottery/tests/test_api_draw_detail.py
git commit -m "feat: 开奖详情接口 + 奖级文字归一 level_label"
```

---

### Task 5: 号码出现/遗漏统计接口

**Files:**
- Create: `lottery_backend/lottery/stats.py`
- Modify: `lottery_backend/lottery/views.py`（追加 DrawStatsView）
- Modify: `lottery_backend/lottery/urls.py`
- Test: `lottery_backend/lottery/tests/test_stats.py`
- Test: `lottery_backend/lottery/tests/test_api_draw_stats.py`

**Interfaces:**
- Produces: `lottery.stats.compute_number_stats(rule_config, draws) -> dict`。`draws` 为按时间**从新到旧**排列的号码列表 `[{"red":[...], "blue":[...]}, ...]`。返回 `{"red": [{"number","count","miss"}, ...], "blue": [...]}`，每个区间覆盖 `min..max` 全部号码，按 number 升序。`count`=在窗口内出现次数；`miss`=遗漏值（距上次出现过去了多少期，最新一期出现则 0；窗口内从未出现则 = 窗口期数）。
- Produces: URL name `openapi-draw-stats` → `GET /api/openapi/draw/stats?code=ssq&periods=30`，`periods` 默认 30、上限 100，取最近 N 期 published 计算。

- [ ] **Step 1: 写 compute_number_stats 失败测试**

`lottery_backend/lottery/tests/test_stats.py`:
```python
from lottery.stats import compute_number_stats

RULE = {"red": {"count": 6, "min": 1, "max": 6}, "blue": {"count": 1, "min": 1, "max": 3}}


def test_count_and_miss():
    # 从新到旧 3 期
    draws = [
        {"red": [1, 2, 3, 4, 5, 6], "blue": [1]},  # 最新
        {"red": [1, 2, 3, 4, 5, 6], "blue": [2]},
        {"red": [1, 2, 3, 4, 5, 6], "blue": [3]},  # 最旧
    ]
    res = compute_number_stats(RULE, draws)
    red = {r["number"]: r for r in res["red"]}
    # 红球 1 每期都出, count=3, 最新一期出现 miss=0
    assert red[1]["count"] == 3
    assert red[1]["miss"] == 0
    blue = {b["number"]: b for b in res["blue"]}
    # 蓝球 1 只在最新一期出现: count=1, miss=0
    assert blue[1]["count"] == 1 and blue[1]["miss"] == 0
    # 蓝球 3 只在最旧一期出现: count=1, miss=2 (隔了 2 期没出)
    assert blue[3]["count"] == 1 and blue[3]["miss"] == 2


def test_never_appeared_miss_equals_window():
    draws = [{"red": [1, 2, 3, 4, 5, 6], "blue": [1]}]  # 窗口 1 期
    res = compute_number_stats(RULE, draws)
    blue = {b["number"]: b for b in res["blue"]}
    # 蓝球 2 从未出现: count=0, miss=1 (=窗口期数)
    assert blue[2]["count"] == 0 and blue[2]["miss"] == 1


def test_covers_full_range_sorted():
    res = compute_number_stats(RULE, [{"red": [1, 2, 3, 4, 5, 6], "blue": [1]}])
    assert [r["number"] for r in res["red"]] == [1, 2, 3, 4, 5, 6]
    assert [b["number"] for b in res["blue"]] == [1, 2, 3]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_stats.py -v`
Expected: FAIL（ModuleNotFoundError: lottery.stats）

- [ ] **Step 3: 实现 compute_number_stats**

`lottery_backend/lottery/stats.py`:
```python
def compute_number_stats(rule_config, draws):
    """统计每个号码在窗口内的出现次数与遗漏值。

    draws: 从新到旧的号码列表 [{"red":[...], "blue":[...]}, ...]。
    返回 {"red": [{"number","count","miss"}, ...], "blue": [...]}，号码升序。
    miss = 距上次出现过去的期数(最新一期出现=0)；窗口内未出现=窗口期数。
    """
    window = len(draws)
    result = {}
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        zone_stats = []
        for number in range(rule["min"], rule["max"] + 1):
            count = 0
            miss = window  # 默认: 从未出现
            first_seen = False
            for idx, draw in enumerate(draws):  # idx=0 是最新一期
                if number in draw.get(zone, []):
                    count += 1
                    if not first_seen:
                        miss = idx
                        first_seen = True
            zone_stats.append({"number": number, "count": count, "miss": miss})
        result[zone] = zone_stats
    return result
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_stats.py -v`
Expected: PASS，3 passed

- [ ] **Step 5: 写统计接口失败测试**

`lottery_backend/lottery/tests/test_api_draw_stats.py`:
```python
import pytest
from datetime import date
from rest_framework.test import APIClient
from lottery.models import Lottery, DrawResult


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def ssq(db):
    lot = Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                 rule_config={"red": {"count": 6, "min": 1, "max": 6},
                                              "blue": {"count": 1, "min": 1, "max": 3}},
                                 draw_days=[2, 4, 7])
    for i in range(3):
        DrawResult.objects.create(
            lottery=lot, issue=f"202606{i}", draw_date=date(2026, 6, i + 1),
            numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [i + 1]},
            status=DrawResult.STATUS_PUBLISHED)
    return lot


def test_stats_endpoint(client, ssq):
    resp = client.get("/api/openapi/draw/stats?code=ssq&periods=30")
    body = resp.json()
    assert body["code"] == 0
    red = {r["number"]: r for r in body["data"]["red"]}
    assert red[1]["count"] == 3 and red[1]["miss"] == 0
    blue = {b["number"]: b for b in body["data"]["blue"]}
    # 按日期倒序最新一期是 6/3(blue 3) → blue 3 miss=0; blue 1 在最旧的 6/1, miss=2
    assert blue[3]["count"] == 1 and blue[3]["miss"] == 0
    assert blue[1]["count"] == 1 and blue[1]["miss"] == 2
    assert body["data"]["periods"] == 3  # 实际参与统计的期数


def test_stats_unknown_code(client, db):
    assert client.get("/api/openapi/draw/stats?code=nope").json()["code"] == 1
```

- [ ] **Step 6: 追加 DrawStatsView + 路由**

`lottery_backend/lottery/views.py` 追加 import 与视图：
```python
from lottery.stats import compute_number_stats
```
```python
class DrawStatsView(APIView):
    """GET /api/openapi/draw/stats?code=ssq&periods=30 —— 最近 N 期号码出现/遗漏统计。"""

    def get(self, request):
        code = request.query_params.get("code")
        lottery = _get_active_lottery(code)
        if lottery is None:
            return Response(make_response(code=1, msg="未知彩种", error=f"code={code}"))
        try:
            periods = int(request.query_params.get("periods", 30))
        except (TypeError, ValueError):
            periods = 30
        periods = max(1, min(periods, 100))
        draws = list(DrawResult.objects
                     .filter(lottery=lottery, status=DrawResult.STATUS_PUBLISHED)
                     .order_by("-draw_date", "-issue")[:periods]
                     .values_list("numbers", flat=True))
        stats = compute_number_stats(lottery.rule_config, draws)
        stats["periods"] = len(draws)
        return Response(make_response(data=stats))
```
`lottery_backend/lottery/urls.py` 追加：
```python
    path("draw/stats", views.DrawStatsView.as_view(), name="openapi-draw-stats"),
```

- [ ] **Step 7: 运行统计相关测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_stats.py lottery/tests/test_api_draw_stats.py -v`
Expected: PASS，5 passed

- [ ] **Step 8: 全量回归 + Commit**

Run: `cd lottery_backend && python -m pytest -q`
Expected: 全部 PASS。
```bash
git add lottery_backend/lottery/stats.py lottery_backend/lottery/views.py lottery_backend/lottery/urls.py lottery_backend/lottery/tests/test_stats.py lottery_backend/lottery/tests/test_api_draw_stats.py
git commit -m "feat: 号码出现/遗漏统计接口"
```

---

## 完成定义（M2a）

- 5 个只读接口可用：`lottery/list`、`draw/latest`、`draw/history`、`draw/detail`、`draw/stats`，统一 `{code,msg,data,error}` 返回。
- 所有接口只暴露 `published` 数据，draft 不可见。
- 详情接口的 `prize_grades` 带统一 `level_label`（解决跨彩种奖级类型不一致）。
- 统计接口给出号码出现次数与遗漏值（纯陈列，无预测）。
- `pytest` 全绿。
- 后续 M2b 用 uni-app 消费这些接口做小程序前端。
