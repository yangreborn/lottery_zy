# A2 后端 · 3D/排列三 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 后端支持 3 位有序可重复数字彩（3D/排列三）：zone flag + judge_digit + 爬虫 + seed。

**Architecture:** 在 zone 上加 ordered/allow_repeat，validators 跳过去重、generator 用 choices+不排序；新增 judge_digit（直选/组选），判奖按 play_type="digit" 分派；新增 3d/pl3 爬虫 + seed。复用 A1 的 get_zones 地基，ssq/dlt/kl8 无回归。

**Tech Stack:** Django 5.2 + DRF；requests；pytest。

## Global Constraints

- 日志 logging（异常 exc_info=True），禁止 print；统一 make_response。
- digit zone：`{key:"digits", min:0, max:9, count:3, ordered:true, allow_repeat:true}`；numbers=`{digits:[d1,d2,d3]}` 有序可重复。
- validators：`zone.get("allow_repeat")` 为真 → 跳过不重复校验；个数/范围照常。
- generator：`zone.get("allow_repeat")` → random.choices 否则 random.sample；`zone.get("ordered")` → 不排序否则 sorted。ssq/dlt/kl8 无 flag 行为不变。
- 判奖分派不合并：judge_prize(红蓝)/judge_keno(快乐8)/judge_digit(数字)；NumberCheckView 按 play_type 选用（digit→judge_digit, keno→judge_keno, 否则 judge_prize）。
- judge_digit：直选(list==list)/组选(sorted==sorted，开奖有重复=组三 否则组六)，按 prize_rules type(direct/group3/group6) 取 label/amount。
- 3d/pl3 prize_rules：`[{type:"direct",amount:1040,label:"直选"},{type:"group3",amount:346,label:"组选三"},{type:"group6",amount:173,label:"组选六"}]`。
- 后端在 `lottery_backend/`（先激活 .venv）；测试 DB Docker 5433。

---

## File Structure

- `lottery_backend/lottery/validators.py`(改)：allow_repeat 跳过去重。
- `lottery_backend/usernumber/generator.py`(改)：choices/ordered。
- `lottery_backend/usernumber/judge.py`(改)：judge_digit。
- `lottery_backend/usernumber/views.py`(改)：digit 分派。
- `lottery_backend/lottery/management/commands/seed_lotteries.py`(改)：加 3d/pl3。
- `lottery_backend/crawler/spiders/td.py` `pl3.py`(新) + `crawler/registry.py`(改)。
- 各任务 tests。

---

### Task 1: validators + generator 支持 digit（allow_repeat/ordered）

**Files:**
- Modify: `lottery_backend/lottery/validators.py`、`lottery_backend/usernumber/generator.py`
- Test: `lottery_backend/lottery/tests/test_validators.py`、`lottery_backend/usernumber/tests/test_generator.py`（各追加）

**Interfaces:**
- Produces: validate_numbers 对 allow_repeat 区跳过去重；random_numbers 对 allow_repeat 区 choices、ordered 区不排序。

- [ ] **Step 1: 追加失败测试**

`lottery_backend/lottery/tests/test_validators.py` 末尾追加：
```python
DIGIT_RC = {"play_type": "digit", "zones": [
    {"key": "digits", "label": "数字", "min": 0, "max": 9, "count": 3,
     "ordered": True, "allow_repeat": True}]}


def test_digit_allows_repeat():
    assert validate_numbers(DIGIT_RC, {"digits": [5, 5, 3]}, mode="pick") == []


def test_digit_count_must_be_3():
    assert validate_numbers(DIGIT_RC, {"digits": [1, 2]}, mode="pick") != []


def test_digit_out_of_range():
    assert validate_numbers(DIGIT_RC, {"digits": [1, 2, 10]}, mode="pick") != []
```

