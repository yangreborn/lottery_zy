# 实时开奖抓取 + 界面小改 实现计划

> **For agentic workers:** 用 TDD 逐任务执行。步骤用 `- [ ]` 勾选。

**Goal:** 首页移除玩法说明入口、修复风格面板遮挡、用 django-rq 在开奖第一时间自动抓取并发布。

**Architecture:** rqscheduler 每分钟触发 `dispatch_due_polls` → 命中开奖窗口的彩种入队 → rqworker 执行 `poll_lottery` 抓取+发布。见同名 spec。

**Tech Stack:** Django 5.2 + django-rq + rq-scheduler + Redis;uni-app 前端。

## Global Constraints

- 日志用 `logging`,异常用 `logging.error(..., exc_info=True)`,不用 print / 不用 logging.exception。
- 回复/注释用中文。
- `.env`/密钥不进 git;Redis 仅监听 127.0.0.1。
- 后端本地测试无 postgres → 用临时 sqlite 设置跑 pytest。

---

### Task 1: 前端移除玩法说明入口

**Files:** Modify `lottery_frontend/src/utils/menu.js`;Test `lottery_frontend/tests/menu.test.js`

- [ ] 改 `menu.test.js`:`HOME_MENU` 长度断言改 6,加 `expect(keys).not.toContain('guide')`,删除对 guide 的断言。
- [ ] 跑 `npm test -- menu` 看失败。
- [ ] `menu.js` 删除 `{ key: 'guide', ... }` 那条。
- [ ] 跑测试通过。

### Task 2: 修复风格面板底部遮挡

**Files:** Modify `lottery_frontend/src/components/ThemePicker.vue`

- [ ] `.sheet` 的 `padding-bottom` 改成 `calc(120rpx + env(safe-area-inset-bottom))`。
- [ ] `npm run build:h5` 确认编译通过(纯 CSS,无单测)。

### Task 3: Lottery 加 draw_time 字段 + 迁移 + 回填

**Files:** Modify `lottery_backend/lottery/models.py`、`lottery/management/commands/seed_lotteries.py`;Create migration;Test `lottery_backend/lottery/tests/test_draw_time.py`

- [ ] 写测试:seed 后各彩种 `draw_time` 等于期望值(ssq 21:15 等)。
- [ ] 跑测试失败。
- [ ] `models.py` 加 `draw_time = models.CharField("开奖时间", max_length=5, blank=True, default="")`。
- [ ] `makemigrations lottery`。
- [ ] `seed_lotteries.py`:每个 SEED 加 `"draw_time"`(ssq 21:15、dlt 21:25、kl8 21:30、3d 20:30、pl3 20:30)。
- [ ] 跑测试通过。

### Task 4: 依赖 + settings 配置 RQ

**Files:** Modify `lottery_backend/requirements.txt`、`lottery_backend/config/settings.py`

- [ ] `requirements.txt` 加 `redis`、`django-rq`、`rq-scheduler`。
- [ ] `settings.py`:`INSTALLED_APPS` 加 `django_rq`;加 `RQ_QUEUES`(HOST/PORT/DB 走环境变量,默认本机)与 `POLL_WINDOW_MINUTES`。
- [ ] `python manage.py check` 通过(测试环境装好依赖)。

### Task 5: due_codes 判定逻辑

**Files:** Create `lottery_backend/crawler/schedule.py`;Test `lottery_backend/crawler/tests/test_schedule.py`

**Interfaces:** Produces `due_codes(now: datetime) -> list[str]`。

- [ ] 写测试(freeze now + 造 Lottery/DrawResult):
  - 开奖日 + 窗口内 + 今日未出 → 命中
  - 非开奖日 / 窗口外(早于 draw_time 或晚于 +90min) / 今日已出 / draw_time 空 → 不命中
- [ ] 跑失败。
- [ ] 实现 `due_codes`:遍历 `Lottery.objects.filter(is_active=True).exclude(draw_time="")`,按 isoweekday、时间窗、最新 published draw_date < today 判定。
- [ ] 跑通过。

### Task 6: poll_lottery 抓取任务

**Files:** Create `lottery_backend/crawler/tasks.py`;Test `lottery_backend/crawler/tests/test_tasks.py`

**Interfaces:** Produces `poll_lottery(code: str) -> None`。

- [ ] 写测试:mock `SPIDERS[code]().run()` 返回一条合法 item → DrawResult 存在且 `status=published`;再调一次不重复(幂等)。未注册 code / spider 抛错 → 不抛出、记日志。
- [ ] 跑失败。
- [ ] 实现 `poll_lottery`:取 spider 与 lottery,`run()` 后 `persist_draw` 再置 published;异常 `logging.error(..., exc_info=True)`。
- [ ] 跑通过。

### Task 7: dispatch_due_polls + setup_schedules 命令

**Files:** Modify `lottery_backend/crawler/schedule.py`(加 dispatch);Create `lottery_backend/crawler/management/commands/setup_schedules.py`;Test `lottery_backend/crawler/tests/test_dispatch.py`

**Interfaces:** Consumes `due_codes`、`poll_lottery`。Produces `dispatch_due_polls()`。

- [ ] 写测试:mock `due_codes` 返回 `['ssq','3d']` 与 mock queue → 断言 `enqueue(poll_lottery, 'ssq')`、`'3d'` 各一次。
- [ ] 跑失败。
- [ ] 实现 `dispatch_due_polls`:`django_rq.get_queue('default')` 遍历入队。
- [ ] `setup_schedules` 命令:用 rq-scheduler `cron("* * * * *", func=dispatch_due_polls, ...)`,注册前先按 id 清理旧任务(幂等)。
- [ ] 跑通过。

### Task 8: 部署文档补 Redis + 两个 systemd

**Files:** Modify `docs/deploy-ecs.md`

- [ ] 补一节:装 redis-server;`lottery-rqworker`、`lottery-rqscheduler` 两个 systemd unit;部署后跑 `setup_schedules`;`.env` 可选 `REDIS_*`/`POLL_WINDOW_MINUTES`。

### 收尾

- [ ] 后端全量 pytest(临时 sqlite 设置)通过;前端 `npm test` + `build:h5` 通过。
- [ ] 提交(按用户确认再 push)。
