# M1 数据底座 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭起 Django 后端，能稳定存储彩种配置与开奖结果，自动爬取双色球/大乐透并校验入库，且管理员可在 Django Admin 手动维护与审核发布。

**Architecture:** Django + DRF 单体后端，PostgreSQL JSONB 存号码/奖级。彩种规则配置化（`rule_config`），号码校验、爬虫解析统一读这份配置。每个彩种一个独立 spider 类（不合并成分发器）。开奖数据 `draft → published` 两态，前端只查 published，脏数据不直面用户。M1 只做"灌库 + 维护"，不含对外查询 API（属 M2）。

**Tech Stack:** Python 3.12 / Django 5.2 LTS / djangorestframework / PostgreSQL 17 / psycopg[binary] / requests / pytest + pytest-django

## Global Constraints

- Python 3.12，Django 5.2 LTS（支持到 2028-04），PostgreSQL 17。
- 日志用 `logging` 标准库（`logging.info/warning/error`），异常记录用 `logging.error(..., exc_info=True)`，**禁止 `print`**。
- **不做收费会员 / 付费 / 支付**：不建 Membership/FeatureFlag 表，不写任何支付逻辑。
- `user_id` 一律以 hash 形式存储与收发，不暴露真实 id（本里程碑暂不涉及用户表，后续遵守）。
- 多 provider（多彩种爬虫）实现保持各自独立函数/类，不合并成分发器。
- 号码、奖级用 JSON 字段，配合 `rule_config` 校验，一张表通吃所有彩种。
- API 返回（后续里程碑）统一 `{code, msg, data, error}` 格式。
- 测试用 pytest + pytest-django，测试文件放 `tests/` 目录下。

---

### Task 1: 项目脚手架与依赖

**Files:**
- Create: `lottery_backend/manage.py`
- Create: `lottery_backend/config/__init__.py`
- Create: `lottery_backend/config/settings.py`
- Create: `lottery_backend/config/urls.py`
- Create: `lottery_backend/config/wsgi.py`
- Create: `requirements.txt`
- Create: `pytest.ini`
- Create: `.gitignore`
- Create: `lottery_backend/.env.example`

**Interfaces:**
- Produces: Django project `config`，settings 从环境变量读取 DB 配置与 `SECRET_KEY`；pytest 可发现 `tests/`。

- [ ] **Step 1: 写依赖文件**

`requirements.txt`:
```
Django==5.2.8
djangorestframework==3.16.0
psycopg[binary]==3.2.3
requests==2.32.3
python-dotenv==1.0.1
pytest==8.3.3
pytest-django==4.9.0
```
> 用 psycopg 3（Django 5.x 推荐），ENGINE 仍为 `django.db.backends.postgresql`，无需改 settings 的 ENGINE。

- [ ] **Step 2: 安装依赖并生成 Django 项目骨架**

Run:
```bash
cd lottery_backend && python -m venv .venv && source .venv/Scripts/activate && pip install -r ../requirements.txt
django-admin startproject config .
```
Expected: 生成 `config/` 与 `manage.py`，无报错。

- [ ] **Step 3: 配置 settings 从环境变量读 DB**

`config/settings.py` 关键改动（替换默认 DATABASES、补 INSTALLED_APPS、读 .env）：
```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-key-change-me")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    # common / lottery / crawler 在各自任务中追加
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "lottery"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_TZ = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}
```

- [ ] **Step 4: 写 .env.example、.gitignore、pytest.ini**

`lottery_backend/.env.example`:
```
SECRET_KEY=change-me
DEBUG=True
DB_NAME=lottery
DB_USER=postgres
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=5432
```

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
db.sqlite3
.pytest_cache/
```

`pytest.ini`:
```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
python_files = tests.py test_*.py *_tests.py
testpaths = lottery_backend
```

- [ ] **Step 5: 验证项目可启动**

Run: `cd lottery_backend && python manage.py check`
Expected: `System check identified no issues`（DB 未建表也应通过 check）。

- [ ] **Step 6: Commit**

```bash
git add lottery_backend requirements.txt pytest.ini .gitignore
git commit -m "chore: Django 项目脚手架与依赖"
```

---

### Task 2: common.make_response 统一返回

**Files:**
- Create: `lottery_backend/common/__init__.py`
- Create: `lottery_backend/common/utils.py`
- Test: `lottery_backend/common/tests/__init__.py`
- Test: `lottery_backend/common/tests/test_utils.py`

**Interfaces:**
- Produces: `make_response(data=None, code=0, msg="ok", error=None) -> dict` 返回 `{"code","msg","data","error"}`。后续所有 API 用它。

- [ ] **Step 1: 写失败测试**

`lottery_backend/common/tests/test_utils.py`:
```python
from common.utils import make_response


