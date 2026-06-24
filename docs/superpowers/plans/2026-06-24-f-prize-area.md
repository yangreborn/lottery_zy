# F · 一等奖分省 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 双色球一等奖可点开查看分省中奖（哪些省中了几注）。

**Architecture:** 后端 DrawResult 加 prize_area 文本字段，ssq 爬虫抓福彩 content 存入，序列化暴露；前端 PrizeGrades 一等奖行可展开显示分省原文（去前缀）。

**Tech Stack:** Django 5.2 + DRF（后端）；uni-app(Vue3+Vite, JS) + vitest（前端）。

## Global Constraints

- 数据约束：分省数据**仅双色球(ssq)有**（福彩 content）；3d/kl8 content 空、体彩无此字段——其余彩种 prize_area 空、前端无展开。
- DrawResult 加 `prize_area = models.TextField("一等奖分省", blank=True, default="")`；ssq spider item 加 `"prize_area": r.get("content", "")`；persist_draw defaults 加 `"prize_area": item.get("prize_area", "")`；序列化 fields 加 `"prize_area"`。
- 前端 `stripAreaPrefix(text)`：去首个 中/英文冒号(：或:)及之前；空/无冒号原样返回。
- PrizeGrades：flat 模式第 0 行（最高奖）若 area 非空可点开，展开显示 stripAreaPrefix(area)；其他行/grouped/空 area 无展开。
- 后端日志 logging 禁 print；前端无 console，不引 Pinia/Vuex。
- 后端在 `lottery_backend/`(先激活 .venv)，测试 DB Docker 5433；前端在 `lottery_frontend/`。

---

## File Structure

- `lottery_backend/lottery/models.py`(改)：DrawResult.prize_area。
- `lottery_backend/lottery/migrations/`(新)：makemigrations。
- `lottery_backend/lottery/serializers.py`(改)：fields 加 prize_area。
- `lottery_backend/crawler/persist.py`(改)：存 prize_area。
- `lottery_backend/crawler/spiders/ssq.py`(改)：抓 content。
- `lottery_frontend/src/utils/prize.js`(改)：stripAreaPrefix。
- `lottery_frontend/src/components/PrizeGrades.vue`(改)：area 展开。
- `lottery_frontend/src/pages/draw/latest.vue` `detail.vue`(改)：传 area。

---

### Task 1: DrawResult.prize_area 字段 + persist + 序列化

**Files:**
- Modify: `lottery_backend/lottery/models.py`、`lottery_backend/lottery/serializers.py`、`lottery_backend/crawler/persist.py`
- Create: `lottery_backend/lottery/migrations/`(makemigrations)、`lottery_backend/crawler/tests/test_prize_area.py`

**Interfaces:**
- Produces: `DrawResult.prize_area`(TextField)；persist_draw 存它；序列化暴露 prize_area。

- [ ] **Step 1: 写失败测试**

`lottery_backend/crawler/tests/test_prize_area.py`:
```python
import datetime
import pytest
from lottery.models import Lottery, DrawResult
from lottery.serializers import DrawResultSerializer
from crawler.persist import persist_draw


@pytest.fixture
def ssq(db):
    return Lottery.objects.create(
        code="ssq", name="双色球", category="福彩",
        rule_config={"zones": [
            {"key": "red", "label": "红球", "min": 1, "max": 33, "count": 6},
            {"key": "blue", "label": "蓝球", "min": 1, "max": 16, "count": 1}]},
        draw_days=[2, 4, 7])


def test_persist_stores_prize_area(ssq):
    item = {
        "issue": "2026071", "draw_date": datetime.date(2026, 6, 23),
        "numbers": {"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
        "prize_grades": [], "prize_area": "一等奖中奖情况：北京1注、广东3注，共4注",
    }
    obj, errors = persist_draw(ssq, item)
    assert errors == []
    assert obj.prize_area == "一等奖中奖情况：北京1注、广东3注，共4注"


def test_serializer_exposes_prize_area(ssq):
    obj = DrawResult.objects.create(
        lottery=ssq, issue="2026072", draw_date=datetime.date(2026, 6, 25),
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]},
        prize_area="北京1注")
    data = DrawResultSerializer(obj).data
    assert data["prize_area"] == "北京1注"


def test_prize_area_defaults_empty(ssq):
    obj = DrawResult.objects.create(
        lottery=ssq, issue="2026073", draw_date=datetime.date(2026, 6, 27),
        numbers={"red": [1, 2, 3, 4, 5, 6], "blue": [7]})
    assert obj.prize_area == ""
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest crawler/tests/test_prize_area.py -v`
Expected: FAIL（DrawResult 无 prize_area 字段 / 序列化无该字段）

