# M4b · 运营看板 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 埋点记录访问行为，后台聚合 DAU/热门彩种/功能分布，运营在 Django staff 看板页查看。

**Architecture:** 新建 `stats` app(AccessLog 模型 + 上报接口 + compute_dashboard 聚合 + staff 看板视图 + Admin)。前端加 utils/report.js(fire-and-forget 上报)，App.vue 启动确保匿名 token，各页/关键动作接入埋点。复用 make_response/current_user_id/ensureLogin/request。

**Tech Stack:** Django 5.2 + DRF；uni-app(Vue3+Vite, JS) + vitest。

## Global Constraints

- 埋点身份匿名：App.vue onLaunch 确保 token(loadToken；空则 ensureLogin)；上报带 X-User-Id 头，后端记 user_id(hash)。
- user_id 全程 hash，**不记真实 openid/IP/号码内容**；埋点仅 path/lottery_code/action/时间。
- 返回统一 `make_response`(成功 code=0，应用级错误 code=1 且 HTTP 200)；后端日志 logging 禁止 print。
- 上报 **fire-and-forget**：前端失败静默(.catch(()=>{}))，绝不阻塞用户操作/不弹错。
- action 取值：`view`/`save_number`/`check_number`；AccessLog 常量 ACTION_VIEW/ACTION_SAVE/ACTION_CHECK。
- 看板用服务端渲染表格(无图表库)，`@staff_member_required`；非 staff → 302 重定向。
- 聚合时间窗用 `timezone.now() - timedelta(days)`；UV/DAU 排除空 user_id；热门彩种排除空 lottery_code。
- 前端 uni-app(Vue3) JS 不引 Pinia/Vuex；request code=0 resolve body.data。
- 前端命令在 `lottery_frontend/`；后端命令在 `lottery_backend/`(先激活 .venv)。后端测试 DB Docker lottery_pg 127.0.0.1:5433。端口：后端 8123、前端 5199。

---

## File Structure

- `lottery_backend/stats/__init__.py`、`apps.py`、`models.py`(AccessLog)、`admin.py`、`views.py`(LogCreateView+dashboard_view)、`aggregate.py`(compute_dashboard)、`templates/stats/dashboard.html`(新建 app)
- `lottery_backend/stats/migrations/`(生成)、`stats/tests/`(新)
- `lottery_backend/config/settings.py`(改)：INSTALLED_APPS 加 `stats`
- `lottery_backend/config/urls.py`(改)：加 log 接口 path + dashboard path
- `lottery_frontend/src/utils/report.js`(新)
- `lottery_frontend/src/App.vue`(改)：onLaunch 确保 token
- `lottery_frontend/src/pages/**`(改)：各页接入埋点
- `lottery_frontend/tests/report.test.js`(新)

---

### Task 1: AccessLog 模型 + stats app + Admin

**Files:**
- Create: `lottery_backend/stats/__init__.py`(空)、`stats/apps.py`、`stats/models.py`、`stats/admin.py`
- Create: `lottery_backend/stats/migrations/__init__.py`(空)、`stats/tests/__init__.py`(空)
- Create: `lottery_backend/stats/tests/test_models.py`
- Modify: `lottery_backend/config/settings.py`

**Interfaces:**
- Produces: `stats.models.AccessLog`(user_id/path/lottery_code/action/created_at；常量 ACTION_VIEW="view"/ACTION_SAVE="save_number"/ACTION_CHECK="check_number")；`AccessLogAdmin`。

- [ ] **Step 1: 建 app 骨架 + 注册**

`lottery_backend/stats/apps.py`:
```python
from django.apps import AppConfig


class StatsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "stats"
```

`lottery_backend/config/settings.py` — INSTALLED_APPS 在 `"guide",` 后加一行：
```python
    "guide",
    "stats",
]
```

`stats/__init__.py`、`stats/migrations/__init__.py`、`stats/tests/__init__.py` 均为空文件。

- [ ] **Step 2: 写失败测试**

`lottery_backend/stats/tests/test_models.py`:
```python
import pytest
from stats.models import AccessLog


def test_create_defaults(db):
    log = AccessLog.objects.create(path="draw/latest")
    assert log.user_id == ""
    assert log.lottery_code == ""
    assert log.action == "view"
    assert log.created_at is not None


def test_action_constants():
    assert AccessLog.ACTION_VIEW == "view"
    assert AccessLog.ACTION_SAVE == "save_number"
    assert AccessLog.ACTION_CHECK == "check_number"
```

