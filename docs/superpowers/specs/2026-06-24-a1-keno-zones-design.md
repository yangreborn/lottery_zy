# A1 · 快乐8 + 区泛化地基 · 设计文档

- 日期：2026-06-24
- 定位：新增"快乐8"彩种（中奖信息 + 玩法选号），并把写死的 red/blue 双区模型泛化为通用"区列表"，为后续 3D/排列三（A2）铺底。对应 note.txt 第 3、4 项中的快乐8部分。
- 前置：A-model-survey.md（红蓝模型 15 个写死点调研）。ssq/dlt 现有功能、爬虫、统计、判奖均就绪。

---

## 0. 范围

**本期做**：① rule_config 泛化为 `zones` 列表；② 后端 validators/generator/stats 改为按 zones 遍历（ssq/dlt 行为不变，靠现有测试证明无回归）；③ 新增 `judge_keno`（选 N 中 M），判奖按 play_type 分派；④ kl8 爬虫 + seed，真抓最近开奖；⑤ 前端 picker/stats/展示页按 zones 动态渲染；⑥ 快乐8"玩法"选号（先选选几，再手动/机选）。
**不做**：3D/排列三（A2 另起里程碑）；定胆 UI（B 已隐藏，仅后端 dan_random_numbers 随泛化保持可用）；不改 DrawResult/UserNumber 的 numbers 存储结构（仍按区 key 字典，无数据迁移）。

## 1. 通用 rule_config（zones 列表）

顶层由写死 red/blue 改为 `zones` 列表 + `prize_rules` + 可选 `play_type`：

```jsonc
// 每个 zone：
{ "key": "red", "label": "红球", "min": 1, "max": 33, "count": 6,
  "pick_min": 1, "pick_max": 10,   // 可选：用户选号个数范围(可变玩法,如快乐8);无则用户必须选 count 个
  "color": "#e53935" }             // 可选：球颜色;无则前端按 key 回退(red/blue/灰)
```

- ssq：`zones=[{red,min1,max33,count6},{blue,min1,max16,count1}]`，无 play_type（=红蓝判奖）。
- dlt：`zones=[{red,min1,max35,count5},{blue,min1,max12,count2}]`。
- 快乐8：`zones=[{key:"main",label:"号码",min:1,max:80,count:20,pick_min:1,pick_max:10,color:"#fb8c00"}]`，`play_type:"keno"`。

**count vs pick**：`count` 是**开奖**号码个数（快乐8=20）；`pick_min/pick_max` 是**用户选号**个数范围（快乐8 1-10）。ssq/dlt 无 pick_*，开奖与用户选号都用 count。

`numbers` 存储不变：按区 key 的字典。快乐8 开奖 `{"main":[20个]}`、用户选号 `{"main":[1-10个]}`。

## 2. 后端 · 校验（validators.py）

`validate_numbers(rule_config, numbers, mode="pick")`：
- 顶层非 dict 守卫保留（返回 ["号码格式应为字典"]）。
- 遍历 `rule_config["zones"]`（缺省空列表）。对每区按 key 取 `numbers[key]`：
  - 非 list → 报错。
  - **个数**：`mode="draw"` → 必须 == `count`；`mode="pick"` → 有 pick_min/pick_max 则 `pick_min ≤ len ≤ pick_max`，否则 == `count`。
  - 不重复校验保留（A1 所有彩种都不重复；A2 再按 allow_repeat 放开）。
  - 范围 `min ≤ n ≤ max` 校验保留。
- 调用方更新：`persist_draw` 传 `mode="draw"`；`NumberCreateView`/`NumberGenerateView` 用默认 `mode="pick"`。

## 3. 后端 · 机选生成（generator.py）

`random_numbers(rule_config, picks=None)`：
- `picks`：可选 `{zone_key: n}`，指定可变区选几（快乐8 的"玩法"）。
- 遍历 zones，每区个数 `n = _pick_count(zone, picks)`：可变区（有 pick_*）→ 取 `picks[key]` 并夹到 `[pick_min, pick_max]`，缺省取 `pick_max`；固定区 → `zone["count"]`。
- `random.sample(range(min, max+1), n)` 后 `sorted`（A1 仍不重复升序；A2 再按 ordered/allow_repeat 分支）。
- `dan_random_numbers` 同步改为遍历 zones（保持 ssq/dlt 可用；UI 不暴露）。

## 4. 后端 · 统计（stats.py）

`compute_number_stats` 遍历 `rule_config["zones"]`，每区按 `range(min, max+1)` 统计出现次数/遗漏（与现逻辑一致，仅区来源改为 zones）。快乐8 单区 1-80 直接复用此模型。返回 `{zone_key: [{number,count,miss}], periods}`（键由 zone key 决定）。

