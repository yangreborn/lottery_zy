# A1 后端 · 快乐8 + 区泛化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 后端把 red/blue 写死模型泛化为 zones 列表，并新增快乐8彩种（校验/生成/统计/判奖/种子/爬虫）。

**Architecture:** 引入 `get_zones(rule_config)` 归一化器（新 zones 格式直读，老 red/blue 格式自动转换），validators/generator/stats 改为遍历 get_zones——现有 ssq/dlt 测试不改即保持绿。判奖按 play_type 分派：保留 judge_prize，新增 judge_keno。seed 重写为 zones 并加 kl8；新增 kl8 爬虫。

**Tech Stack:** Django 5.2 + DRF；requests（爬虫）；pytest。

## Global Constraints

- 日志用 logging（异常 exc_info=True），禁止 print；统一 make_response({code,msg,data,error})。
- `get_zones(rule_config)` 归一化：有 `zones` 列表直返；否则按老 red/blue 顶层键转 `[{key,label,...}]`。
- zone 字段：key/label/min/max/count，可选 pick_min/pick_max（用户可变选号个数）、color。
- `validate_numbers(rule_config, numbers, mode="pick")`：mode="draw" 个数==count；mode="pick" 有 pick_min/pick_max 则范围校验，否则==count。persist_draw 传 mode="draw"。
- `random_numbers(rule_config, picks=None)`：picks={zone_key:n} 指定可变区选几，缺省 pick_max；固定区用 count。
- 判奖分派不合并成一个函数：保留 judge_prize(红蓝)，新增 judge_keno(选N中M)；NumberCheckView 按 `rule_config.get("play_type")=="keno"` 选用。两者都返回 label + desc。
- numbers 存储不变（按 zone key 字典）；不做 DB 迁移（rule_config 是 JSONField）。
- 后端在 `lottery_backend/`（先激活 .venv）；测试 DB Docker lottery_pg 127.0.0.1:5433。

---

## File Structure

- `lottery_backend/lottery/zones.py`(新)：get_zones 归一化。
- `lottery_backend/lottery/validators.py`(改)：遍历 get_zones + mode。
- `lottery_backend/crawler/persist.py`(改)：validate 传 mode="draw"。
- `lottery_backend/usernumber/generator.py`(改)：遍历 get_zones + picks。
- `lottery_backend/lottery/stats.py`(改)：遍历 get_zones。
- `lottery_backend/usernumber/judge.py`(改)：judge_prize 加 desc + 新增 judge_keno。
- `lottery_backend/usernumber/views.py`(改)：NumberCheckView 按 play_type 分派。
- `lottery_backend/lottery/management/commands/seed_lotteries.py`(改)：ssq/dlt 重写为 zones + 加 kl8。
- `lottery_backend/crawler/spiders/kl8.py`(新) + `crawler/registry.py`(改)：kl8 爬虫。
- 各任务对应 tests。

---

### Task 1: get_zones 归一化器

**Files:**
- Create: `lottery_backend/lottery/zones.py`、`lottery_backend/lottery/tests/test_zones.py`

**Interfaces:**
- Produces: `get_zones(rule_config) -> list[dict]`，每项含 key + 原 zone 字段。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_zones.py`:
```python
from lottery.zones import get_zones


def test_new_format_zones_passthrough():
    rc = {"zones": [{"key": "main", "label": "号码", "min": 1, "max": 80, "count": 20,
                     "pick_min": 1, "pick_max": 10}]}
    zones = get_zones(rc)
    assert len(zones) == 1
    assert zones[0]["key"] == "main"
    assert zones[0]["pick_max"] == 10


def test_legacy_red_blue_converted():
    rc = {"red": {"count": 6, "min": 1, "max": 33},
          "blue": {"count": 1, "min": 1, "max": 16}}
    zones = get_zones(rc)
    assert [z["key"] for z in zones] == ["red", "blue"]
    assert zones[0]["count"] == 6 and zones[0]["min"] == 1 and zones[0]["max"] == 33
    assert zones[0]["label"] == "红球" and zones[1]["label"] == "蓝球"


def test_legacy_single_red_only():
    rc = {"red": {"count": 5, "min": 1, "max": 35}}
    zones = get_zones(rc)
    assert [z["key"] for z in zones] == ["red"]


def test_empty():
    assert get_zones({}) == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest lottery/tests/test_zones.py -v`
Expected: FAIL（无 zones 模块）

- [ ] **Step 3: 写实现**

`lottery_backend/lottery/zones.py`:
```python
_LEGACY_LABELS = {"red": "红球", "blue": "蓝球"}