`lottery_backend/usernumber/tests/test_generator.py` 末尾追加：
```python
DIGIT_RC = {"play_type": "digit", "zones": [
    {"key": "digits", "min": 0, "max": 9, "count": 3, "ordered": True, "allow_repeat": True}]}


def test_random_digit_length_and_range():
    r = random_numbers(DIGIT_RC)
    assert len(r["digits"]) == 3
    assert all(0 <= d <= 9 for d in r["digits"])


def test_random_digit_not_forced_sorted():
    # 有序区不强制升序：多次抽样应出现至少一次非升序(可重复+乱序)
    seen_unsorted = False
    for _ in range(50):
        d = random_numbers(DIGIT_RC)["digits"]
        if d != sorted(d):
            seen_unsorted = True
            break
    assert seen_unsorted


def test_random_ssq_still_sorted_unique():
    rc = {"red": {"count": 6, "min": 1, "max": 33}, "blue": {"count": 1, "min": 1, "max": 16}}
    r = random_numbers(rc)
    assert r["red"] == sorted(r["red"]) and len(set(r["red"])) == 6
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest lottery/tests/test_validators.py usernumber/tests/test_generator.py -v`
Expected: FAIL（digit [5,5,3] 被判重复；generator 用 sample 不能重复/强制 sorted）

- [ ] **Step 3: 改 validators.py**

`lottery_backend/lottery/validators.py` 第 21-22 行：
```python
        if len(set(nums)) != len(nums):
            errors.append(f"{key} 号码有重复")
```
改为：
```python
        if not zone.get("allow_repeat") and len(set(nums)) != len(nums):
            errors.append(f"{key} 号码有重复")
```

- [ ] **Step 4: 改 generator.py**

`lottery_backend/usernumber/generator.py` 的 random_numbers 整体替换为：
```python
def random_numbers(rule_config, picks=None):
    """按 rule_config 机选。picks={zone_key:n} 指定可变区选几(缺省 pick_max)。
    allow_repeat 区可重复(choices)否则不重复(sample)；ordered 区不排序否则升序。"""
    result = {}
    for zone in get_zones(rule_config):
        n = _pick_count(zone, picks)
        pool = list(range(zone["min"], zone["max"] + 1))
        if zone.get("allow_repeat"):
            nums = random.choices(pool, k=n)
        else:
            nums = random.sample(pool, n)
        result[zone["key"]] = nums if zone.get("ordered") else sorted(nums)
    return result
```

- [ ] **Step 5: 跑测试确认通过 + 全量回归**

Run: `python -m pytest lottery/tests/test_validators.py usernumber/tests/test_generator.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（ssq/dlt/kl8 无 flag → sample+sorted/去重照旧，全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/lottery/validators.py lottery_backend/usernumber/generator.py lottery_backend/lottery/tests/test_validators.py lottery_backend/usernumber/tests/test_generator.py
git commit -m "feat: validators/generator 支持 digit 区(allow_repeat/ordered)"
```

---

### Task 2: judge_digit + 按 play_type 分派

**Files:**
- Modify: `lottery_backend/usernumber/judge.py`、`lottery_backend/usernumber/views.py`
- Test: `lottery_backend/usernumber/tests/test_judge.py`（追加）

**Interfaces:**
- Consumes: prize_rules（digit 用 {type:direct/group3/group6, amount, label}）
- Produces: `judge_digit(rule_config, draw_numbers, user_numbers)`；NumberCheckView 增加 digit 分派。

- [ ] **Step 1: 追加失败测试**

`lottery_backend/usernumber/tests/test_judge.py` 末尾追加（顶部 import 改为 `from usernumber.judge import judge_prize, judge_keno, judge_digit`）：
```python
DIGIT_RC = {"play_type": "digit", "zones": [{"key": "digits", "min": 0, "max": 9, "count": 3}],
            "prize_rules": [
                {"type": "direct", "amount": 1040, "label": "直选"},
                {"type": "group3", "amount": 346, "label": "组选三"},
                {"type": "group6", "amount": 173, "label": "组选六"},
            ]}


def test_digit_direct():
    r = judge_digit(DIGIT_RC, {"digits": [6, 9, 0]}, {"digits": [6, 9, 0]})
    assert r["hit_type"] == "direct" and r["label"] == "直选" and r["amount"] == 1040


def test_digit_group6():
    # 开奖 690 全不同；用户 069 集合相同、顺序不同 → 组选六
    r = judge_digit(DIGIT_RC, {"digits": [6, 9, 0]}, {"digits": [0, 6, 9]})
    assert r["hit_type"] == "group6" and r["amount"] == 173


def test_digit_group3():
    # 开奖 559 有重复；用户 595 集合相同 → 组选三
    r = judge_digit(DIGIT_RC, {"digits": [5, 5, 9]}, {"digits": [5, 9, 5]})
    assert r["hit_type"] == "group3" and r["amount"] == 346


def test_digit_no_win():
    r = judge_digit(DIGIT_RC, {"digits": [6, 9, 0]}, {"digits": [1, 2, 3]})
    assert r["hit_type"] is None and r["label"] == "未中奖"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_judge.py -v`
