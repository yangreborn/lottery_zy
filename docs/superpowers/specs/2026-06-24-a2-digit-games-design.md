# A2 · 3D / 排列三（位置式数字彩）· 设计文档

- 日期：2026-06-24
- 定位：新增福彩3D、体彩排列三（中奖信息 + 玩法选号）。3 位有序可重复数字，复用 A1 的 zones 地基，在 zone 上加 ordered/allow_repeat 维度。对应 note.txt 第 3、4 项中的 3D/排列三部分。
- 前置：A1（zones 地基 + get_zones + validate/generate/stats 按 zones + judge 分派 + 前端 zones 渲染）已就绪。

---

## 0. 范围

**本期做**：① zone 加 ordered/allow_repeat；validators 跳过去重、generator 用 choices+不排序；② 新增 judge_digit（直选/组选），判奖按 play_type="digit" 分派；③ 3d/pl3 爬虫 + seed（直选/组选奖表），真抓最近开奖；④ 前端 picker 位置式选号 + 数字球单字符。
**不做**：统计不改（复用数字频次）；不做和值/跨度等衍生玩法；不做组三/组六分别投注（判奖只判"这注若投会中直选还是组选"）。

## 1. 数据来源（已实测可达）

- 福彩3D：中国福彩网 `findDrawNotice` `name=3d`，`red` 形如 `"6,9,0"`（逗号分隔 3 位）。
- 排列三：中国体彩网 `getHistoryPageListV1` `gameNo=35`，`lotteryDrawResult` 形如 `"7 1 5"`（空格分隔 3 位）。
- 解析为 `numbers={"digits":[d1,d2,d3]}`（有序，可重复）。

## 2. zone 加两个维度

3D/排列三 zone：`{key:"digits", label:"数字", min:0, max:9, count:3, ordered:true, allow_repeat:true, color:"#43a047"}`。

- **validators**（`validate_numbers`）：当 `zone.allow_repeat` 为真时**跳过不重复校验**；个数仍 `== count`(3)（无 pick_*）；范围仍 `0 ≤ n ≤ 9`。其他彩种无此 flag，去重照旧。
- **generator**（`random_numbers`）：`zone.allow_repeat` → `random.choices`（可重复）否则 `random.sample`；`zone.ordered` → **不排序**否则 sorted。ssq/dlt/kl8 无 flag，行为不变。

## 3. 判奖（新 judge_digit，play_type="digit"，与红蓝/快乐8 分开）

`judge_digit(rule_config, draw_numbers, user_numbers)`（main 区 key 取 zones[0]["key"]="digits"）：
- 用户 U、开奖 D 各 3 位。
- `U == D`（含顺序）→ **直选**。
- `sorted(U) == sorted(D)`（集合相同）→ **组选**：开奖有重复数字(`len(set(D))<3`)=组三，全不同=组六。
- 否则未中奖。
- 按 prize_rules 的 `type`（direct/group3/group6）取 label/amount。返回 `{hit_type, label, amount, desc}`（desc 如 "直选命中" / "组选三命中" / "未中奖"）。
- NumberCheckView 分派：`play_type=="digit"` → judge_digit；`=="keno"` → judge_keno；否则 judge_prize。

prize_rules（3D/排列三 固定奖，官方）：`[{type:"direct", amount:1040, label:"直选"}, {type:"group3", amount:346, label:"组选三"}, {type:"group6", amount:173, label:"组选六"}]`。

## 4. 统计

不改。`compute_number_stats` 对 digits 区按 `range(0,10)` 统计每个数字在近 N 期出现的期数（频次），统计页"数字"单区 0-9 + 最多/最少筛选直接复用。

## 5. 爬虫 + seed

- `crawler/spiders/td.py`（3D，cwl name=3d，parse `red.split(",")`→digits）+ 注册。
- `crawler/spiders/pl3.py`（排列三，sporttery gameNo=35，parse `lotteryDrawResult.split()`→digits）+ 注册。
- seed 加 `3d`、`pl3`（play_type=digit，digits zone，直选/组选 prize_rules，draw_days 每日）。
- 控制端执行时真跑 `load_history --code 3d --count 100`、`--code pl3 --count 100`。

## 6. 前端（位置式选号 + 数字球）

- **picker**：检测含 digit zone（`ordered && allow_repeat`）时，渲染 **count 个位置选择器**，每位一行 0-9（可重复选，互不影响）；手动 sel[key] 为定长 3 数组（按位赋值）。机选走 generate（generator 已 choices）。非 digit 彩种照旧。
- **数字球**：Ball 加 `pad`（默认 2），digit 区传 `:pad="1"` 显示单字符（3D 690 显示 6 9 0 而非 06 09 00）。展示页/picker 对 digit zone 传 pad=1。
- 展示/统计页复用 A1 的 zones entries 渲染（digits 区 0-9 单字符球）。

## 7. 错误处理

- validate_numbers 去重跳过仅 allow_repeat 区；个数/范围照常 code=1。
- 爬虫单条/整彩种失败容错沿用 load_history。
- 前端选号位置未选满时禁用保存。

## 8. 测试

- 后端 pytest：validators digit（允许重复 [5,5,3] 合法、超范围 code1、个数!=3 code1）；generator digit（choices 可重复、不排序、长度 3）；judge_digit（直选/组选三/组选六/未中奖）；3d/pl3 spider parse（mock）；seed digit 彩种。ssq/dlt/kl8 全程无回归。
- 前端 vitest：位置式选号纯函数（按位 set、是否选满）；数字球 pad。
- 控制端端到端：真抓 3d/pl3，起后端验证开奖展示(3 位)、统计(数字频次)、选号(位置式→机选/手动→保存→直选/组选判奖)。

## 9. 拆分

- **A2-后端**：zone flag（validators/generator）+ judge_digit + 3d/pl3 爬虫 + seed。
- **A2-前端**：picker 位置式选号 + 数字球 pad。
各自独立 spec→plan→实现（本设计文档覆盖两者）。

## 10. 里程碑定位

note.txt 第 3、4 项的 3D/排列三部分，A 系列收官（继 A1 快乐8）。后续：F 中奖信息(1) → G 体验版(10) → dlt 翻页抓满一年(可选)。