- [ ] **Step 3: 加 prize_area 字段**

`lottery_backend/lottery/models.py` 的 DrawResult 中，在 `prize_grades` 行之后加：
```python
    prize_area = models.TextField("一等奖分省", blank=True, default="")
```

- [ ] **Step 4: 生成迁移**

Run: `python manage.py makemigrations lottery`
Expected: 生成 `lottery/migrations/000X_drawresult_prize_area.py`

- [ ] **Step 5: persist_draw 存 prize_area**

`lottery_backend/crawler/persist.py` 的 update_or_create defaults 里，在 `"prize_grades": item.get("prize_grades", []),` 之后加：
```python
            "prize_area": item.get("prize_area", ""),
```

- [ ] **Step 6: 序列化器加 prize_area**

`lottery_backend/lottery/serializers.py` 中，把 DrawResultSerializer 的 Meta.fields（含 `"prize_grades"` 的那个 tuple）末尾加 `"prize_area"`：
```python
        fields = ("issue", "draw_date", "numbers", "sales_amount",
                  "pool_amount", "prize_grades", "prize_area")
```
（若 DrawDetailSerializer 另有自己的 Meta.fields tuple，也同样补 `"prize_area"`；DrawDetailSerializer 若仅继承父 Meta 则无需重复。）

- [ ] **Step 7: 跑测试确认通过 + 全量回归**

Run: `python -m pytest crawler/tests/test_prize_area.py -v`
Expected: PASS（3 passed）
Run: `python -m pytest -q`
Expected: PASS（全量全绿）

- [ ] **Step 8: 提交**

```bash
git add lottery_backend/lottery/models.py lottery_backend/lottery/migrations/ lottery_backend/lottery/serializers.py lottery_backend/crawler/persist.py lottery_backend/crawler/tests/test_prize_area.py
git commit -m "feat: DrawResult.prize_area 字段 + persist + 序列化"
```

---

### Task 2: ssq 爬虫抓 content → prize_area

**Files:**
- Modify: `lottery_backend/crawler/spiders/ssq.py`
- Test: `lottery_backend/crawler/tests/test_ssq.py`（追加；无则新建）

**Interfaces:**
- Consumes: 福彩 findDrawNotice 的 `content` 字段
- Produces: ssq parse item 含 `prize_area`。

- [ ] **Step 1: 追加失败测试**

`lottery_backend/crawler/tests/test_ssq.py`（无则新建，顶部 `from crawler.spiders.ssq import SsqSpider`）追加：
```python
def test_ssq_parse_captures_prize_area():
    raw = {"result": [{
        "code": "2026071", "date": "2026-06-23(二)",
        "red": "01,02,03,04,05,06", "blue": "07",
        "content": "一等奖中奖情况：北京1注、广东3注，共4注",
        "prizegrades": [],
    }]}
    items = SsqSpider().parse(raw)
    assert items[0]["prize_area"] == "一等奖中奖情况：北京1注、广东3注，共4注"


def test_ssq_parse_prize_area_missing_ok():
    raw = {"result": [{
        "code": "2026072", "date": "2026-06-25(四)",
        "red": "01,02,03,04,05,06", "blue": "07", "prizegrades": [],
    }]}
    items = SsqSpider().parse(raw)
    assert items[0]["prize_area"] == ""
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest crawler/tests/test_ssq.py -v`
Expected: FAIL（item 无 prize_area 键）

- [ ] **Step 3: ssq parse 加 prize_area**