- [ ] **Step 3: 跑测试确认失败**

Run: `python -m pytest stats/tests/test_models.py -v`
Expected: FAIL（`ModuleNotFoundError: stats.models`）

- [ ] **Step 4: 写模型**

`lottery_backend/stats/models.py`:
```python
from django.db import models


class AccessLog(models.Model):
    """访问埋点。user_id 匿名 hash(可空)；仅记路径/彩种/动作/时间。"""
    ACTION_VIEW = "view"
    ACTION_SAVE = "save_number"
    ACTION_CHECK = "check_number"

    user_id = models.CharField("用户哈希", max_length=64, blank=True, default="", db_index=True)
    path = models.CharField("路径", max_length=100)
    lottery_code = models.CharField("彩种", max_length=20, blank=True, default="")
    action = models.CharField("动作", max_length=20, default=ACTION_VIEW)
    created_at = models.DateTimeField("时间", auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = verbose_name_plural = "访问日志"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} {self.path}"
```

- [ ] **Step 5: 写 Admin**

`lottery_backend/stats/admin.py`:
```python
from django.contrib import admin
from stats.models import AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ("short_user", "path", "lottery_code", "action", "created_at")
    list_filter = ("action", "lottery_code")
    date_hierarchy = "created_at"

    def short_user(self, obj):
        return obj.user_id[:8] if obj.user_id else "(anon)"
    short_user.short_description = "用户"
```

- [ ] **Step 6: 生成迁移**

Run: `python manage.py makemigrations stats`
Expected: 生成 `stats/migrations/0001_initial.py`

- [ ] **Step 7: 跑测试确认通过**

Run: `python -m pytest stats/tests/test_models.py -v`
Expected: PASS（2 passed）

- [ ] **Step 8: 提交**

```bash
git add lottery_backend/stats lottery_backend/config/settings.py
git commit -m "feat: AccessLog 埋点模型 + stats app + Admin"
```

---

### Task 2: 埋点上报接口 POST /api/openapi/log

**Files:**
- Create: `lottery_backend/stats/views.py`
- Modify: `lottery_backend/config/urls.py`
- Test: `lottery_backend/stats/tests/test_log_api.py`

**Interfaces:**
- Consumes: `common.utils.make_response`、`common.auth.current_user_id`、`AccessLog`
- Produces: `LogCreateView`(POST /api/openapi/log)；body `{path, lottery_code?, action?}`；user_id 取 current_user_id(无则空串)；缺 path → code=1。

- [ ] **Step 1: 写失败测试**

`lottery_backend/stats/tests/test_log_api.py`:
```python
import pytest
from rest_framework.test import APIClient
from stats.models import AccessLog


def test_log_with_header(db):
    c = APIClient()
    c.credentials(HTTP_X_USER_ID="tok123")
    resp = c.post("/api/openapi/log",
                  {"path": "draw/latest", "lottery_code": "ssq", "action": "view"}, format="json")
    assert resp.json()["code"] == 0
    log = AccessLog.objects.get()
    assert log.user_id == "tok123"
    assert log.path == "draw/latest"
    assert log.lottery_code == "ssq"
    assert log.action == "view"


def test_log_without_header(db):
    resp = APIClient().post("/api/openapi/log", {"path": "guide/index"}, format="json")
    assert resp.json()["code"] == 0
    log = AccessLog.objects.get()
    assert log.user_id == ""
    assert log.action == "view"


def test_log_missing_path(db):
    resp = APIClient().post("/api/openapi/log", {}, format="json")
    assert resp.json()["code"] == 1
    assert AccessLog.objects.count() == 0
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest stats/tests/test_log_api.py -v`
Expected: FAIL（404 / 视图未定义）

- [ ] **Step 3: 写视图**

`lottery_backend/stats/views.py`:
```python
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
```

- [ ] **Step 4: 挂载路由**