def get_zones(rule_config):
    """返回标准化区列表 [{key,label,min,max,count,...}]。
    新格式直读 rule_config['zones']；老格式(red/blue 顶层键)自动转换。"""
    zones = rule_config.get("zones")
    if isinstance(zones, list):
        return zones
    result = []
    for key in ("red", "blue"):
        rule = rule_config.get(key)
        if rule is None:
            continue
        zone = dict(rule)
        zone["key"] = key
        zone.setdefault("label", _LEGACY_LABELS[key])
        result.append(zone)
    return result
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest lottery/tests/test_zones.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/lottery/zones.py lottery_backend/lottery/tests/test_zones.py
git commit -m "feat: get_zones 归一化器(新zones格式+老red/blue兼容)"
```

---

### Task 2: validators 遍历 zones + mode

**Files:**
- Modify: `lottery_backend/lottery/validators.py`、`lottery_backend/crawler/persist.py`
- Test: `lottery_backend/lottery/tests/test_validators.py`（追加）

**Interfaces:**
- Consumes: `get_zones`（Task1）
- Produces: `validate_numbers(rule_config, numbers, mode="pick")`

- [ ] **Step 1: 追加失败测试**

在 `lottery_backend/lottery/tests/test_validators.py` 末尾追加：
```python
KENO_RC = {"zones": [{"key": "main", "label": "号码", "min": 1, "max": 80,
                      "count": 20, "pick_min": 1, "pick_max": 10}], "play_type": "keno"}


def test_keno_pick_within_range_ok():
    assert validate_numbers(KENO_RC, {"main": [1, 2, 3, 4, 5]}, mode="pick") == []


def test_keno_pick_too_many():
    errs = validate_numbers(KENO_RC, {"main": list(range(1, 12))}, mode="pick")  # 11 个
    assert errs != []


def test_keno_draw_must_be_20():
    assert validate_numbers(KENO_RC, {"main": list(range(1, 21))}, mode="draw") == []
    assert validate_numbers(KENO_RC, {"main": [1, 2, 3]}, mode="draw") != []


def test_keno_pick_out_of_value_range():
    assert validate_numbers(KENO_RC, {"main": [99]}, mode="pick") != []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest lottery/tests/test_validators.py -v`
Expected: FAIL（validate_numbers 不接受 mode / 不识别 zones）

- [ ] **Step 3: 改 validators.py**

`lottery_backend/lottery/validators.py` 整体替换为：
```python
from lottery.zones import get_zones


def validate_numbers(rule_config, numbers, mode="pick"):
    """按 rule_config 校验 numbers，返回错误信息列表，空列表=合法。
    mode='draw' 校验开奖号(个数==count)；mode='pick' 校验用户选号(可变区用 pick_min/pick_max)。"""
    if not isinstance(numbers, dict):
        return ["号码格式应为字典"]
    errors = []
    for zone in get_zones(rule_config):
        key = zone["key"]
        nums = numbers.get(key, [])
        if not isinstance(nums, list):
            errors.append(f"{key} 号码格式应为列表")
            continue
        if mode == "pick" and "pick_min" in zone and "pick_max" in zone:
            if not (zone["pick_min"] <= len(nums) <= zone["pick_max"]):
                errors.append(f"{key} 选号个数应为 {zone['pick_min']}-{zone['pick_max']}，实际 {len(nums)}")
        elif len(nums) != zone["count"]:
            errors.append(f"{key} 号码个数应为 {zone['count']}，实际 {len(nums)}")
        if len(set(nums)) != len(nums):
            errors.append(f"{key} 号码有重复")
        for n in nums:
            if not (zone["min"] <= n <= zone["max"]):
                errors.append(f"{key} 号码 {n} 超出范围 [{zone['min']},{zone['max']}]")
    return errors
```

- [ ] **Step 4: persist_draw 传 mode="draw"**

`lottery_backend/crawler/persist.py` 第 10 行：
```python
    errors = validate_numbers(lottery.rule_config, item.get("numbers", {}))
```
改为：
```python
    errors = validate_numbers(lottery.rule_config, item.get("numbers", {}), mode="draw")
```

- [ ] **Step 5: 跑测试确认通过 + 全量回归**

Run: `python -m pytest lottery/tests/test_validators.py -v`
Expected: PASS（含既有 + 4 新增）
Run: `python -m pytest -q`
Expected: PASS（既有全绿——ssq/dlt 老格式经 get_zones 转换行为不变；persist draw 校验 ssq count=6 不变）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/lottery/validators.py lottery_backend/crawler/persist.py lottery_backend/lottery/tests/test_validators.py
git commit -m "feat: validate_numbers 遍历 zones + draw/pick 双 mode"
```

---