## 5. 后端 · 判奖（judge.py，分派不合并）

- 保留 `judge_prize(rule_config, draw_numbers, user_numbers)`（红蓝：各区交集 hit，按 prize_rules 的 {red,blue} 匹配）。返回加 `desc`（如 "命中 红6 蓝1"）。
- **新增 `judge_keno(rule_config, draw_numbers, user_numbers)`**：main 区 `hit = |user ∩ draw|`、`pick = len(user)`，按 prize_rules 的 `{pick, hit}` 匹配奖级；返回 `{hit, pick, level, label, desc}`（desc 如 "选5中5"）。
- `NumberCheckView` 分派：`rule_config.get("play_type")=="keno"` → judge_keno，否则 judge_prize。两者都返回 `label` + `desc`，前端统一展示 `{desc}，{label}`。
- 快乐8 prize_rules：选一…选十 的 (pick,hit)→label+amount 官方奖金表（具体表在实现计划/seed 内）。

## 6. 后端 · kl8 爬虫 + seed

- 新增 `crawler/spiders/kl8.py`：中国福彩网 `findDrawNotice` `name=kl8`，parse 输出 `{"main":[20个]}`（kl8 开奖号字段按官方返回解析）。注册进 SPIDERS。
- `seed_lotteries.py` 加 kl8 记录（zones/play_type/prize_rules，draw_days=每日）。
- 控制端执行时真跑 `load_history --code kl8 --count 100`（快乐8 每日开，抓约 100 期），并 ssq/dlt re-seed 为 zones 结构。

## 7. 前端 · 区泛化（ssq/dlt 渲染不变）

- `utils/picker.js` `selectionComplete(numbers, rule)`：遍历 `rule.zones`（按 key + 个数规则，pick_* 用范围）。`toggleBall` 不变（A1 仍升序；A2 再处理有序）。
- `pages/mine/picker.vue`：`sel` 由写死 `{red,blue}` 改为按 `rule.zones` 动态建区；模板 `v-for zone in rule.zones` 出区块（标签 zone.label、颜色 zone.color）；保存按 zones 组装 numbers。
- `pages/draw/stats.vue`：遍历返回的 zone 列表动态出标题 + Heatmap（不再写死红蓝两块）。
- `pages/draw/latest.vue`/`history.vue`/`detail.vue`：按该彩种 `rule.zones` 顺序枚举 `draw.numbers[zone.key]` 渲染。
- `utils/format.js` `ballColor`：优先用 zone.color；无则回退现有 red/blue/灰。

## 8. 前端 · 快乐8玩法选号

- picker 检测当前彩种有可变区（pick_min/pick_max）时，显示"**玩法**"选择行（选1…选pick_max），选中即设该区目标个数 `pickCount`。
- 手动：选满 pickCount 个即可保存；机选：调 generate 传 `picks={main: pickCount}` 生成 pickCount 个。
- 固定区彩种（ssq/dlt）不显示玩法行，行为不变。

## 9. 错误处理

- validate_numbers 顶层非 dict、各区个数/范围/重复 → code=1（沿用）。
- 爬虫单条/整彩种失败容错沿用 load_history。
- 前端接口失败 toast + 空态沿用。

## 10. 测试

- **后端 pytest**：
  - 泛化无回归：validators/generator/stats 对 ssq/dlt 行为与改造前一致（现有用例保持绿 + 必要补充）。
  - 校验：kl8 draw(==20)/pick(1-10 范围) 两 mode；个数越界 code=1。
  - 生成：random_numbers(picks={main:5}) 生成 5 个且范围内；ssq 不传 picks 仍 6+1。
  - 判奖：judge_keno 选5中5/选5中3/选10中0 各奖级正确；judge_prize 红蓝不变。
  - kl8 spider parse（mock 官方响应）输出 {main:[20]}。
- **前端 vitest**：selectionComplete 按 zones（固定区 ssq、可变区 kl8 范围）；既有 picker/statsort/records 全绿。
- **控制端端到端**：re-seed + 真抓 kl8；起后端验证 kl8 开奖展示、统计、选号(选玩法→机选/手动→保存→比对中奖)。

## 11. 怎么看效果

彩种切到"快乐8"：开奖页显示 20 个号；统计页单区 1-80 出现/遗漏；选号页先选"选5"→选 5 个号（或机选 5 个）→保存→比对显示"选5中X，X等奖/未中奖"。ssq/dlt 一切照旧。

## 12. 里程碑定位

note.txt 第 3、4 项的快乐8部分 + 区泛化地基。后续 A2：3D/排列三（位置式、有序可重复、直选/组选判奖、按位统计），复用本期 zones 地基再加 ordered/allow_repeat 维度。