`lottery_backend/config/urls.py` — 顶部 import 区加：
```python
from stats.views import LogCreateView
```
urlpatterns 中，在 `path("api/openapi/guide/", ...)` **之前**加一行：
```python
    path("api/openapi/log", LogCreateView.as_view(), name="openapi-log"),
    path("api/openapi/guide/", include("guide.urls")),
    path("api/openapi/", include("lottery.urls")),
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python -m pytest stats/tests/test_log_api.py -v`
Expected: PASS（3 passed）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/stats/views.py lottery_backend/config/urls.py lottery_backend/stats/tests/test_log_api.py
git commit -m "feat: 埋点上报接口 /api/openapi/log"
```

---

### Task 3: 聚合 compute_dashboard

**Files:**
- Create: `lottery_backend/stats/aggregate.py`
- Test: `lottery_backend/stats/tests/test_aggregate.py`

**Interfaces:**
- Consumes: `AccessLog`
- Produces: `compute_dashboard(days=7) -> {"pv","uv","dau":[{date,count}],"top_lotteries":[{lottery_code,count}],"actions":[{action,count}],"days"}`；UV/DAU 排除空 user_id；热门彩种排除空 lottery_code；时间窗近 days 天。

- [ ] **Step 1: 写失败测试**

`lottery_backend/stats/tests/test_aggregate.py`:
```python
import datetime
import pytest
from django.utils import timezone
from stats.models import AccessLog
from stats.aggregate import compute_dashboard


@pytest.fixture
def logs(db):
    AccessLog.objects.create(user_id="A", path="draw/latest", lottery_code="ssq", action="view")
    AccessLog.objects.create(user_id="A", path="draw/stats", lottery_code="ssq", action="view")
    AccessLog.objects.create(user_id="B", path="guide/index", lottery_code="dlt", action="view")
    AccessLog.objects.create(user_id="", path="draw/latest", lottery_code="ssq", action="view")
    AccessLog.objects.create(user_id="A", path="mine/create", lottery_code="ssq", action="save_number")


def test_pv_uv(logs):
    d = compute_dashboard(7)
    assert d["pv"] == 5
    assert d["uv"] == 2  # A,B；空 user_id 排除


def test_top_lotteries(logs):
    d = compute_dashboard(7)
    top = {r["lottery_code"]: r["count"] for r in d["top_lotteries"]}
    assert top["ssq"] == 4
    assert top["dlt"] == 1


def test_actions(logs):
    d = compute_dashboard(7)
    acts = {r["action"]: r["count"] for r in d["actions"]}
    assert acts["view"] == 4
    assert acts["save_number"] == 1


def test_excludes_old(logs):
    old = AccessLog.objects.create(user_id="C", path="x", lottery_code="ssq", action="view")
    AccessLog.objects.filter(id=old.id).update(
        created_at=timezone.now() - datetime.timedelta(days=30))
    d = compute_dashboard(7)
    assert d["uv"] == 2  # C 超出近 7 天不计


def test_dau_has_today(logs):
    d = compute_dashboard(7)
    assert len(d["dau"]) >= 1
    assert d["dau"][0]["count"] == 2  # 今日 distinct user A,B
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest stats/tests/test_aggregate.py -v`
Expected: FAIL（`ModuleNotFoundError: stats.aggregate`）

- [ ] **Step 3: 写实现**

`lottery_backend/stats/aggregate.py`:
```python
from datetime import timedelta

from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDate

from stats.models import AccessLog


def compute_dashboard(days=7):
    """近 days 天访问聚合：pv/uv/每日 dau/热门彩种/功能分布。"""
    since = timezone.now() - timedelta(days=days)
    qs = AccessLog.objects.filter(created_at__gte=since)

    pv = qs.count()
    uv = qs.exclude(user_id="").values("user_id").distinct().count()

    dau_rows = (qs.exclude(user_id="")
                .annotate(date=TruncDate("created_at"))
                .values("date")
                .annotate(count=Count("user_id", distinct=True))
                .order_by("-date"))
    dau = [{"date": str(r["date"]), "count": r["count"]} for r in dau_rows]

    top_lotteries = [
        {"lottery_code": r["lottery_code"], "count": r["count"]}
        for r in (qs.exclude(lottery_code="")
                  .values("lottery_code")
                  .annotate(count=Count("id"))
                  .order_by("-count"))
    ]

    actions = [
        {"action": r["action"], "count": r["count"]}
        for r in (qs.values("action").annotate(count=Count("id")).order_by("-count"))
    ]

    return {"pv": pv, "uv": uv, "dau": dau,
            "top_lotteries": top_lotteries, "actions": actions, "days": days}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest stats/tests/test_aggregate.py -v`
Expected: PASS（5 passed）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/stats/aggregate.py lottery_backend/stats/tests/test_aggregate.py
git commit -m "feat: 看板聚合 compute_dashboard"
```

---

### Task 4: 看板视图 dashboard + 模板

**Files:**
- Modify: `lottery_backend/stats/views.py`(追加 dashboard_view)
- Create: `lottery_backend/stats/templates/stats/dashboard.html`
- Modify: `lottery_backend/config/urls.py`(加 dashboard path)
- Test: `lottery_backend/stats/tests/test_dashboard_view.py`