`lottery_backend/crawler/spiders/ssq.py` 的 parse 中，`items.append({...})` 字典里在 `"prize_grades": [...]` 之后加一行：
```python
                    "prize_area": r.get("content", ""),
```

- [ ] **Step 4: 跑测试确认通过 + 全量回归**

Run: `python -m pytest crawler/tests/test_ssq.py -v`
Expected: PASS
Run: `python -m pytest -q`
Expected: PASS（3d/kl8 等其他 spider 不动，全绿）

- [ ] **Step 5: 提交**

```bash
git add lottery_backend/crawler/spiders/ssq.py lottery_backend/crawler/tests/test_ssq.py
git commit -m "feat: ssq 爬虫抓 content 存入 prize_area"
```

---

### Task 3: 前端 stripAreaPrefix + PrizeGrades 一等奖展开

**Files:**
- Modify: `lottery_frontend/src/utils/prize.js`、`lottery_frontend/src/components/PrizeGrades.vue`、`lottery_frontend/src/pages/draw/latest.vue`、`lottery_frontend/src/pages/draw/detail.vue`
- Test: `lottery_frontend/tests/prize.test.js`（追加）

**Interfaces:**
- Consumes: `draw.prize_area`、`normalizePrizes`、`formatAmount`
- Produces: `stripAreaPrefix(text)`；PrizeGrades `area` prop 一等奖展开。

- [ ] **Step 1: 追加失败测试**

`lottery_frontend/tests/prize.test.js` 末尾追加（顶部 import 补 stripAreaPrefix）：
```js
import { stripAreaPrefix } from '../src/utils/prize.js'

describe('stripAreaPrefix', () => {
  it('去掉中文冒号前缀', () => {
    expect(stripAreaPrefix('一等奖中奖情况：北京1注、广东3注，共4注')).toBe('北京1注、广东3注，共4注')
  })
  it('无冒号原样', () => {
    expect(stripAreaPrefix('北京1注')).toBe('北京1注')
  })
  it('空安全', () => {
    expect(stripAreaPrefix('')).toBe('')
    expect(stripAreaPrefix(null)).toBe('')
  })
})
```

- [ ] **Step 2: 跑测试确认失败**

Run: `npm test`
Expected: FAIL（无 stripAreaPrefix）

- [ ] **Step 3: 加 stripAreaPrefix**

`lottery_frontend/src/utils/prize.js` 末尾追加：
```js
export function stripAreaPrefix(text) {
  if (!text) return ''
  return String(text).replace(/^[^：:]*[：:]/, '')
}
```

- [ ] **Step 4: PrizeGrades 加 area 展开**