### Task 3: generator 遍历 zones + picks

**Files:**
- Modify: `lottery_backend/usernumber/generator.py`
- Test: `lottery_backend/usernumber/tests/test_generator.py`（追加；无则新建）

**Interfaces:**
- Consumes: `get_zones`
- Produces: `random_numbers(rule_config, picks=None)`、`dan_random_numbers(rule_config, dan_numbers)`

- [ ] **Step 1: 追加失败测试**

在 `lottery_backend/usernumber/tests/test_generator.py`（无则新建，顶部 `from usernumber.generator import random_numbers`）追加：
```python
KENO_RC = {"zones": [{"key": "main", "min": 1, "max": 80, "count": 20,
                      "pick_min": 1, "pick_max": 10}], "play_type": "keno"}


def test_random_keno_uses_picks():
    r = random_numbers(KENO_RC, picks={"main": 5})
    assert len(r["main"]) == 5
    assert all(1 <= n <= 80 for n in r["main"])
    assert len(set(r["main"])) == 5  # 不重复


def test_random_keno_default_pick_max():
    r = random_numbers(KENO_RC)  # 不传 picks → pick_max=10
    assert len(r["main"]) == 10


def test_random_keno_clamps():
    assert len(random_numbers(KENO_RC, picks={"main": 99})["main"]) == 10  # 夹到 pick_max
    assert len(random_numbers(KENO_RC, picks={"main": 0})["main"]) == 1    # 夹到 pick_min


def test_random_ssq_legacy_unchanged():
    rc = {"red": {"count": 6, "min": 1, "max": 33}, "blue": {"count": 1, "min": 1, "max": 16}}
    r = random_numbers(rc)
    assert len(r["red"]) == 6 and len(r["blue"]) == 1
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_generator.py -v`
Expected: FAIL（random_numbers 不接受 picks / 不识别 zones）

- [ ] **Step 3: 改 generator.py**

`lottery_backend/usernumber/generator.py` 整体替换为：
```python
import random
from lottery.zones import get_zones


def _pick_count(zone, picks):
    if "pick_min" in zone and "pick_max" in zone:
        n = (picks or {}).get(zone["key"], zone["pick_max"])
        return max(zone["pick_min"], min(n, zone["pick_max"]))
    return zone["count"]


def random_numbers(rule_config, picks=None):
    """按 rule_config 机选，每区取若干不重复号码升序返回。
    picks: 可选 {zone_key: n}，指定可变区(pick_min/pick_max)选几;缺省取 pick_max。固定区用 count。"""
    result = {}
    for zone in get_zones(rule_config):
        n = _pick_count(zone, picks)
        result[zone["key"]] = sorted(random.sample(range(zone["min"], zone["max"] + 1), n))
    return result


def dan_random_numbers(rule_config, dan_numbers):
    """定胆随机：锁定胆码，剩余位从未选号码池随机补全；胆码非法抛 ValueError。"""
    result = {}
    for zone in get_zones(rule_config):
        key = zone["key"]
        dans = list(dict.fromkeys(dan_numbers.get(key, [])))  # 去重保序
        count = zone["count"]
        for d in dans:
            if not (zone["min"] <= d <= zone["max"]):
                raise ValueError(f"{key} 胆码 {d} 超出范围 [{zone['min']},{zone['max']}]")
        if len(dans) > count:
            raise ValueError(f"{key} 胆码数量 {len(dans)} 超过该区号码数 {count}")
        pool = [n for n in range(zone["min"], zone["max"] + 1) if n not in dans]
        picks = dans + random.sample(pool, count - len(dans))
        result[key] = sorted(picks)
    return result
```

- [ ] **Step 4: 跑测试确认通过 + 全量回归**

Run: `python -m pytest usernumber/tests/test_generator.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（ssq/dlt 机选/定胆经 get_zones 行为不变；number_create/generate 用默认 picks=None 不变）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/usernumber/generator.py lottery_backend/usernumber/tests/test_generator.py
git commit -m "feat: random_numbers 遍历 zones + picks 可变选号个数"
```

---

### Task 4: stats 遍历 zones

**Files:**
- Modify: `lottery_backend/lottery/stats.py`
- Test: `lottery_backend/lottery/tests/test_stats.py`（追加；无则新建）

**Interfaces:**
- Consumes: `get_zones`
- Produces: `compute_number_stats(rule_config, draws)`（返回键由 zone key 决定）

- [ ] **Step 1: 追加失败测试**