**Interfaces:**
- Consumes: `compute_dashboard`、`django.contrib.admin.views.decorators.staff_member_required`
- Produces: `dashboard_view`(GET /dashboard/，staff 渲染表格；非 staff 302)。

- [ ] **Step 1: 写失败测试**

`lottery_backend/stats/tests/test_dashboard_view.py`:
```python
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


def test_dashboard_staff_200(db):
    User.objects.create_superuser("admin", "a@a.com", "pw")
    c = APIClient()
    c.login(username="admin", password="pw")
    resp = c.get("/dashboard/")
    assert resp.status_code == 200
    assert "运营看板" in resp.content.decode()


def test_dashboard_non_staff_redirect(db):
    resp = APIClient().get("/dashboard/")
    assert resp.status_code == 302
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest stats/tests/test_dashboard_view.py -v`
Expected: FAIL（404 / dashboard_view 未定义）

- [ ] **Step 3: 写视图**

`lottery_backend/stats/views.py` — 顶部 import 区追加：
```python
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from stats.aggregate import compute_dashboard
```
文件末尾追加：
```python
@staff_member_required
def dashboard_view(request):
    """GET /dashboard/ —— staff 运营看板(服务端渲染)。"""
    data = compute_dashboard(7)
    return render(request, "stats/dashboard.html", {"data": data})
```

- [ ] **Step 4: 写模板**

`lottery_backend/stats/templates/stats/dashboard.html`:
```html
<!DOCTYPE html>
<html lang="zh-hans">
<head>
  <meta charset="utf-8">
  <title>运营看板</title>
  <style>
    body { font-family: sans-serif; margin: 24px; }
    table { border-collapse: collapse; margin: 12px 0; }
    td, th { border: 1px solid #ddd; padding: 6px 14px; }
    h2 { margin-top: 24px; }
    .kpi { font-size: 20px; }
  </style>
</head>
<body>
  <h1>运营看板（近 {{ data.days }} 天）</h1>
  <p class="kpi">PV：{{ data.pv }}　UV：{{ data.uv }}</p>

  <h2>每日活跃用户（DAU）</h2>
  <table>
    <tr><th>日期</th><th>活跃用户</th></tr>
    {% for r in data.dau %}<tr><td>{{ r.date }}</td><td>{{ r.count }}</td></tr>
    {% empty %}<tr><td colspan="2">暂无数据</td></tr>{% endfor %}
  </table>

  <h2>热门彩种</h2>
  <table>
    <tr><th>彩种</th><th>访问次数</th></tr>
    {% for r in data.top_lotteries %}<tr><td>{{ r.lottery_code }}</td><td>{{ r.count }}</td></tr>
    {% empty %}<tr><td colspan="2">暂无数据</td></tr>{% endfor %}
  </table>

  <h2>功能使用分布</h2>
  <table>
    <tr><th>动作</th><th>次数</th></tr>
    {% for r in data.actions %}<tr><td>{{ r.action }}</td><td>{{ r.count }}</td></tr>
    {% empty %}<tr><td colspan="2">暂无数据</td></tr>{% endfor %}
  </table>
</body>
</html>
```

- [ ] **Step 5: 挂载路由**

`lottery_backend/config/urls.py` — import 区把 `from stats.views import LogCreateView` 改为：
```python
from stats.views import LogCreateView, dashboard_view
```
urlpatterns 追加(与 admin/ 同级即可)：
```python
    path("dashboard/", dashboard_view, name="dashboard"),
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python -m pytest stats/tests/test_dashboard_view.py -v`
Expected: PASS（2 passed）

- [ ] **Step 7: 全量回归**

Run: `python -m pytest -q`
Expected: PASS（之前 98 + 本里程碑新增，全绿）

- [ ] **Step 8: 提交**

```bash
git add lottery_backend/stats/views.py lottery_backend/stats/templates lottery_backend/config/urls.py lottery_backend/stats/tests/test_dashboard_view.py
git commit -m "feat: 运营看板视图 /dashboard/ + 模板"
```

---

### Task 5: 前端上报 util + App.vue 确保匿名 token

**Files:**
- Create: `lottery_frontend/src/utils/report.js`
- Modify: `lottery_frontend/src/App.vue`
- Test: `lottery_frontend/tests/report.test.js`