Expected: FAIL（无 judge_digit）

- [ ] **Step 3: 加 judge_digit**

`lottery_backend/usernumber/judge.py` 末尾追加：
```python
def judge_digit(rule_config, draw_numbers, user_numbers):
    """3D/排列三判奖：直选(完全一致)/组选(集合相同,开奖有重复=组三 否则组六)。"""
    zones = rule_config.get("zones") or []
    key = zones[0]["key"] if zones else "digits"
    user = list(user_numbers.get(key, []))
    drawn = list(draw_numbers.get(key, []))
    rules = {r.get("type"): r for r in rule_config.get("prize_rules", [])}
    matched = None
    if user and user == drawn:
        matched = rules.get("direct")
    elif user and sorted(user) == sorted(drawn):
        matched = rules.get("group3") if len(set(drawn)) < len(drawn) else rules.get("group6")
    label = matched["label"] if matched else "未中奖"
    amount = matched.get("amount", 0) if matched else 0
    hit_type = matched.get("type") if matched else None
    desc = f"{label}命中" if matched else "未中奖"
    return {"hit_type": hit_type, "label": label, "amount": amount, "desc": desc}
```

- [ ] **Step 4: NumberCheckView 加 digit 分派**

`lottery_backend/usernumber/views.py`：
1. 顶部 `from usernumber.judge import judge_prize, judge_keno` 改为 `from usernumber.judge import judge_prize, judge_keno, judge_digit`。
2. 分派块：
```python
        if rc.get("play_type") == "keno":
            result = judge_keno(rc, draw.numbers, rec.numbers)
        else:
            result = judge_prize(rc, draw.numbers, rec.numbers)
```
改为：
```python
        if rc.get("play_type") == "digit":
            result = judge_digit(rc, draw.numbers, rec.numbers)
        elif rc.get("play_type") == "keno":
            result = judge_keno(rc, draw.numbers, rec.numbers)
        else:
            result = judge_prize(rc, draw.numbers, rec.numbers)
```

- [ ] **Step 5: 跑测试确认通过 + 全量回归**

Run: `python -m pytest usernumber/tests/test_judge.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（红蓝/快乐8 判奖不变）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/judge.py lottery_backend/usernumber/views.py lottery_backend/usernumber/tests/test_judge.py
git commit -m "feat: judge_digit 直选/组选 + NumberCheckView digit 分派"
```

---

### Task 3: seed 加 3D/排列三

**Files:**
- Modify: `lottery_backend/lottery/management/commands/seed_lotteries.py`
- Test: `lottery_backend/lottery/tests/test_seed_lotteries.py`（追加）

**Interfaces:**
- Produces: seed 后新增 3d、pl3（play_type=digit + digits zone + 直选/组选 prize）。

- [ ] **Step 1: 追加失败测试**

`lottery_backend/lottery/tests/test_seed_lotteries.py` 末尾追加：
```python
def test_digit_lotteries_seeded(seeded):
    from lottery.zones import get_zones
    for code in ("3d", "pl3"):
        rc = Lottery.objects.get(code=code).rule_config
        assert rc["play_type"] == "digit"
        z = get_zones(rc)[0]
        assert z["key"] == "digits" and z["count"] == 3 and z["max"] == 9
        assert z.get("ordered") and z.get("allow_repeat")
        types = {r["type"] for r in rc["prize_rules"]}
        assert types == {"direct", "group3", "group6"}
```
（说明：复用文件顶部已有的 `seeded` fixture——它 call_command("seed_lotteries")。）

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest lottery/tests/test_seed_lotteries.py -v`
Expected: FAIL（无 3d/pl3）

- [ ] **Step 3: seed 加 3d/pl3**

`lottery_backend/lottery/management/commands/seed_lotteries.py`：
1. 在 `KENO_PRIZES = [...]` 之后、`SEEDS = [` 之前加：
```python
DIGIT_PRIZES = [
    {"type": "direct", "amount": 1040, "label": "直选"},
    {"type": "group3", "amount": 346, "label": "组选三"},
    {"type": "group6", "amount": 173, "label": "组选六"},
]

DIGIT_ZONE = {"key": "digits", "label": "数字", "min": 0, "max": 9, "count": 3,
              "ordered": True, "allow_repeat": True, "color": "#43a047"}
```
2. 在 SEEDS 列表里 kl8 那个 dict 之后、列表结束 `]` 之前，加入两个 dict：
```python
    {
        "code": "3d", "name": "福彩3D", "category": "福彩",
        "rule_config": {"play_type": "digit", "zones": [DIGIT_ZONE], "prize_rules": DIGIT_PRIZES},
        "draw_days": [1, 2, 3, 4, 5, 6, 7],
    },
    {
        "code": "pl3", "name": "排列三", "category": "体彩",
        "rule_config": {"play_type": "digit", "zones": [DIGIT_ZONE], "prize_rules": DIGIT_PRIZES},
        "draw_days": [1, 2, 3, 4, 5, 6, 7],
    },
