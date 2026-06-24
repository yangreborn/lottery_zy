# 历史开奖数据填充（约一年真实数据）· 设计文档

- 日期：2026-06-24
- 定位：把约一年的真实官方开奖数据抓进数据库并发布，让历史页/统计页有真实深度。对应 note.txt 第 2 项"补全历史的统计信息"的数据基础。
- 前置：M1 爬虫（ssq/dlt spider + crawl_draw + persist_draw）、DrawResult 模型、M2a 统计接口均已就绪。

---

## 0. 范围

**本期做**：① `BaseSpider.run(count)` 支持抓多期；② 新增 `load_history` 命令（抓 N 期真实官方数据 → 入库 → 发布）；③ 实际跑一次灌入约一年的双色球/大乐透真实开奖。
**不做**：统计实时算（已有 compute_number_stats，本期不动）；不建预计算统计表（数据量小，实时算足够）；前端不动（历史/统计页自动用上新数据）；统计"最多/最少"筛选（note 第 11 项，属后续 D）。

## 1. 数据来源（真实官方）

- 双色球(ssq)：中国福彩网 `http://www.cwl.gov.cn/.../findDrawNotice`，参数 `name=ssq&issueCount=N` 返回最近 N 期。已实测可达（HTTP 200，返回真实号码/奖池/奖级/销售额）。
- 超级大乐透(dlt)：中国体彩网 `https://webapi.sporttery.cn/.../getHistoryPageListV1.qry`，参数 `pageSize=N`。
- 现有 `SsqSpider.fetch(issue_count)` / `DltSpider.fetch(page_size)` 已支持期数参数，仅 `run()` 未透传。

## 2. 爬虫 run(count) 改造

`crawler/spiders/base.py` 的 `BaseSpider.run` 由 `run(self)` 改为 `run(self, count=1)`，实现 `return self.parse(self.fetch(count))`。两个 spider 的 `fetch` 第一个位置参数即期数（issue_count / page_size），`self.fetch(count)` 对两者都成立。`fetch`/`parse` 抽象方法签名与子类不变。

## 3. load_history 命令

`crawler/management/commands/load_history.py`：
- 参数：`--count`（默认 160，约一年）、`--code`（可选，缺省抓全部已注册彩种）。
- 逐彩种：取 Lottery 配置 → `spider.run(count)` 得 items → 逐条 `persist_draw(lottery, item)`；persist 成功（返回 obj 非 None）则**发布**：`obj.status = DrawResult.STATUS_PUBLISHED; obj.save(update_fields=["status"])`。
- 容错：彩种未注册/配置缺失 → logger.warning 跳过；某彩种 `run` 网络异常 → logger.error(exc_info=True) 跳过（不影响其他彩种）；单条 persist 异常 → 跳过（沿用 crawl_draw 的按条 try/except）。
- 统计并 logger.info 每彩种入库/发布条数。
- **persist_draw 不改**（仍写 draft，供常规 crawl_draw 的人工审核流程）；发布仅在本命令内做（真实官方数据可信，直接发布）。

## 4. 实际灌数据（运行步骤）

`python manage.py load_history --count 160`：双色球 + 大乐透各抓约一年真实开奖（约 300+ 条）入库并发布。这是一次性 bootstrap，之后日常用 crawl_draw 增量抓最新。

## 5. 前端

无改动。历史页（倒序分页）与统计页（最近 10/30/50/100 期号码出现/遗漏，从 DrawResult 实时 compute_number_stats）会自动展示这一年数据。

## 6. 错误处理

- 网络不可达：该彩种 run 抛异常被捕获、logger.error，命令继续下一彩种；已抓到的不回滚。
- 单条号码校验失败：persist_draw 已有 `validate_numbers` 守卫，不入库 + warning。
- 重复抓取：persist_draw 用 `update_or_create(lottery, issue)`，幂等；重跑 load_history 不产生重复，已存在的更新并发布。

## 7. 测试

- **pytest（mock 网络）**：
  - `run(count)`：用一个 fake spider 子类（fetch 记录收到的 count），断言 `run(7)` 把 7 传给 fetch。
  - `load_history`：monkeypatch SPIDERS 或 spider.run 返回固定 items（2-3 条合法），断言对应 DrawResult 入库且 `status=published`；幂等（跑两次条数不变）；某彩种 run 抛异常时不影响另一彩种、命令不崩。
  - 测试**不打真实网络**。
- **真实抓取验证（运行步骤）**：执行时真跑一次 `load_history --count 160`，确认 ssq/dlt 各入库约一年条数、published 可被 `/api/openapi/draw/history` 与 `draw/stats` 读到。

## 8. 怎么看效果

跑 `load_history --count 160` 后启后端：历史页能往下翻约一年各期；统计页选近 100 期有真实的号码出现/遗漏分布。

## 9. 里程碑定位

note.txt 第 2 项的数据基础（历史数据填充）。后续：D 统计筛选（最多/最少，11）→ C 记录分组（7）→ A 新彩种（3/4）→ F 中奖信息（1）→ G 体验版（10）。