在 `lottery_backend/lottery/tests/test_stats.py`（无则新建，顶部 `from lottery.stats import compute_number_stats`）追加：
```python
def test_stats_keno_single_zone():
    rc = {"zones": [{"key": "main", "min": 1, "max": 80, "count": 20}], "play_type": "keno"}
    draws = [{"main": [1, 2, 3]}, {"main": [1, 5, 80]}]
    res = compute_number_stats(rc, draws)
    assert "main" in res and "red" not in res
    cells = {c["number"]: c for c in res["main"]}
    assert cells[1]["count"] == 2   # 两期都有 1
    assert cells[1]["miss"] == 0    # 最新一期(idx0)出现
    assert cells[80]["count"] == 1
    assert len(res["main"]) == 80


def test_stats_ssq_legacy_unchanged():
    rc = {"red": {"min": 1, "max": 33, "count": 6}, "blue": {"min": 1, "max": 16, "count": 1}}
    res = compute_number_stats(rc, [{"red": [1, 2, 3, 4, 5, 6], "blue": [7]}])
    assert "red" in res and "blue" in res
    assert len(res["red"]) == 33 and len(res["blue"]) == 16
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest lottery/tests/test_stats.py -v`
Expected: FAIL（keno 用例：res 无 "main"，因 stats 写死 red/blue）

- [ ] **Step 3: 改 stats.py**

`lottery_backend/lottery/stats.py` 整体替换为：
```python
from lottery.zones import get_zones


def compute_number_stats(rule_config, draws):
    """统计每个号码在窗口内的出现次数与遗漏值。

    draws: 从新到旧的号码列表 [{zone_key:[...]}, ...]。
    返回 {zone_key: [{"number","count","miss"}, ...]}，号码升序。
    miss = 距上次出现过去的期数(最新一期出现=0)；窗口内未出现=窗口期数。
    """
    window = len(draws)
    result = {}
    for zone in get_zones(rule_config):
        key = zone["key"]
        lo, hi = zone.get("min"), zone.get("max")
        if lo is None or hi is None:
            continue
        zone_stats = []
        for number in range(lo, hi + 1):
            count = 0
            miss = window  # 默认: 从未出现
            first_seen = False
            for idx, draw in enumerate(draws):  # idx=0 是最新一期
                if number in draw.get(key, []):
                    count += 1
                    if not first_seen:
                        miss = idx
                        first_seen = True
            zone_stats.append({"number": number, "count": count, "miss": miss})
        result[key] = zone_stats
    return result
```

- [ ] **Step 4: 跑测试确认通过 + 全量回归**

Run: `python -m pytest lottery/tests/test_stats.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（ssq/dlt 统计经 get_zones 行为不变）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/lottery/stats.py lottery_backend/lottery/tests/test_stats.py
git commit -m "feat: compute_number_stats 遍历 zones"
```

---

### Task 5: judge_keno + 按 play_type 分派

**Files:**
- Modify: `lottery_backend/usernumber/judge.py`、`lottery_backend/usernumber/views.py`
- Test: `lottery_backend/usernumber/tests/test_judge.py`（追加；无则新建）

**Interfaces:**
- Consumes: prize_rules（red/blue 用 {red,blue,level}；keno 用 {pick,hit,label,amount}）
- Produces: `judge_prize(...)`(加 desc)、`judge_keno(rule_config, draw_numbers, user_numbers)`；NumberCheckView 按 play_type 分派。

- [ ] **Step 1: 追加失败测试**

在 `lottery_backend/usernumber/tests/test_judge.py`（无则新建，顶部 `from usernumber.judge import judge_prize, judge_keno`）追加：
```python
KENO_RC = {"play_type": "keno", "zones": [{"key": "main", "min": 1, "max": 80, "count": 20}],
           "prize_rules": [
               {"pick": 5, "hit": 5, "level": 1, "label": "选五中五", "amount": 1000},
               {"pick": 5, "hit": 4, "level": 2, "label": "选五中四", "amount": 21},
               {"pick": 5, "hit": 3, "level": 3, "label": "选五中三", "amount": 3},
           ]}


def test_keno_hit_all():
    draw = {"main": [1, 2, 3, 4, 5] + list(range(10, 25))}  # 含 1-5
    r = judge_keno(KENO_RC, draw, {"main": [1, 2, 3, 4, 5]})
    assert r["pick"] == 5 and r["hit"] == 5
    assert r["label"] == "选五中五" and r["amount"] == 1000
    assert r["desc"] == "选5中5"


def test_keno_partial_hit():
    draw = {"main": [1, 2, 3] + list(range(30, 47))}  # 含 1,2,3 不含 4,5
    r = judge_keno(KENO_RC, draw, {"main": [1, 2, 3, 4, 5]})
    assert r["hit"] == 3 and r["label"] == "选五中三"


def test_keno_no_win():
    draw = {"main": list(range(40, 60))}  # 不含 1-5
    r = judge_keno(KENO_RC, draw, {"main": [1, 2, 3, 4, 5]})
    assert r["hit"] == 0 and r["label"] == "未中奖"


def test_prize_has_desc():
    rc = {"red": {"count": 6, "min": 1, "max": 33}, "blue": {"count": 1, "min": 1, "max": 16},
          "prize_rules": [{"level": 1, "red": 6, "blue": 1}]}
    r = judge_prize(rc, {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
                    {"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    assert r["level"] == 1 and r["desc"] == "命中 红6 蓝1"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest usernumber/tests/test_judge.py -v`