```

- [ ] **Step 4: 跑测试确认通过 + 全量回归**

Run: `python -m pytest lottery/tests/test_seed_lotteries.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/lottery/management/commands/seed_lotteries.py lottery_backend/lottery/tests/test_seed_lotteries.py
git commit -m "feat: seed 加福彩3D/排列三(digit + 直选组选奖)"
```

---

### Task 4: 3D/排列三 爬虫 + 注册

**Files:**
- Create: `lottery_backend/crawler/spiders/td.py`、`lottery_backend/crawler/spiders/pl3.py`、`lottery_backend/crawler/tests/test_digit_spiders.py`
- Modify: `lottery_backend/crawler/registry.py`

**Interfaces:**
- Consumes: `BaseSpider.run(count)`
- Produces: `TDSpider`(3d, cwl name=3d)、`PL3Spider`(pl3, sporttery gameNo=35)；parse 输出 `{"digits":[d1,d2,d3]}`；SPIDERS 加 3d/pl3。

- [ ] **Step 1: 写失败测试**

`lottery_backend/crawler/tests/test_digit_spiders.py`:
```python
from crawler.spiders.td import TDSpider
from crawler.spiders.pl3 import PL3Spider


def test_3d_parse():
    raw = {"result": [{"code": "2026164", "date": "2026-06-23(二)", "red": "6,9,0"}]}
    items = TDSpider().parse(raw)
    assert len(items) == 1
    assert items[0]["issue"] == "2026164"
    assert items[0]["numbers"] == {"digits": [6, 9, 0]}


def test_3d_parse_skips_bad():
    assert TDSpider().parse({"result": [{"code": "x", "date": "2026-06-23", "red": "a,b"}]}) == []


def test_pl3_parse():
    raw = {"value": {"list": [
        {"lotteryDrawNum": "26164", "lotteryDrawTime": "2026-06-23", "lotteryDrawResult": "7 1 5"}]}}
    items = PL3Spider().parse(raw)
    assert len(items) == 1
    assert items[0]["issue"] == "26164"
    assert items[0]["numbers"] == {"digits": [7, 1, 5]}


def test_pl3_parse_skips_bad():
    assert PL3Spider().parse({"value": {"list": [
        {"lotteryDrawNum": "x", "lotteryDrawTime": "2026-06-23", "lotteryDrawResult": "a b"}]}}) == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest crawler/tests/test_digit_spiders.py -v`
Expected: FAIL（无 td/pl3 模块）

- [ ] **Step 3: 写 td.py（3D，仿 kl8）**

`lottery_backend/crawler/spiders/td.py`:
```python
import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"