**Interfaces:**
- Consumes: `request`(api/request)、`loadToken`/`authState`(store/auth)、`ensureLogin`(api/user)
- Produces: `reportAccess(path, opts={}) -> Promise`(POST /api/openapi/log {path,lottery_code,action}，fire-and-forget 静默吞错)；App.vue onLaunch 确保 token。

- [ ] **Step 1: 写失败测试**

`lottery_frontend/tests/report.test.js`:
```js
import { describe, it, expect, beforeEach } from 'vitest'
import { reportAccess } from '../src/utils/report.js'
import { authState } from '../src/store/auth.js'

let captured
function stubUni(ok = true) {
  globalThis.uni = {
    request: (opts) => {
      captured = opts
      if (ok) opts.success({ statusCode: 200, data: { code: 0, msg: 'ok', data: {}, error: null } })
      else opts.fail({ errMsg: 'fail' })
    },
  }
}

describe('reportAccess', () => {
  beforeEach(() => { authState.token = ''; captured = undefined })

  it('POST log 带参数', async () => {
    stubUni(true)
    await reportAccess('draw/latest', { lottery_code: 'ssq', action: 'view' })
    expect(captured.url).toContain('/api/openapi/log')
    expect(captured.method).toBe('POST')
    expect(captured.data).toEqual({ path: 'draw/latest', lottery_code: 'ssq', action: 'view' })
  })

  it('缺省 action=view、lottery_code 空', async () => {
    stubUni(true)
    await reportAccess('guide/index')
    expect(captured.data).toEqual({ path: 'guide/index', lottery_code: '', action: 'view' })
  })

  it('失败被静默吞不抛', async () => {
    stubUni(false)
    await expect(reportAccess('x')).resolves.toBeUndefined()
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（找不到 report.js）

- [ ] **Step 3: 写 report util**

`lottery_frontend/src/utils/report.js`:
```js
import { request } from '../api/request.js'

export function reportAccess(path, opts = {}) {
  return request('/api/openapi/log', {
    method: 'POST',
    data: {
      path,
      lottery_code: opts.lottery_code || '',
      action: opts.action || 'view',
    },
  }).catch(() => {})
}
```

- [ ] **Step 4: 改 App.vue 启动确保 token**

`lottery_frontend/src/App.vue` — 把 `<script>` 整段替换为(在现有 loadToken 基础上增加 ensureLogin 兜底)：
```vue
<script>
import { loadToken, authState } from './store/auth.js'
import { ensureLogin } from './api/user.js'

export default {
  onLaunch: async function () {
    loadToken()
    if (!authState.token) {
      try { await ensureLogin() } catch (e) { /* 匿名登录失败不阻塞启动 */ }
    }
  },
}
</script>
```
（若现有 App.vue 还有 onShow/onHide 钩子，保留它们，仅改 import 与 onLaunch。）

- [ ] **Step 5: 跑测试确认通过**

Run: `npm test`
Expected: PASS（report 全绿；既有单测不破）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/utils/report.js lottery_frontend/src/App.vue lottery_frontend/tests/report.test.js
git commit -m "feat: 前端埋点上报 util + 启动确保匿名 token"
```

---

### Task 6: 各页/关键动作接入埋点

**Files:**
- Modify: `lottery_frontend/src/pages/draw/latest.vue`、`history.vue`、`stats.vue`、`detail.vue`
- Modify: `lottery_frontend/src/pages/guide/index.vue`、`detail.vue`
- Modify: `lottery_frontend/src/pages/mine/index.vue`、`picker.vue`

**Interfaces:**
- Consumes: `reportAccess`(utils/report)、各页已有 `lotteryStore`
- Produces: 页面浏览(action=view)与关键动作(save_number/check_number)埋点。

每个页面：加 `import { reportAccess } from '../../utils/report.js'`（页面都在 `src/pages/<dir>/` 下，相对路径 `../../utils/report.js`），并在对应钩子调用。各页 reportAccess 失败静默(util 已 .catch)，不影响渲染。

- [ ] **Step 1: tab 页接入页面浏览埋点**

`pages/draw/latest.vue`：现有 `onShow(load)` 改为：
```js
onShow(() => { reportAccess('draw/latest', { lottery_code: lotteryStore.code }); load() })
```
（latest 已 import lotteryStore；补 import reportAccess。）

`pages/draw/history.vue`：onShow 回调内首行加：
```js
  reportAccess('draw/history', { lottery_code: lotteryStore.code })
```

`pages/draw/stats.vue`：现有 `onShow(load)` 改为：
```js
onShow(() => { reportAccess('draw/stats', { lottery_code: lotteryStore.code }); load() })
```