def test_make_response_defaults():
    assert make_response() == {"code": 0, "msg": "ok", "data": None, "error": None}


def test_make_response_with_data_and_error():
    r = make_response(data={"a": 1}, code=1, msg="bad", error="boom")
    assert r == {"code": 1, "msg": "bad", "data": {"a": 1}, "error": "boom"}
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest common/tests/test_utils.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'common.utils'`

- [ ] **Step 3: 实现 make_response 并注册 app**

`lottery_backend/common/utils.py`:
```python
def make_response(data=None, code=0, msg="ok", error=None):
    """统一 API 返回结构 {code, msg, data, error}。"""
    return {"code": code, "msg": msg, "data": data, "error": error}
```
创建空的 `common/__init__.py` 与 `common/tests/__init__.py`。在 `config/settings.py` 的 INSTALLED_APPS 追加 `"common",`。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest common/tests/test_utils.py -v`
Expected: PASS，2 passed

- [ ] **Step 5: Commit**

```bash
git add lottery_backend/common
git commit -m "feat: common.make_response 统一返回结构"
```

---

### Task 3: Lottery 彩种模型 + 双色球/大乐透种子数据

**Files:**
- Create: `lottery_backend/lottery/__init__.py`
- Create: `lottery_backend/lottery/apps.py`
- Create: `lottery_backend/lottery/models.py`
- Create: `lottery_backend/lottery/migrations/__init__.py`
- Create: `lottery_backend/lottery/management/__init__.py`
- Create: `lottery_backend/lottery/management/commands/__init__.py`
- Create: `lottery_backend/lottery/management/commands/seed_lotteries.py`
- Test: `lottery_backend/lottery/tests/__init__.py`
- Test: `lottery_backend/lottery/tests/test_models.py`

**Interfaces:**
- Produces: `lottery.models.Lottery`，字段 `code`(唯一), `name`, `category`, `rule_config`(JSON), `draw_days`(JSON list), `is_active`(bool)。
- Produces: `rule_config` 结构约定 `{"red": {"count": int, "min": int, "max": int}, "blue": {"count": int, "min": int, "max": int}}`。
- Produces: `seed_lotteries` 命令插入 ssq/dlt 两条配置。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_models.py`:
```python
import pytest
from django.db import IntegrityError
from lottery.models import Lottery


@pytest.mark.django_db
def test_create_lottery_and_unique_code():
    Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7], is_active=True,
    )
    assert Lottery.objects.get(code="ssq").name == "双色球"
    with pytest.raises(IntegrityError):
        Lottery.objects.create(
            code="ssq", name="重复", category="福彩",
            rule_config={}, draw_days=[],
        )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_models.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'lottery.models'` 或导入错误

- [ ] **Step 3: 实现 Lottery 模型**

`lottery_backend/lottery/models.py`:
```python
from django.db import models