Expected: FAIL（无 judge_keno / judge_prize 无 desc）

- [ ] **Step 3: 改 judge.py**

`lottery_backend/usernumber/judge.py` 整体替换为：
```python
from lottery.grades import grade_label


def judge_prize(rule_config, draw_numbers, user_numbers):
    """红蓝判奖：各区命中数按 prize_rules {red,blue} 匹配，取最小 level(最高奖)。"""
    red_hit = len(set(user_numbers.get("red", [])) & set(draw_numbers.get("red", [])))
    blue_hit = len(set(user_numbers.get("blue", [])) & set(draw_numbers.get("blue", [])))
    level = None
    for rule in rule_config.get("prize_rules", []):
        if rule.get("red") == red_hit and rule.get("blue") == blue_hit:
            if level is None or rule["level"] < level:
                level = rule["level"]
    label = grade_label(level) if level is not None else "未中奖"
    return {"red_hit": red_hit, "blue_hit": blue_hit, "level": level, "label": label,
            "desc": f"命中 红{red_hit} 蓝{blue_hit}"}


def judge_keno(rule_config, draw_numbers, user_numbers):
    """快乐8判奖：选 N 中 M，按 prize_rules {pick,hit} 匹配固定奖。"""
    zones = rule_config.get("zones") or []
    main_key = zones[0]["key"] if zones else "main"
    user = user_numbers.get(main_key, [])
    drawn = draw_numbers.get(main_key, [])
    pick = len(user)
    hit = len(set(user) & set(drawn))
    matched = None
    for rule in rule_config.get("prize_rules", []):
        if rule.get("pick") == pick and rule.get("hit") == hit:
            matched = rule
            break
    label = matched["label"] if matched else "未中奖"
    amount = matched.get("amount", 0) if matched else 0
    level = matched.get("level") if matched else None
    return {"hit": hit, "pick": pick, "level": level, "label": label, "amount": amount,
            "desc": f"选{pick}中{hit}"}
```

- [ ] **Step 4: NumberCheckView 分派**

`lottery_backend/usernumber/views.py`：
1. 顶部 import 行 `from usernumber.judge import judge_prize` 改为 `from usernumber.judge import judge_prize, judge_keno`。
2. NumberCheckView 中：
```python
        result = judge_prize(rec.lottery.rule_config, draw.numbers, rec.numbers)
        return Response(make_response(data=result))
```
改为：
```python
        rc = rec.lottery.rule_config
        if rc.get("play_type") == "keno":
            result = judge_keno(rc, draw.numbers, rec.numbers)
        else:
            result = judge_prize(rc, draw.numbers, rec.numbers)
        return Response(make_response(data=result))
```

- [ ] **Step 5: 跑测试确认通过 + 全量回归**

Run: `python -m pytest usernumber/tests/test_judge.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（红蓝判奖逻辑不变，仅加 desc 字段；既有 check 测试若断言 result 仅多 desc 不受影响）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/usernumber/judge.py lottery_backend/usernumber/views.py lottery_backend/usernumber/tests/test_judge.py
git commit -m "feat: judge_keno 选N中M + NumberCheckView 按 play_type 分派"
```

---

### Task 6: seed 重写为 zones + 加快乐8

**Files:**
- Modify: `lottery_backend/lottery/management/commands/seed_lotteries.py`
- Test: `lottery_backend/lottery/tests/test_seed_lotteries.py`（新建）

**Interfaces:**
- Produces: seed 后 ssq/dlt rule_config 为 zones 格式；新增 kl8（play_type=keno + 选N中M prize 表）。

- [ ] **Step 1: 写失败测试**