`pages/guide/index.vue`：onShow 回调内、`load()` 之前加：
```js
  reportAccess('guide/index', { lottery_code: lotteryStore.code })
```

`pages/mine/index.vue`：onShow 回调内、首行加：
```js
  reportAccess('mine/index', { lottery_code: lotteryStore.code })
```

- [ ] **Step 2: 详情页接入(onLoad)**

`pages/draw/detail.vue`：onLoad 回调内首行加（q 含 code）：
```js
  reportAccess('draw/detail', { lottery_code: q.code })
```

`pages/guide/detail.vue`：onLoad 回调内首行加：
```js
  reportAccess('guide/detail')
```

- [ ] **Step 3: 关键动作埋点**

`pages/mine/picker.vue`：`save(payload)` 里 `createNumber` 成功后(showToast 之后、navigateBack 之前)加：
```js
    reportAccess('mine/create', { lottery_code: code, action: 'save_number' })
```

`pages/mine/index.vue`：`doCheck(id)` 里 `checkNumber` 成功(取得 r 之后、showModal 之前或之后)加：
```js
    reportAccess('mine/check', { lottery_code: store.code, action: 'check_number' })
```

- [ ] **Step 4: build + 端到端目测**

后端：`lottery_backend` 激活 venv → migrate → seed_lotteries → 后台 `runserver 127.0.0.1:8123`；建超级用户(若无)：`python manage.py createsuperuser`(或在 shell 建)。
前端：先 `npm run build:h5`(确认全量编译通过)；再后台 `npm run dev:h5`。
Expected:
- 浏览器开各 tab、存号、比对，后端 AccessLog 产生记录。
- curl 验证上报：`curl -s -XPOST http://127.0.0.1:8123/api/openapi/log -H "Content-Type: application/json" -H "X-User-Id: tok1" -d '{"path":"draw/latest","lottery_code":"ssq","action":"view"}'` → code:0。
- 登录 admin 访问 `http://127.0.0.1:8123/dashboard/` 看 PV/UV/DAU/热门彩种/功能分布表格有数据。
完成后停掉后台进程。

- [ ] **Step 5: 全量前端测试**

Run: `npm test`
Expected: PASS（页面改动不影响既有单测，全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_frontend/src/pages
git commit -m "feat: 各页与关键动作接入埋点上报"
```

---

## 计划自检

**1. Spec 覆盖：**
- AccessLog 模型(user_id/path/lottery_code/action/created_at) → Task 1 ✓
- AccessLog Admin → Task 1 ✓
- 上报接口(header 取 user_id, 缺 path code=1) → Task 2 ✓
- compute_dashboard(pv/uv/dau/热门彩种/action 分布, 排除空) → Task 3 ✓
- staff 看板视图 + 模板(非 staff 302) → Task 4 ✓
- 前端 report util(fire-and-forget) + App.vue 确保 token → Task 5 ✓
- 各页页面浏览 + 2 关键动作埋点 → Task 6 ✓
- 隐私(user_id hash, 无 PII) → 模型/接口仅记 path/code/action ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `AccessLog.ACTION_VIEW/SAVE/CHECK`(Task1) 被聚合测试/接口默认值/前端 action 值一致。
- `current_user_id`(已有，token-header 兜底) 被 LogCreateView 取 user_id。
- `compute_dashboard(days)` 返回结构(Task3) 被 dashboard_view/模板(Task4) 字段一致(pv/uv/dau/top_lotteries/actions/days)。
- `reportAccess(path,opts)`(Task5) 被各页(Task6) 调用一致；data 形如 {path,lottery_code,action}。
- `ensureLogin`/`authState`/`loadToken`(已有 M3b) 被 App.vue(Task5) 引用一致。

**4. 注意点（给执行者）：**
- config/urls：`api/openapi/log` 精确 path 放在 guide/lottery include 之前（精确路径优先于前缀 include，稳妥）。
- 上报 fire-and-forget：report util 必须 `.catch(()=>{})`，页面调用不 await 阻塞渲染（直接调用即可）。
- dashboard 模板放 `stats/templates/stats/dashboard.html`(APP_DIRS=True 自动发现)。
- 看板测试用 `User.objects.create_superuser` + `client.login`；非 staff 期望 302。
- 端到端看板需要 superuser 账号；compute_dashboard 近 7 天窗口，刚埋的点当天可见。
- Task6 是多页 glue 无单测，靠 build:h5 + 端到端(AccessLog 产生 + dashboard 显示)验证。
