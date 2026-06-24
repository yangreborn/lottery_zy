# 历史开奖数据填充 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让爬虫能抓多期，新增 load_history 命令抓约一年真实官方开奖并发布。

**Architecture:** 后端：BaseSpider.run(count) 透传期数给 fetch；新增 load_history 管理命令（spider.run(count) → persist_draw → 发布 published）。复用现有 ssq/dlt spider、persist_draw、SPIDERS 注册。前端不动。

**Tech Stack:** Django 5.2 + DRF；requests（爬虫）；pytest。

## Global Constraints

- 后端日志用 logging（异常 exc_info=True），禁止 print。
- 数据来源真实官方：ssq=cwl.gov.cn（issueCount）、dlt=sporttery.cn（pageSize）；不造假数据。
- `BaseSpider.run(count=1)` 把 count 传给 `fetch`（ssq fetch(issue_count) / dlt fetch(page_size) 第一位置参数）。
- `persist_draw` **不改**（仍写 draft，给常规 crawl_draw 的人工审核流程）；发布只在 load_history 内做：persist 成功的 obj 置 `status=DrawResult.STATUS_PUBLISHED` 并 save。
- load_history 容错：彩种未注册/配置缺失 → warning 跳过；某彩种 run 异常 → error(exc_info) 跳过不影响其他；单条 persist 异常 → 跳过。
- persist_draw 用 `update_or_create(lottery, issue)` 幂等；重跑不重复。
- 单元测试**不打真实网络**（mock spider）；真实抓取由控制端运行验证。
- 后端命令在 `lottery_backend/`（先激活 .venv）；测试 DB Docker lottery_pg 127.0.0.1:5433。

---

## File Structure

- `lottery_backend/crawler/spiders/base.py`(改)：run(count)。
- `lottery_backend/crawler/tests/test_base_run.py`(新)：run 透传 count 测试。
- `lottery_backend/crawler/management/commands/load_history.py`(新)：抓 N 期+发布命令。
- `lottery_backend/crawler/tests/test_load_history.py`(新)：mock spider 的命令测试。

---

### Task 1: BaseSpider.run(count) 透传期数

**Files:**
- Modify: `lottery_backend/crawler/spiders/base.py`
- Test: `lottery_backend/crawler/tests/test_base_run.py`

**Interfaces:**
- Produces: `BaseSpider.run(count=1)` → `self.parse(self.fetch(count))`；fetch/parse 抽象签名不变。

- [ ] **Step 1: 写失败测试**

`lottery_backend/crawler/tests/test_base_run.py`:
```python
from crawler.spiders.base import BaseSpider


class _FakeSpider(BaseSpider):
    lottery_code = "fake"

    def __init__(self):
        self.got = None

    def fetch(self, count=1):
        self.got = count
        return {"x": count}

    def parse(self, raw):
        return [raw]


def test_run_passes_count_to_fetch():
    s = _FakeSpider()
    out = s.run(7)
    assert s.got == 7
    assert out == [{"x": 7}]


def test_run_default_count_1():
    s = _FakeSpider()
    s.run()
    assert s.got == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest crawler/tests/test_base_run.py -v`
Expected: FAIL（run() 当前不接受/不透传 count → `run(7)` TypeError，或 got 仍为 1）

- [ ] **Step 3: 改 run**

`lottery_backend/crawler/spiders/base.py` 的 `run` 由：
```python
    def run(self):
        return self.parse(self.fetch())
```
改为：
```python
    def run(self, count=1):
        return self.parse(self.fetch(count))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest crawler/tests/test_base_run.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: 确认未破坏既有爬虫测试**

Run: `python -m pytest crawler/ -q`
Expected: PASS（既有 spider/persist/crawl_command 测试全绿；crawl_draw 调 run() 默认 count=1 行为不变）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/crawler/spiders/base.py lottery_backend/crawler/tests/test_base_run.py
git commit -m "feat: BaseSpider.run(count) 透传抓取期数"
```

---

### Task 2: load_history 命令（抓 N 期 + 发布）

**Files:**
- Create: `lottery_backend/crawler/management/commands/load_history.py`
- Test: `lottery_backend/crawler/tests/test_load_history.py`

**Interfaces:**
- Consumes: `SPIDERS`(crawler.registry)、`persist_draw`、`Lottery`/`DrawResult`、`BaseSpider.run(count)`
- Produces: 命令 `load_history --count N --code X`；逐彩种 `spider.run(count)` → persist → 发布；幂等；容错。

- [ ] **Step 1: 写失败测试**