`lottery_backend/lottery/tests/test_seed_lotteries.py`:
```python
import pytest
from django.core.management import call_command
from lottery.models import Lottery
from lottery.zones import get_zones


@pytest.fixture
def seeded(db):
    call_command("seed_lotteries")


def test_ssq_zones_format(seeded):
    rc = Lottery.objects.get(code="ssq").rule_config
    zones = get_zones(rc)
    assert [z["key"] for z in zones] == ["red", "blue"]
    assert zones[0]["count"] == 6 and zones[1]["count"] == 1


def test_kl8_seeded(seeded):
    kl8 = Lottery.objects.get(code="kl8")
    rc = kl8.rule_config
    assert rc["play_type"] == "keno"
    z = get_zones(rc)[0]
    assert z["key"] == "main" and z["max"] == 80 and z["count"] == 20
    assert z["pick_min"] == 1 and z["pick_max"] == 10
    # 选十中十在奖表里
    assert any(r["pick"] == 10 and r["hit"] == 10 for r in rc["prize_rules"])
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest lottery/tests/test_seed_lotteries.py -v`
Expected: FAIL（ssq 仍老格式无 zones / 无 kl8）

- [ ] **Step 3: 重写 seed_lotteries.py**

`lottery_backend/lottery/management/commands/seed_lotteries.py` 整体替换为：
```python
import logging
from django.core.management.base import BaseCommand
from lottery.models import Lottery

logger = logging.getLogger(__name__)

# 快乐8 选N中M 固定奖金表(官方)
KENO_PRIZES = [
    {"pick": 1, "hit": 1, "amount": 4.6, "label": "选一中一"},
    {"pick": 2, "hit": 2, "amount": 19, "label": "选二中二"},
    {"pick": 3, "hit": 3, "amount": 53, "label": "选三中三"},
    {"pick": 3, "hit": 2, "amount": 3, "label": "选三中二"},
    {"pick": 4, "hit": 4, "amount": 100, "label": "选四中四"},
    {"pick": 4, "hit": 3, "amount": 5, "label": "选四中三"},
    {"pick": 4, "hit": 2, "amount": 3, "label": "选四中二"},
    {"pick": 5, "hit": 5, "amount": 1000, "label": "选五中五"},
    {"pick": 5, "hit": 4, "amount": 21, "label": "选五中四"},
    {"pick": 5, "hit": 3, "amount": 3, "label": "选五中三"},
    {"pick": 6, "hit": 6, "amount": 3000, "label": "选六中六"},
    {"pick": 6, "hit": 5, "amount": 30, "label": "选六中五"},
    {"pick": 6, "hit": 4, "amount": 10, "label": "选六中四"},
    {"pick": 6, "hit": 3, "amount": 3, "label": "选六中三"},
    {"pick": 7, "hit": 7, "amount": 10000, "label": "选七中七"},
    {"pick": 7, "hit": 6, "amount": 288, "label": "选七中六"},
    {"pick": 7, "hit": 5, "amount": 28, "label": "选七中五"},
    {"pick": 7, "hit": 4, "amount": 4, "label": "选七中四"},
    {"pick": 7, "hit": 0, "amount": 2, "label": "选七中零"},
    {"pick": 8, "hit": 8, "amount": 50000, "label": "选八中八"},
    {"pick": 8, "hit": 7, "amount": 800, "label": "选八中七"},
    {"pick": 8, "hit": 6, "amount": 88, "label": "选八中六"},
    {"pick": 8, "hit": 5, "amount": 10, "label": "选八中五"},
    {"pick": 8, "hit": 4, "amount": 3, "label": "选八中四"},
    {"pick": 8, "hit": 0, "amount": 2, "label": "选八中零"},
    {"pick": 9, "hit": 9, "amount": 300000, "label": "选九中九"},
    {"pick": 9, "hit": 8, "amount": 2000, "label": "选九中八"},
    {"pick": 9, "hit": 7, "amount": 200, "label": "选九中七"},
    {"pick": 9, "hit": 6, "amount": 20, "label": "选九中六"},
    {"pick": 9, "hit": 5, "amount": 5, "label": "选九中五"},
    {"pick": 9, "hit": 4, "amount": 3, "label": "选九中四"},
    {"pick": 9, "hit": 0, "amount": 2, "label": "选九中零"},
    {"pick": 10, "hit": 10, "amount": 5000000, "label": "选十中十"},
    {"pick": 10, "hit": 9, "amount": 8000, "label": "选十中九"},
    {"pick": 10, "hit": 8, "amount": 800, "label": "选十中八"},
    {"pick": 10, "hit": 7, "amount": 80, "label": "选十中七"},
    {"pick": 10, "hit": 6, "amount": 5, "label": "选十中六"},
    {"pick": 10, "hit": 5, "amount": 3, "label": "选十中五"},
    {"pick": 10, "hit": 0, "amount": 2, "label": "选十中零"},
]

SEEDS = [
    {
        "code": "ssq", "name": "双色球", "category": "福彩",
        "rule_config": {
            "zones": [
                {"key": "red", "label": "红球", "min": 1, "max": 33, "count": 6, "color": "#e53935"},
                {"key": "blue", "label": "蓝球", "min": 1, "max": 16, "count": 1, "color": "#1e88e5"},
            ],
            "prize_rules": [
                {"level": 1, "red": 6, "blue": 1}, {"level": 2, "red": 6, "blue": 0},
                {"level": 3, "red": 5, "blue": 1}, {"level": 4, "red": 5, "blue": 0},
                {"level": 4, "red": 4, "blue": 1}, {"level": 5, "red": 4, "blue": 0},
                {"level": 5, "red": 3, "blue": 1}, {"level": 6, "red": 2, "blue": 1},
                {"level": 6, "red": 1, "blue": 1}, {"level": 6, "red": 0, "blue": 1},
            ],
        },
        "draw_days": [2, 4, 7],
    },
    {
        "code": "dlt", "name": "超级大乐透", "category": "体彩",
        "rule_config": {
            "zones": [
                {"key": "red", "label": "前区", "min": 1, "max": 35, "count": 5, "color": "#e53935"},
                {"key": "blue", "label": "后区", "min": 1, "max": 12, "count": 2, "color": "#1e88e5"},
            ],
            "prize_rules": [
                {"level": 1, "red": 5, "blue": 2}, {"level": 2, "red": 5, "blue": 1},
                {"level": 3, "red": 5, "blue": 0}, {"level": 4, "red": 4, "blue": 2},
                {"level": 5, "red": 4, "blue": 1}, {"level": 6, "red": 3, "blue": 2},
                {"level": 7, "red": 4, "blue": 0}, {"level": 8, "red": 3, "blue": 1},
                {"level": 8, "red": 2, "blue": 2}, {"level": 9, "red": 3, "blue": 0},
                {"level": 9, "red": 1, "blue": 2}, {"level": 9, "red": 2, "blue": 1},
                {"level": 9, "red": 0, "blue": 2},
            ],
        },
        "draw_days": [1, 3, 6],
    },
    {
        "code": "kl8", "name": "快乐8", "category": "福彩",
        "rule_config": {
            "play_type": "keno",
            "zones": [
                {"key": "main", "label": "号码", "min": 1, "max": 80, "count": 20,
                 "pick_min": 1, "pick_max": 10, "color": "#fb8c00"},
            ],
            "prize_rules": KENO_PRIZES,
        },
        "draw_days": [1, 2, 3, 4, 5, 6, 7],
    },
]


class Command(BaseCommand):
    help = "插入/更新双色球、大乐透、快乐8 彩种配置(zones 格式)"

    def handle(self, *args, **options):
        for s in SEEDS:
            defaults = {k: v for k, v in s.items() if k != "code"}
            obj, created = Lottery.objects.update_or_create(code=s["code"], defaults=defaults)
            logger.info("seed lottery %s %s", s["code"], "created" if created else "updated")
```