class Lottery(models.Model):
    """彩种配置。号码区规则放 rule_config，加新彩种只插一条数据。"""
    CATEGORY_CHOICES = [("福彩", "福彩"), ("体彩", "体彩")]

    code = models.CharField("彩种标识", max_length=20, unique=True)
    name = models.CharField("名称", max_length=50)
    category = models.CharField("类别", max_length=10, choices=CATEGORY_CHOICES)
    rule_config = models.JSONField("号码规则", default=dict)
    draw_days = models.JSONField("开奖星期", default=list)
    is_active = models.BooleanField("是否上架", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "彩种"

    def __str__(self):
        return f"{self.name}({self.code})"
```
创建 `lottery/apps.py`:
```python
from django.apps import AppConfig


class LotteryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lottery"
```
创建空 `lottery/__init__.py`、`lottery/migrations/__init__.py`、`lottery/tests/__init__.py`。在 `config/settings.py` 的 INSTALLED_APPS 追加 `"lottery",`。

- [ ] **Step 4: 生成迁移并跑测试**

Run:
```bash
cd lottery_backend && python manage.py makemigrations lottery && python -m pytest lottery/tests/test_models.py -v
```
Expected: 迁移生成成功；测试 PASS

- [ ] **Step 5: 写种子命令**

`lottery_backend/lottery/management/commands/seed_lotteries.py`:
```python
import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery

logger = logging.getLogger(__name__)

SEEDS = [
    {
        "code": "ssq", "name": "双色球", "category": "福彩",
        "rule_config": {"red": {"count": 6, "min": 1, "max": 33},
                        "blue": {"count": 1, "min": 1, "max": 16}},
        "draw_days": [2, 4, 7],
    },
    {
        "code": "dlt", "name": "超级大乐透", "category": "体彩",
        "rule_config": {"red": {"count": 5, "min": 1, "max": 35},
                        "blue": {"count": 2, "min": 1, "max": 12}},
        "draw_days": [1, 3, 6],
    },
]


class Command(BaseCommand):
    help = "插入/更新双色球、大乐透彩种配置"

    def handle(self, *args, **options):
        for s in SEEDS:
            obj, created = Lottery.objects.update_or_create(
                code=s["code"], defaults=s
            )
            logger.info("seed lottery %s %s", s["code"], "created" if created else "updated")
```
创建空 `lottery/management/__init__.py`、`lottery/management/commands/__init__.py`。

- [ ] **Step 6: 写种子命令测试**

追加到 `lottery_backend/lottery/tests/test_models.py`:
```python
from django.core.management import call_command


@pytest.mark.django_db
def test_seed_lotteries_idempotent():
    call_command("seed_lotteries")
    call_command("seed_lotteries")  # 再跑一次不应重复
    assert Lottery.objects.count() == 2
    dlt = Lottery.objects.get(code="dlt")
    assert dlt.rule_config["blue"]["count"] == 2
```

- [ ] **Step 7: 跑测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_models.py -v`
Expected: PASS，3 passed

- [ ] **Step 8: Commit**

```bash
git add lottery_backend/lottery
git commit -m "feat: Lottery 彩种模型与双色球/大乐透种子数据"
```

---

### Task 4: 号码校验（读 rule_config）

**Files:**
- Create: `lottery_backend/lottery/validators.py`
- Test: `lottery_backend/lottery/tests/test_validators.py`

**Interfaces:**
- Consumes: `rule_config` 结构（Task 3）。
- Produces: `validate_numbers(rule_config: dict, numbers: dict) -> list[str]` 返回错误信息列表，空列表表示合法。`numbers` 结构 `{"red": [...], "blue": [...]}`。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_validators.py`:
```python
from lottery.validators import validate_numbers

SSQ = {"red": {"count": 6, "min": 1, "max": 33},
       "blue": {"count": 1, "min": 1, "max": 16}}


def test_valid_ssq():
    assert validate_numbers(SSQ, {"red": [1, 5, 12, 20, 28, 33], "blue": [8]}) == []


def test_wrong_count():
    errs = validate_numbers(SSQ, {"red": [1, 5, 12], "blue": [8]})
    assert any("red" in e and "个数" in e for e in errs)


def test_out_of_range():
    errs = validate_numbers(SSQ, {"red": [1, 5, 12, 20, 28, 99], "blue": [8]})
    assert any("范围" in e for e in errs)


def test_duplicate_numbers():
    errs = validate_numbers(SSQ, {"red": [1, 1, 12, 20, 28, 33], "blue": [8]})
    assert any("重复" in e for e in errs)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_validators.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'lottery.validators'`

- [ ] **Step 3: 实现校验**

`lottery_backend/lottery/validators.py`:
```python
def validate_numbers(rule_config, numbers):
    """按 rule_config 校验 numbers，返回错误信息列表，空列表=合法。"""
    errors = []
    for zone in ("red", "blue"):
        rule = rule_config.get(zone)
        if rule is None:
            continue
        nums = numbers.get(zone, [])
        if len(nums) != rule["count"]:
            errors.append(f"{zone} 号码个数应为 {rule['count']}，实际 {len(nums)}")
        if len(set(nums)) != len(nums):
            errors.append(f"{zone} 号码有重复")
        for n in nums:
            if not (rule["min"] <= n <= rule["max"]):
                errors.append(f"{zone} 号码 {n} 超出范围 [{rule['min']},{rule['max']}]")
    return errors
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_validators.py -v`
Expected: PASS，4 passed

- [ ] **Step 5: Commit**

```bash
git add lottery_backend/lottery/validators.py lottery_backend/lottery/tests/test_validators.py
git commit -m "feat: 号码校验 validate_numbers"
```

---

### Task 5: DrawResult 开奖结果模型

**Files:**
- Modify: `lottery_backend/lottery/models.py`（追加 DrawResult）
- Test: `lottery_backend/lottery/tests/test_drawresult.py`

**Interfaces:**
- Consumes: `Lottery`（Task 3）。
- Produces: `lottery.models.DrawResult`，字段 `lottery`(FK), `issue`, `draw_date`, `numbers`(JSON), `sales_amount`, `pool_amount`, `prize_grades`(JSON), `source`('crawler'/'manual'), `status`('draft'/'published'), `updated_by`。`unique_together=(lottery, issue)`。
- Produces: 常量 `DrawResult.SOURCE_CRAWLER='crawler'`, `SOURCE_MANUAL='manual'`, `STATUS_DRAFT='draft'`, `STATUS_PUBLISHED='published'`。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_drawresult.py`:
```python
import pytest
from datetime import date
from django.db import IntegrityError
from lottery.models import Lottery, DrawResult


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_create_drawresult(ssq):
    d = DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22),
        numbers={"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
        pool_amount="1500000000", prize_grades=[{"level": 1, "count": 5, "amount": "8000000"}],
        source=DrawResult.SOURCE_CRAWLER, status=DrawResult.STATUS_DRAFT,
    )
    assert d.status == "draft"
    assert d.numbers["blue"] == [8]


def test_unique_lottery_issue(ssq):
    DrawResult.objects.create(lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22), numbers={})
    with pytest.raises(IntegrityError):
        DrawResult.objects.create(lottery=ssq, issue="2026073", draw_date=date(2026, 6, 22), numbers={})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_drawresult.py -v`
Expected: FAIL，`ImportError: cannot import name 'DrawResult'`

- [ ] **Step 3: 追加 DrawResult 模型**

追加到 `lottery_backend/lottery/models.py`:
```python
class DrawResult(models.Model):
    SOURCE_CRAWLER = "crawler"
    SOURCE_MANUAL = "manual"
    SOURCE_CHOICES = [(SOURCE_CRAWLER, "爬虫"), (SOURCE_MANUAL, "人工")]

    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_CHOICES = [(STATUS_DRAFT, "草稿"), (STATUS_PUBLISHED, "已发布")]

    lottery = models.ForeignKey(Lottery, on_delete=models.CASCADE, related_name="draws", verbose_name="彩种")
    issue = models.CharField("期号", max_length=20)
    draw_date = models.DateField("开奖日期")
    numbers = models.JSONField("开奖号码", default=dict)
    sales_amount = models.CharField("销售额", max_length=30, blank=True, default="")
    pool_amount = models.CharField("奖池金额", max_length=30, blank=True, default="")
    prize_grades = models.JSONField("各奖级", default=list)
    source = models.CharField("来源", max_length=10, choices=SOURCE_CHOICES, default=SOURCE_CRAWLER)
    status = models.CharField("状态", max_length=10, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    updated_by = models.CharField("最后修改人", max_length=50, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "开奖结果"
        unique_together = ("lottery", "issue")
        ordering = ["-draw_date", "-issue"]

    def __str__(self):
        return f"{self.lottery.code} {self.issue}"
```

- [ ] **Step 4: 生成迁移并跑测试**

Run:
```bash
cd lottery_backend && python manage.py makemigrations lottery && python -m pytest lottery/tests/test_drawresult.py -v
```
Expected: 迁移生成；测试 PASS，2 passed

- [ ] **Step 5: Commit**

```bash
git add lottery_backend/lottery
git commit -m "feat: DrawResult 开奖结果模型"
```

---

### Task 6: Django Admin 维护与审核发布

**Files:**
- Create: `lottery_backend/lottery/admin.py`
- Test: `lottery_backend/lottery/tests/test_admin.py`

**Interfaces:**
- Consumes: `Lottery`, `DrawResult`（Task 3/5）。
- Produces: Admin 注册；`DrawResult` admin 含 action `publish_selected`（把选中记录置为 published 并记 updated_by）。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_admin.py`:
```python
import pytest
from datetime import date
from django.contrib.admin.sites import site
from lottery.models import Lottery, DrawResult
from lottery.admin import DrawResultAdmin


@pytest.mark.django_db
def test_models_registered():
    assert Lottery in site._registry
    assert DrawResult in site._registry


@pytest.mark.django_db
def test_publish_action_sets_status():
    lot = Lottery.objects.create(code="ssq", name="双色球", category="福彩",
                                 rule_config={}, draw_days=[])
    d = DrawResult.objects.create(lottery=lot, issue="2026073",
                                  draw_date=date(2026, 6, 22), numbers={},
                                  status=DrawResult.STATUS_DRAFT)
    admin = DrawResultAdmin(DrawResult, site)
    admin.publish_selected(request=None, queryset=DrawResult.objects.filter(pk=d.pk))
    d.refresh_from_db()
    assert d.status == DrawResult.STATUS_PUBLISHED
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_admin.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'lottery.admin'`

- [ ] **Step 3: 实现 admin**

`lottery_backend/lottery/admin.py`:
```python
import logging
from django.contrib import admin
from lottery.models import Lottery, DrawResult

logger = logging.getLogger(__name__)


@admin.register(Lottery)
class LotteryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("code", "name")


@admin.register(DrawResult)
class DrawResultAdmin(admin.ModelAdmin):
    list_display = ("lottery", "issue", "draw_date", "status", "source", "pool_amount")
    list_filter = ("lottery", "status", "source")
    search_fields = ("issue",)
    actions = ["publish_selected"]

    @admin.action(description="发布选中开奖记录")
    def publish_selected(self, request, queryset):
        username = getattr(getattr(request, "user", None), "username", "admin")
        updated = queryset.update(status=DrawResult.STATUS_PUBLISHED, updated_by=username)
        logger.info("published %s draw results by %s", updated, username)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest lottery/tests/test_admin.py -v`
Expected: PASS，2 passed

- [ ] **Step 5: Commit**

```bash
git add lottery_backend/lottery/admin.py lottery_backend/lottery/tests/test_admin.py
git commit -m "feat: 开奖数据 Admin 维护与发布 action"
```

---

### Task 7: 爬虫基类与入库流程

**Files:**
- Create: `lottery_backend/crawler/__init__.py`
- Create: `lottery_backend/crawler/apps.py`
- Create: `lottery_backend/crawler/spiders/__init__.py`
- Create: `lottery_backend/crawler/spiders/base.py`
- Create: `lottery_backend/crawler/persist.py`
- Test: `lottery_backend/crawler/tests/__init__.py`
- Test: `lottery_backend/crawler/tests/test_persist.py`

**Interfaces:**
- Consumes: `Lottery`, `DrawResult`（Task 3/5），`validate_numbers`（Task 4）。
- Produces: `crawler.spiders.base.BaseSpider`，抽象方法 `fetch() -> str|dict`、`parse(raw) -> list[dict]`；具体类设 `lottery_code`。`parse` 返回的每条 dict 结构：`{"issue","draw_date"(date),"numbers","sales_amount","pool_amount","prize_grades"}`。
- Produces: `crawler.persist.persist_draw(lottery, item) -> tuple[DrawResult|None, list[str]]`：校验通过则 update_or_create 写入 `draft`（source=crawler），返回 (对象, [])；校验失败返回 (None, 错误列表) 且不入库。

- [ ] **Step 1: 写失败测试**

`lottery_backend/crawler/tests/test_persist.py`:
```python
import pytest
from datetime import date
from lottery.models import Lottery, DrawResult
from crawler.persist import persist_draw


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_persist_valid_creates_draft(ssq):
    item = {"issue": "2026073", "draw_date": date(2026, 6, 22),
            "numbers": {"red": [1, 5, 12, 20, 28, 33], "blue": [8]},
            "sales_amount": "300000000", "pool_amount": "1500000000",
            "prize_grades": [{"level": 1, "count": 5, "amount": "8000000"}]}
    obj, errs = persist_draw(ssq, item)
    assert errs == []
    assert obj.status == DrawResult.STATUS_DRAFT
    assert obj.source == DrawResult.SOURCE_CRAWLER


def test_persist_invalid_skips(ssq):
    item = {"issue": "2026074", "draw_date": date(2026, 6, 24),
            "numbers": {"red": [1, 5, 12], "blue": [8]}, "prize_grades": []}
    obj, errs = persist_draw(ssq, item)
    assert obj is None
    assert errs
    assert DrawResult.objects.filter(issue="2026074").count() == 0
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_persist.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'crawler.persist'`

- [ ] **Step 3: 实现 base 与 persist**

`lottery_backend/crawler/spiders/base.py`:
```python
from abc import ABC, abstractmethod


class BaseSpider(ABC):
    """每个彩种一个 spider 子类，设 lottery_code，实现 fetch/parse。"""
    lottery_code = None

    @abstractmethod
    def fetch(self):
        """抓取原始数据，返回 str 或 dict。"""

    @abstractmethod
    def parse(self, raw):
        """解析为统一结构 list[dict]。"""

    def run(self):
        return self.parse(self.fetch())
```

`lottery_backend/crawler/persist.py`:
```python
import logging
from lottery.models import DrawResult
from lottery.validators import validate_numbers

logger = logging.getLogger(__name__)


def persist_draw(lottery, item):
    """校验 item 号码，合法则写 draft(crawler)，失败则不入库。返回 (obj|None, errors)。"""
    errors = validate_numbers(lottery.rule_config, item.get("numbers", {}))
    if errors:
        logger.warning("draw %s %s 校验失败，不入库: %s", lottery.code, item.get("issue"), errors)
        return None, errors
    obj, created = DrawResult.objects.update_or_create(
        lottery=lottery, issue=item["issue"],
        defaults={
            "draw_date": item["draw_date"],
            "numbers": item["numbers"],
            "sales_amount": item.get("sales_amount", ""),
            "pool_amount": item.get("pool_amount", ""),
            "prize_grades": item.get("prize_grades", []),
            "source": DrawResult.SOURCE_CRAWLER,
            "status": DrawResult.STATUS_DRAFT,
        },
    )
    logger.info("draw %s %s %s", lottery.code, item["issue"], "created" if created else "updated")
    return obj, []
```
创建空 `crawler/__init__.py`、`crawler/spiders/__init__.py`、`crawler/tests/__init__.py`，及 `crawler/apps.py`:
```python
from django.apps import AppConfig


class CrawlerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "crawler"
```
在 `config/settings.py` 的 INSTALLED_APPS 追加 `"crawler",`。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_persist.py -v`
Expected: PASS，2 passed

- [ ] **Step 5: Commit**

```bash
git add lottery_backend/crawler
git commit -m "feat: 爬虫基类 BaseSpider 与 persist_draw 入库流程"
```

---

### Task 8: 双色球 spider（解析中彩网 JSON）

**Files:**
- Create: `lottery_backend/crawler/spiders/ssq.py`
- Test: `lottery_backend/crawler/tests/test_ssq.py`
- Create: `lottery_backend/crawler/tests/fixtures/ssq_sample.json`

**Interfaces:**
- Consumes: `BaseSpider`（Task 7）。
- Produces: `crawler.spiders.ssq.SsqSpider`，`lottery_code="ssq"`，`fetch()` 请求中彩网接口，`parse(raw_json)` 返回 list[dict]（结构同 Task 7 约定）。

- [ ] **Step 1: 准备 fixture（先抓真实样本核对字段）**

先用浏览器/curl 取一次真实响应核对结构，再保存精简样本到 `lottery_backend/crawler/tests/fixtures/ssq_sample.json`：
```json
{
  "state": 0, "message": "查询成功", "total": 1,
  "result": [
    {
      "name": "双色球", "code": "2026073", "date": "2026-06-22(日)",
      "red": "01,05,12,20,28,33", "blue": "08",
      "sales": "300000000", "poolmoney": "1500000000",
      "prizegrades": [
        {"type": 1, "typenum": "5", "typemoney": "8000000"},
        {"type": 2, "typenum": "100", "typemoney": "200000"}
      ]
    }
  ]
}
```
> 接口参考：`http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=1`。若真实字段名与上方不符，以真实为准同步修改 fixture 与 parse。

- [ ] **Step 2: 写失败测试（只测 parse，不联网）**

`lottery_backend/crawler/tests/test_ssq.py`:
```python
import json
from datetime import date
from pathlib import Path
from crawler.spiders.ssq import SsqSpider

FIXTURE = Path(__file__).parent / "fixtures" / "ssq_sample.json"


def test_parse_ssq():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    items = SsqSpider().parse(raw)
    assert len(items) == 1
    it = items[0]
    assert it["issue"] == "2026073"
    assert it["draw_date"] == date(2026, 6, 22)
    assert it["numbers"] == {"red": [1, 5, 12, 20, 28, 33], "blue": [8]}
    assert it["pool_amount"] == "1500000000"
    assert it["prize_grades"][0] == {"level": 1, "count": "5", "amount": "8000000"}
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_ssq.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'crawler.spiders.ssq'`

- [ ] **Step 4: 实现 SsqSpider**

`lottery_backend/crawler/spiders/ssq.py`:
```python
import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"


class SsqSpider(BaseSpider):
    lottery_code = "ssq"

    def fetch(self, issue_count=1):
        resp = requests.get(
            API, params={"name": "ssq", "issueCount": issue_count},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "http://www.cwl.gov.cn/"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("result", []):
            reds = [int(x) for x in r["red"].split(",")]
            blues = [int(x) for x in r["blue"].split(",")]
            items.append({
                "issue": r["code"],
                "draw_date": datetime.strptime(r["date"][:10], "%Y-%m-%d").date(),
                "numbers": {"red": reds, "blue": blues},
                "sales_amount": str(r.get("sales", "")),
                "pool_amount": str(r.get("poolmoney", "")),
                "prize_grades": [
                    {"level": g["type"], "count": g["typenum"], "amount": g["typemoney"]}
                    for g in r.get("prizegrades", [])
                ],
            })
        return items
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_ssq.py -v`
Expected: PASS，1 passed

- [ ] **Step 6: Commit**

```bash
git add lottery_backend/crawler/spiders/ssq.py lottery_backend/crawler/tests/test_ssq.py lottery_backend/crawler/tests/fixtures/ssq_sample.json
git commit -m "feat: 双色球 spider"
```

---

### Task 9: 大乐透 spider（解析体彩 JSON）

**Files:**
- Create: `lottery_backend/crawler/spiders/dlt.py`
- Test: `lottery_backend/crawler/tests/test_dlt.py`
- Create: `lottery_backend/crawler/tests/fixtures/dlt_sample.json`

**Interfaces:**
- Consumes: `BaseSpider`（Task 7）。
- Produces: `crawler.spiders.dlt.DltSpider`，`lottery_code="dlt"`，`parse(raw_json)` 返回 list[dict]。大乐透号码区 red=前 5 个，blue=后 2 个。

- [ ] **Step 1: 准备 fixture（先抓真实样本核对字段）**

保存精简样本到 `lottery_backend/crawler/tests/fixtures/dlt_sample.json`：
```json
{
  "value": {
    "list": [
      {
        "lotteryDrawNum": "26073",
        "lotteryDrawResult": "01 05 12 20 30 03 07",
        "lotteryDrawTime": "2026-06-22",
        "totalSaleAmount": "200000000",
        "poolBalanceAfterdraw": "800000000",
        "prizeLevelList": [
          {"prizeLevel": "一等奖", "stakeCount": "3", "stakeAmount": "10000000"},
          {"prizeLevel": "二等奖", "stakeCount": "50", "stakeAmount": "200000"}
        ]
      }
    ]
  }
}
```
> 接口参考：`https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=85&provinceId=0&pageSize=1&isVerify=1&pageNo=1`。真实字段以实际为准同步。

- [ ] **Step 2: 写失败测试**

`lottery_backend/crawler/tests/test_dlt.py`:
```python
import json
from datetime import date
from pathlib import Path
from crawler.spiders.dlt import DltSpider

FIXTURE = Path(__file__).parent / "fixtures" / "dlt_sample.json"


def test_parse_dlt():
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    items = DltSpider().parse(raw)
    assert len(items) == 1
    it = items[0]
    assert it["issue"] == "26073"
    assert it["draw_date"] == date(2026, 6, 22)
    assert it["numbers"] == {"red": [1, 5, 12, 20, 30], "blue": [3, 7]}
    assert it["pool_amount"] == "800000000"
    assert it["prize_grades"][0] == {"level": "一等奖", "count": "3", "amount": "10000000"}
```

- [ ] **Step 3: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_dlt.py -v`
Expected: FAIL，`ModuleNotFoundError: No module named 'crawler.spiders.dlt'`

- [ ] **Step 4: 实现 DltSpider**

`lottery_backend/crawler/spiders/dlt.py`:
```python
import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"


class DltSpider(BaseSpider):
    lottery_code = "dlt"

    def fetch(self, page_size=1):
        resp = requests.get(
            API,
            params={"gameNo": 85, "provinceId": 0, "pageSize": page_size, "isVerify": 1, "pageNo": 1},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.sporttery.cn/"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("value", {}).get("list", []):
            nums = [int(x) for x in r["lotteryDrawResult"].split()]
            items.append({
                "issue": r["lotteryDrawNum"],
                "draw_date": datetime.strptime(r["lotteryDrawTime"][:10], "%Y-%m-%d").date(),
                "numbers": {"red": nums[:5], "blue": nums[5:7]},
                "sales_amount": str(r.get("totalSaleAmount", "")),
                "pool_amount": str(r.get("poolBalanceAfterdraw", "")),
                "prize_grades": [
                    {"level": g["prizeLevel"], "count": g["stakeCount"], "amount": g["stakeAmount"]}
                    for g in r.get("prizeLevelList", [])
                ],
            })
        return items
```

- [ ] **Step 5: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_dlt.py -v`
Expected: PASS，1 passed

- [ ] **Step 6: Commit**

```bash
git add lottery_backend/crawler/spiders/dlt.py lottery_backend/crawler/tests/test_dlt.py lottery_backend/crawler/tests/fixtures/dlt_sample.json
git commit -m "feat: 大乐透 spider"
```

---

### Task 10: crawl_draw 管理命令（串起抓取→校验→入库）

**Files:**
- Create: `lottery_backend/crawler/management/__init__.py`
- Create: `lottery_backend/crawler/management/commands/__init__.py`
- Create: `lottery_backend/crawler/management/commands/crawl_draw.py`
- Create: `lottery_backend/crawler/registry.py`
- Test: `lottery_backend/crawler/tests/test_crawl_command.py`

**Interfaces:**
- Consumes: `SsqSpider`, `DltSpider`（Task 8/9），`persist_draw`（Task 7），`Lottery`（Task 3）。
- Produces: `crawler.registry.SPIDERS = {"ssq": SsqSpider, "dlt": DltSpider}`。
- Produces: 命令 `python manage.py crawl_draw --code=ssq`，缺省遍历全部已注册彩种。

- [ ] **Step 1: 写失败测试（mock fetch，不联网）**

`lottery_backend/crawler/tests/test_crawl_command.py`:
```python
import json
import pytest
from pathlib import Path
from unittest import mock
from django.core.management import call_command
from lottery.models import Lottery, DrawResult

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


def test_crawl_draw_ssq(ssq):
    raw = json.loads((FIXTURES / "ssq_sample.json").read_text(encoding="utf-8"))
    with mock.patch("crawler.spiders.ssq.SsqSpider.fetch", return_value=raw):
        call_command("crawl_draw", "--code=ssq")
    d = DrawResult.objects.get(lottery=ssq, issue="2026073")
    assert d.status == DrawResult.STATUS_DRAFT
    assert d.numbers["red"] == [1, 5, 12, 20, 28, 33]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_crawl_command.py -v`
Expected: FAIL，`Unknown command: 'crawl_draw'`

- [ ] **Step 3: 实现 registry 与命令**

`lottery_backend/crawler/registry.py`:
```python
from crawler.spiders.ssq import SsqSpider
from crawler.spiders.dlt import DltSpider

SPIDERS = {"ssq": SsqSpider, "dlt": DltSpider}
```

`lottery_backend/crawler/management/commands/crawl_draw.py`:
```python
import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery
from crawler.registry import SPIDERS
from crawler.persist import persist_draw

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "抓取开奖数据并写入 draft。--code 指定彩种，缺省抓全部。"

    def add_arguments(self, parser):
        parser.add_argument("--code", default=None)

    def handle(self, *args, **options):
        codes = [options["code"]] if options["code"] else list(SPIDERS.keys())
        for code in codes:
            spider_cls = SPIDERS.get(code)
            if spider_cls is None:
                logger.warning("未注册的彩种: %s", code)
                continue
            try:
                lottery = Lottery.objects.get(code=code)
            except Lottery.DoesNotExist:
                logger.warning("彩种配置不存在，请先 seed_lotteries: %s", code)
                continue
            try:
                items = spider_cls().run()
            except Exception:
                logger.error("抓取 %s 失败", code, exc_info=True)
                continue
            for item in items:
                persist_draw(lottery, item)
```
创建空 `crawler/management/__init__.py`、`crawler/management/commands/__init__.py`。

- [ ] **Step 4: 运行测试确认通过**

Run: `cd lottery_backend && python -m pytest crawler/tests/test_crawl_command.py -v`
Expected: PASS，1 passed

- [ ] **Step 5: 全量回归 + 真实联网冒烟**

Run: `cd lottery_backend && python -m pytest -v`
Expected: 全部 PASS。

联网冒烟（手动，验证真实接口与字段映射）：
```bash
cd lottery_backend && python manage.py migrate && python manage.py seed_lotteries && python manage.py crawl_draw --code=ssq && python manage.py crawl_draw --code=dlt
```
Expected: 日志显示 created/updated；若解析报 KeyError，说明真实字段名与 fixture 不符，按真实响应修正对应 spider 的 parse 与 fixture 后重跑测试。

- [ ] **Step 6: Commit**

```bash
git add lottery_backend/crawler
git commit -m "feat: crawl_draw 管理命令串起抓取入库"
```

---

## 完成定义（M1）

- `python manage.py migrate && seed_lotteries && crawl_draw` 能把双色球/大乐透当期数据以 `draft` 入库。
- Django Admin 可查看/编辑开奖号码、奖池、奖金，可手动新增，可一键发布（draft→published）。
- 号码校验拦截非法数据（个数/范围/重复），不污染库。
- `pytest` 全绿。
- 后续 M2 在此基础上加对外只读查询 API 与前端。