class TDSpider(BaseSpider):
    lottery_code = "3d"

    def fetch(self, issue_count=1):
        resp = requests.get(
            API, params={"name": "3d", "issueCount": issue_count},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "http://www.cwl.gov.cn/"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("result", []):
            try:
                digits = [int(x) for x in r["red"].split(",")]
                items.append({
                    "issue": r["code"],
                    "draw_date": datetime.strptime(r["date"][:10], "%Y-%m-%d").date(),
                    "numbers": {"digits": digits},
                    "sales_amount": str(r.get("sales", "")),
                    "pool_amount": str(r.get("poolmoney", "")),
                    "prize_grades": [
                        {"level": g["type"], "count": g["typenum"], "amount": g["typemoney"]}
                        for g in r.get("prizegrades", [])
                    ],
                })
            except Exception:
                logger.error("parse 3d 记录解析失败, 跳过: %r", r.get("code", r), exc_info=True)
                continue
        return items
```

- [ ] **Step 4: 写 pl3.py（排列三，仿 dlt）**

`lottery_backend/crawler/spiders/pl3.py`:
```python
import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry"


class PL3Spider(BaseSpider):
    lottery_code = "pl3"

    def fetch(self, page_size=1):
        resp = requests.get(
            API,
            params={"gameNo": 35, "provinceId": 0, "pageSize": page_size, "isVerify": 1, "pageNo": 1},
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
                "Referer": "https://www.sporttery.cn/",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://www.sporttery.cn",
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("value", {}).get("list", []):
            try:
                digits = [int(x) for x in r["lotteryDrawResult"].split()]
                items.append({
                    "issue": r["lotteryDrawNum"],
                    "draw_date": datetime.strptime(r["lotteryDrawTime"][:10], "%Y-%m-%d").date(),
                    "numbers": {"digits": digits},
                    "sales_amount": str(r.get("totalSaleAmount", "")),
                    "pool_amount": str(r.get("poolBalanceAfterdraw", "")),
                    "prize_grades": [
                        {"level": g["prizeLevel"], "count": g["stakeCount"], "amount": g["stakeAmount"]}
                        for g in r.get("prizeLevelList", [])
                    ],
                })
            except Exception:
                logger.error("parse pl3 记录解析失败, 跳过: %r", r.get("lotteryDrawNum", r), exc_info=True)
                continue
        return items
```

- [ ] **Step 5: 注册**

`lottery_backend/crawler/registry.py` 整体替换为：
```python
from crawler.spiders.ssq import SsqSpider
from crawler.spiders.dlt import DltSpider
from crawler.spiders.kl8 import KL8Spider
from crawler.spiders.td import TDSpider
from crawler.spiders.pl3 import PL3Spider

SPIDERS = {"ssq": SsqSpider, "dlt": DltSpider, "kl8": KL8Spider, "3d": TDSpider, "pl3": PL3Spider}
```

- [ ] **Step 6: 跑测试确认通过 + 全量回归**

Run: `python -m pytest crawler/tests/test_digit_spiders.py -v`
Expected: PASS（4 passed）
Run: `python -m pytest -q`
Expected: PASS（全量全绿）

- [ ] **Step 7: 提交**

```bash
git add lottery_backend/crawler/spiders/td.py lottery_backend/crawler/spiders/pl3.py lottery_backend/crawler/registry.py lottery_backend/crawler/tests/test_digit_spiders.py
git commit -m "feat: 福彩3D(td)/排列三(pl3) 爬虫 + 注册"
```

---

## 计划自检

**1. Spec 覆盖（后端部分）：**
- zone flag allow_repeat/ordered（validators/generator）→ Task 1 ✓
- judge_digit 直选/组选 + play_type 分派 → Task 2 ✓
- seed 3d/pl3 → Task 3 ✓
- 3d/pl3 爬虫 → Task 4 ✓
- 前端位置式选号 + 数字球 → A2-前端计划（后端合并后另写）
- 统计不改（复用数字频次）→ 范围外 ✓
- 真抓 3d/pl3 + 端到端 → 控制端合并前执行

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- digit zone 字段 allow_repeat/ordered(Task1) 与 seed DIGIT_ZONE(Task3)、judge_digit 读 zones[0]["key"]="digits"(Task2) 一致。
- prize_rules type direct/group3/group6 + amount(Task3 seed) 与 judge_digit 匹配键(Task2) 一致。
- spider 输出 {"digits":[...]}（Task4）与 seed digits zone key、judge_digit key 一致。
- random_numbers(rule_config,picks)(Task1) 签名不变，仅内部按 flag 分支；既有 create/generate 调用不受影响。

**4. 注意点（给执行者）：**
- 无回归核心：ssq/dlt/kl8 无 allow_repeat/ordered，validators 去重照旧、generator sample+sorted 照旧；每任务跑全量 `pytest -q`。
- judge_digit 直选优先于组选（if/elif）；空 user 不误判。
- 3d 用 cwl name=3d(仿 kl8)；pl3 用 sporttery gameNo=35(仿 dlt 含反爬请求头)。
- 真实抓取由控制端 `load_history --code 3d --count 100` / `--code pl3 --count 100` 执行（运行步骤，非单测）；单测只测 parse 不打网络。