- [ ] **Step 4: 跑测试确认通过 + 全量回归**

Run: `python -m pytest lottery/tests/test_seed_lotteries.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（zones 格式 ssq/dlt 经 get_zones 与老格式等价，全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/lottery/management/commands/seed_lotteries.py lottery_backend/lottery/tests/test_seed_lotteries.py
git commit -m "feat: seed 重写为 zones + 新增快乐8(选N中M奖表)"
```

---

### Task 7: kl8 爬虫 + 注册

**Files:**
- Create: `lottery_backend/crawler/spiders/kl8.py`、`lottery_backend/crawler/tests/test_kl8.py`
- Modify: `lottery_backend/crawler/registry.py`

**Interfaces:**
- Consumes: `BaseSpider.run(count)`（已就绪）
- Produces: `KL8Spider`（parse 输出 `{"main":[20个]}`）；SPIDERS 加 "kl8"。

- [ ] **Step 1: 写失败测试**

`lottery_backend/crawler/tests/test_kl8.py`:
```python
from crawler.spiders.kl8 import KL8Spider


def test_kl8_parse():
    raw = {"result": [
        {"code": "2026100", "date": "2026-06-23(二)",
         "red": "01,05,09,12,18,22,25,30,33,38,41,44,50,55,60,66,70,73,77,80"},
    ]}
    items = KL8Spider().parse(raw)
    assert len(items) == 1
    it = items[0]
    assert it["issue"] == "2026100"
    assert it["numbers"]["main"][:3] == [1, 5, 9]
    assert len(it["numbers"]["main"]) == 20


def test_kl8_parse_skips_bad_record():
    raw = {"result": [{"code": "x", "date": "2026-06-23", "red": "not,num"}]}
    assert KL8Spider().parse(raw) == []
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest crawler/tests/test_kl8.py -v`
Expected: FAIL（无 kl8 模块）

