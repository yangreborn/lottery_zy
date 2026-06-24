# F · 一等奖分省中奖信息 · 设计文档

- 日期：2026-06-24
- 定位：双色球一等奖可点开，查看哪些省份中了几注。对应 note.txt 第 1 项"补全当期和往期的中奖信息"。
- 数据实测结论：**只有双色球(ssq)有分省数据**（福彩 `content` 字段："一等奖中奖情况：北京1注、广东3注…共8注"）；3D/快乐8 content 为空；大乐透/排列三（体彩 API）完全无分省字段。

---

## 0. 范围

**本期做**：DrawResult 存一等奖分省文本（ssq 的 content）；前端 PrizeGrades 一等奖行可点开显示分省（原文，去前缀）。
**不做**：不解析成结构化省份卡片（存原文，稳当）；体彩/3D/快乐8 无此数据→无展开入口；不做低奖级分省。

## 1. 后端

- `DrawResult` 加 `prize_area = models.TextField("一等奖分省", blank=True, default="")` + 迁移（rule_config 风格的纯加字段，无数据迁移）。
- `crawler/spiders/ssq.py` parse 的 item 加 `"prize_area": r.get("content", "")`（3d/kl8 spider 不动，其 content 空；体彩无此字段）。
- `crawler/persist.py` 的 `persist_draw` 在 update_or_create defaults 里加 `"prize_area": item.get("prize_area", "")`。
- `DrawResult` 序列化器 fields 加 `"prize_area"`。
- 控制端重抓 ssq（`load_history --code ssq --count 160`）让历史数据带上分省。

## 2. 前端

- `utils/prize.js` 加 `stripAreaPrefix(text)`：去掉首个"：/:"及之前（"一等奖中奖情况：北京1注…" → "北京1注…"）；空/无前缀原样返回。
- `components/PrizeGrades.vue`：
  - 加 `area` prop（默认 ''）。
  - flat 模式下**第 0 行（一等奖/最高奖）**：若 `area` 非空 → 该行可点击，行尾显示"▼分省"；点开在该行下方展开一行 `stripAreaPrefix(area)` 文本；再点收起。
  - 其他行、grouped(快乐8) 模式、area 空 → 无展开。
- `pages/draw/latest.vue` / `detail.vue`：`<PrizeGrades :grades="draw.prize_grades" :area="draw.prize_area" />`（history 列表项不展开奖级表，不传）。

## 3. 错误处理

- prize_area 缺失/空 → 前端无展开入口（其他彩种、旧数据）。
- stripAreaPrefix 对空/无冒号文本安全返回。

## 4. 测试

- 后端 pytest：persist_draw 存 prize_area；序列化器暴露 prize_area；ssq spider parse 带 prize_area（mock content）；3d/kl8 spider parse 无 prize_area 或空（不破坏）。
- 前端 vitest：stripAreaPrefix（去前缀 / 空 / 无冒号）。
- 控制端：重抓 ssq，起后端验证 ssq draw/latest 返回 prize_area，前端一等奖可点开显示分省。

## 5. 怎么看效果

双色球当期/详情：一等奖行尾有"▼分省"，点开显示"北京1注、内蒙古1注、广东3注…共8注"；其他奖级和其他彩种无此入口。

## 6. 里程碑定位

note.txt 第 1 项（中奖信息补全，一等奖分省）。后续：G 体验版（10）→ dlt 翻页抓满一年（可选）。