`lottery_backend/crawler/tests/test_load_history.py`:
```python
import datetime
import pytest
from django.core.management import call_command
from lottery.models import Lottery, DrawResult
from crawler import registry


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"red": {"count": 6, "min": 1, "max": 33},
                     "blue": {"count": 1, "min": 1, "max": 16}},
        draw_days=[2, 4, 7],
    )


class _FakeSsq:
    lottery_code = "ssq"

    def run(self, count=1):
        return [
            {"issue": "2026070", "draw_date": datetime.date(2026, 6, 20),
             "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
             "sales_amount": "100", "pool_amount": "200",
             "prize_grades": [{"level": 1, "count": 1, "amount": "1000"}]},
            {"issue": "2026071", "draw_date": datetime.date(2026, 6, 23),
             "numbers": {"red": [2, 3, 4, 5, 6, 7], "blue": [8]},
             "sales_amount": "110", "pool_amount": "210", "prize_grades": []},
        ]


def test_load_history_persists_and_publishes(ssq, monkeypatch):
    monkeypatch.setitem(registry.SPIDERS, "ssq", _FakeSsq)
    call_command("load_history", "--code", "ssq", "--count", "2")
    qs = DrawResult.objects.filter(lottery__code="ssq", status=DrawResult.STATUS_PUBLISHED)
    assert qs.count() == 2
    assert set(qs.values_list("issue", flat=True)) == {"2026070", "2026071"}


def test_load_history_idempotent(ssq, monkeypatch):
    monkeypatch.setitem(registry.SPIDERS, "ssq", _FakeSsq)
    call_command("load_history", "--code", "ssq", "--count", "2")
    call_command("load_history", "--code", "ssq", "--count", "2")
    assert DrawResult.objects.filter(lottery__code="ssq").count() == 2


def test_load_history_run_exception_skips(ssq, monkeypatch):
    class _Boom:
        lottery_code = "ssq"

        def run(self, count=1):
            raise RuntimeError("network down")

    monkeypatch.setitem(registry.SPIDERS, "ssq", _Boom)
    call_command("load_history", "--code", "ssq", "--count", "2")  # 不抛
    assert DrawResult.objects.filter(lottery__code="ssq").count() == 0
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest crawler/tests/test_load_history.py -v`
Expected: FAIL（`Unknown command: 'load_history'`）

- [ ] **Step 3: 写命令**

`lottery_backend/crawler/management/commands/load_history.py`:
```python
import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery, DrawResult
from crawler.registry import SPIDERS
from crawler.persist import persist_draw

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "抓取最近 N 期真实开奖并发布(bootstrap 历史数据)。--count 期数 --code 彩种(缺省全部)。"

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=160)
        parser.add_argument("--code", default=None)

    def handle(self, *args, **options):
        count = options["count"]
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
                items = spider_cls().run(count)
            except Exception:
                logger.error("抓取 %s 失败", code, exc_info=True)
                continue
            published = 0
            for item in items:
                try:
                    obj, errors = persist_draw(lottery, item)
                    if obj is not None:
                        obj.status = DrawResult.STATUS_PUBLISHED
                        obj.save(update_fields=["status"])
                        published += 1
                except Exception:
                    logger.error("persist %s %s 失败", code, item.get("issue"), exc_info=True)
            logger.info("load_history %s 发布 %d 期", code, published)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest crawler/tests/test_load_history.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: 全量回归**

Run: `python -m pytest -q`
Expected: PASS（之前 121 + 本里程碑新增，全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/crawler/management/commands/load_history.py lottery_backend/crawler/tests/test_load_history.py
git commit -m "feat: load_history 命令抓 N 期真实开奖并发布"
```

> 真实抓取（约一年真实数据入库）由控制端在合并前验证时执行：`python manage.py load_history --count 160`，确认 ssq/dlt 各入库约一年 published 条数，并经 `/api/openapi/draw/history` 与 `draw/stats` 验证可读。

---

## 计划自检

**1. Spec 覆盖：**
- run(count) 透传期数 → Task 1 ✓
- load_history 命令(抓 N 期 + persist + 发布) → Task 2 ✓
- 容错(彩种缺失/run 异常/单条异常)、幂等 → Task 2 ✓
- persist_draw 不改、发布仅命令内做 → Task 2 ✓
- 真实抓取约一年 → 控制端运行步骤（Task 2 末尾说明）✓
- 前端不动、统计实时算 → 不在改动范围 ✓

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `run(count=1)`(Task1) 被 load_history 的 `spider_cls().run(count)`(Task2) 调用一致。
- `persist_draw(lottery, item) -> (obj|None, errors)`（既有）被 Task2 用：obj 非 None 则发布。
- `DrawResult.STATUS_PUBLISHED`/`SPIDERS`/`Lottery` 既有，引用一致。

**4. 注意点（给执行者）：**
- 单元测试用 `monkeypatch.setitem(registry.SPIDERS, "ssq", FakeClass)` mock，不打真实网络。
- crawl_draw 仍调 `run()`（默认 count=1），run 加默认参数不破坏它——Task1 Step5 验证既有 crawler 测试。
- 发布只在 load_history：`obj.status=published; obj.save(update_fields=["status"])`；persist_draw 保持 draft。
- 真实 160 期抓取是控制端运行步骤，非单元测试；网络不可达时该彩种被跳过不崩。