- [ ] **Step 3: 写 kl8 spider**

`lottery_backend/crawler/spiders/kl8.py`（仿 ssq.py，福彩网 name=kl8，无蓝区）:
```python
import logging
from datetime import datetime
import requests
from crawler.spiders.base import BaseSpider

logger = logging.getLogger(__name__)

API = "http://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"


class KL8Spider(BaseSpider):
    lottery_code = "kl8"

    def fetch(self, issue_count=1):
        resp = requests.get(
            API, params={"name": "kl8", "issueCount": issue_count},
            headers={"User-Agent": "Mozilla/5.0", "Referer": "http://www.cwl.gov.cn/"},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()

    def parse(self, raw):
        items = []
        for r in raw.get("result", []):
            try:
                mains = [int(x) for x in r["red"].split(",")]
                items.append({
                    "issue": r["code"],
                    "draw_date": datetime.strptime(r["date"][:10], "%Y-%m-%d").date(),
                    "numbers": {"main": mains},
                    "sales_amount": str(r.get("sales", "")),
                    "pool_amount": str(r.get("poolmoney", "")),
                    "prize_grades": [
                        {"level": g["type"], "count": g["typenum"], "amount": g["typemoney"]}
                        for g in r.get("prizegrades", [])
                    ],
                })
            except Exception:
                logger.error("parse kl8 记录解析失败, 跳过: %r", r.get("code", r), exc_info=True)
                continue
        return items
```

- [ ] **Step 4: 注册 kl8**

`lottery_backend/crawler/registry.py` 整体替换为：
```python
from crawler.spiders.ssq import SsqSpider
from crawler.spiders.dlt import DltSpider
from crawler.spiders.kl8 import KL8Spider

SPIDERS = {"ssq": SsqSpider, "dlt": DltSpider, "kl8": KL8Spider}
```

- [ ] **Step 5: 跑测试确认通过 + 全量回归**

Run: `python -m pytest crawler/tests/test_kl8.py -v`
Expected: PASS（2 passed）
Run: `python -m pytest -q`
Expected: PASS（全量全绿）

- [ ] **Step 6: 提交**

```bash
git add lottery_backend/crawler/spiders/kl8.py lottery_backend/crawler/registry.py lottery_backend/crawler/tests/test_kl8.py
git commit -m "feat: 快乐8 爬虫 kl8 + 注册"
```

---

## 计划自检

**1. Spec 覆盖（后端部分）：**
- zones 泛化（get_zones）→ Task 1；validators/generator/stats 遍历 zones → Task 2/3/4 ✓
- draw/pick 双 mode + 可变 picks → Task 2/3 ✓
- judge_keno 选N中M + play_type 分派 → Task 5 ✓
- seed zones + kl8（选N中M奖表）→ Task 6 ✓
- kl8 爬虫 → Task 7 ✓
- 前端泛化 + 玩法选号 → **A1-前端计划（后端合并后另写）**
- 真抓 kl8 + re-seed + 端到端 → 控制端合并前执行

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码（含 kl8 官方奖表）。

**3. 类型/签名一致性：**
- `get_zones(rule_config)->list`(Task1) 被 validators/generator/stats(Task2-4) 一致调用，读 zone["key"]/["min"]/["max"]/["count"]/["pick_*"]。
- `validate_numbers(rc,numbers,mode="pick")`(Task2)；persist 传 mode="draw"；create/generate 用默认 pick。
- `random_numbers(rc,picks=None)`(Task3)；既有 create/generate 调用不传 picks 不变。
- `judge_keno`(Task5) 读 zones[0]["key"] 与 seed 的 kl8 main 一致；prize_rules {pick,hit,label,amount}(Task6) 与 judge_keno 匹配键一致。
- kl8 spider 输出 {"main":[...]}(Task7) 与 seed kl8 zone key "main"、judge_keno main_key 一致。

**4. 注意点（给执行者）：**
- 核心无回归策略：get_zones 兼容老 red/blue，**现有 ssq/dlt 测试不改即应保持绿**；每个改造任务都跑全量 `pytest -q` 确认。
- validate_numbers 错误信息用 zone key（老格式 key=red/blue，与原"red 号码..."文案一致），既有断言不破。
- judge_prize 仅新增 desc 字段，不改原有 red_hit/blue_hit/level/label。
- kl8 spider parse 仿 ssq；真实抓取由控制端 `load_history --code kl8 --count 100` 执行（属运行步骤，非单测）。
- 全部不打真实网络（spider 测试只测 parse）。