`lottery_frontend/src/components/PrizeGrades.vue` 整体替换为：
```vue
<template>
  <view class="grades">
    <view class="grade head-row">
      <text class="c1">奖级</text><text class="c2">注数</text><text class="c3">单注奖金</text>
    </view>
    <template v-if="!data.grouped">
      <template v-for="(g, i) in data.flat" :key="i">
        <view class="grade" :class="{ clickable: i === 0 && area }" @click="i === 0 && area ? (open1 = !open1) : null">
          <text class="c1">{{ g.label }}<text v-if="i === 0 && area" class="more">{{ open1 ? ' ▲' : ' ▼分省' }}</text></text>
          <text class="c2">{{ g.count }}</text>
          <text class="c3">{{ formatAmount(g.amount) }}</text>
        </view>
        <view v-if="i === 0 && area && open1" class="area">{{ areaText }}</view>
      </template>
      <view v-if="!data.flat.length" class="none">暂无奖级数据</view>
    </template>
    <template v-else>
      <view v-for="grp in data.groups" :key="grp.pick" class="kgroup">
        <view class="ghead" @click="toggle(grp.pick)">
          <text>{{ grp.label }}（{{ grp.rows.length }}档）</text>
          <text>{{ open.includes(grp.pick) ? '▲' : '▼' }}</text>
        </view>
        <template v-if="open.includes(grp.pick)">
          <view v-for="(g, i) in grp.rows" :key="i" class="grade">
            <text class="c1">{{ g.label }}</text>
            <text class="c2">{{ g.count }}</text>
            <text class="c3">{{ formatAmount(g.amount) }}</text>
          </view>
        </template>
      </view>
    </template>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { normalizePrizes, stripAreaPrefix } from '../utils/prize.js'
import { formatAmount } from '../utils/format.js'

const props = defineProps({
  grades: { type: Array, default: () => [] },
  area: { type: String, default: '' },
})
const data = computed(() => normalizePrizes(props.grades))
const areaText = computed(() => stripAreaPrefix(props.area))
const open1 = ref(false)
const open = ref([])
function toggle(pick) {
  open.value = open.value.includes(pick)
    ? open.value.filter((p) => p !== pick)
    : [...open.value, pick]
}
</script>

<style scoped>
.grades { border-top: 1px solid #f0f0f0; padding-top: 16rpx; }
.grade { display: flex; padding: 10rpx 0; font-size: 30rpx; color: #555; }
.c1 { flex: 2; }
.c2 { flex: 1; text-align: center; }
.c3 { flex: 2; text-align: right; }
.head-row { color: #999; font-weight: 600; }
.clickable .more { color: #e53935; font-size: 26rpx; }
.area { padding: 10rpx 0 16rpx; font-size: 28rpx; color: #777; line-height: 1.6; }
.kgroup { border-bottom: 1px solid #f5f5f5; }
.ghead { display: flex; justify-content: space-between; padding: 16rpx 0; font-size: 30rpx; color: #e53935; font-weight: 600; }
.none { text-align: center; color: #999; padding: 20rpx 0; font-size: 28rpx; }
</style>
```

- [ ] **Step 5: latest/detail 传 area**

`lottery_frontend/src/pages/draw/latest.vue` 与 `detail.vue` 中的：
```html
      <PrizeGrades :grades="draw.prize_grades" />
```
改为：
```html
      <PrizeGrades :grades="draw.prize_grades" :area="draw.prize_area" />
```

- [ ] **Step 6: build + 目测 + 测试**

Run: `npm run build:h5`（Build complete）；`npm test`（全绿）
目测（后端 8123 + 重抓 ssq 后）：双色球当期/详情一等奖行尾有"▼分省"，点开显示"北京1注、广东3注…共4注"；其他奖级/其他彩种无该入口。

- [ ] **Step 7: 提交**

```bash
git add lottery_frontend/src/utils/prize.js lottery_frontend/src/components/PrizeGrades.vue lottery_frontend/src/pages/draw/latest.vue lottery_frontend/src/pages/draw/detail.vue lottery_frontend/tests/prize.test.js
git commit -m "feat: 一等奖可点开查看分省中奖(stripAreaPrefix + PrizeGrades area)"
```

---

## 计划自检

**1. Spec 覆盖：**
- DrawResult.prize_area + persist + 序列化 → Task 1 ✓
- ssq 抓 content → Task 2 ✓
- stripAreaPrefix + PrizeGrades 一等奖展开 + latest/detail 传 area → Task 3 ✓
- 重抓 ssq → 控制端运行步骤

**2. Placeholder 扫描：** 无 TBD/TODO；每步含完整代码。

**3. 类型/签名一致性：**
- `prize_area`(Task1 model/persist/serializer) ← ssq spider item prize_area(Task2) ← 前端 draw.prize_area(Task3)，键名贯通。
- `stripAreaPrefix`(Task3 prize.js) 被 PrizeGrades areaText(Task3) 用；`area` prop 由 latest/detail 传 draw.prize_area。

**4. 注意点（给执行者）：**
- 仅 ssq 有分省数据；3d/kl8 content 空、体彩无 → prize_area 空 → 前端无展开，正常。
- 序列化器：DrawResultSerializer 加 prize_area；若 DrawDetailSerializer 自带 Meta.fields 也补，否则继承即可（实现时 grep 确认）。
- PrizeGrades 仅 flat 第 0 行 + area 非空才展开；grouped(快乐8)不涉及。
- 重抓 ssq（`load_history --code ssq --count 160`）由控制端执行，让历史/当期带分省；旧数据无 prize_area→无展开。
