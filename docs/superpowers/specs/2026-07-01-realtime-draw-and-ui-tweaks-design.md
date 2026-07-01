# 实时开奖抓取 + 界面小改 设计文档

> 日期：2026-07-01
> 范围：后端 `crawler`/`lottery` app(django-rq 实时抓取) + 前端两处小改。

## 目标

1. **去除玩法说明**:首页不再展示"玩法说明"入口(页面与后端保留)。
2. **风格面板遮挡修复**:切换风格弹层最后一项被自绘 tabBar 遮住。
3. **django-rq 实时抓开奖**:在官网出结果的第一时间(≤约 1 分钟)自动抓取并发布,平时不空转。

## 一、去除玩法说明(前端)

- `lottery_frontend/src/utils/menu.js`:`HOME_MENU` 移除 `key: 'guide'` 那条(7→6 项)。
- `lottery_frontend/tests/menu.test.js`:断言改为长度 6、`not.toContain('guide')`,移除对 guide 项的断言。
- 页面 `pages/guide/*`、路由 `pages.json`、后端 `guide` app **均保留**,仅去掉首页入口,便于日后恢复。

## 二、风格面板遮挡修复(前端)

- `lottery_frontend/src/components/ThemePicker.vue`:`.sheet` 的 `padding-bottom` 由
  `calc(40rpx + env(safe-area-inset-bottom))` 改为 `calc(120rpx + env(safe-area-inset-bottom))`,
  让最后一项从 App 自绘 tabBar(约 100rpx)下方露出。纯 CSS,无逻辑改动。

## 三、django-rq 实时抓开奖(后端)

### 架构

```
rqscheduler(每 1 分钟 cron) → dispatch_due_polls()   —— 轻量:只查时间 + DB
        └─ 命中开奖窗口且今日未出 → queue.enqueue(poll_lottery, code)
rqworker → poll_lottery(code):spider.run() → persist_draw → status=PUBLISHED
```

- **调度器(rqscheduler)** 周期性触发 `dispatch_due_polls`,它判断"现在该不该抓",只把该抓的彩种入队。
- **worker(rqworker)** 执行 `poll_lottery`,复用现有 spider 与 `persist_draw`,抓到即发布。
- 拿到结果后该彩种最新 `draw_date` 变为今天,下一次巡检不再入队 → **自动停,窗口外零抓取**。

### 数据模型

`Lottery` 增加字段:

```python
draw_time = models.CharField("开奖时间", max_length=5, blank=True, default="")  # "HH:MM"
```

- 迁移一份;`seed_lotteries` 回填:
  ssq=21:15、dlt=21:25、kl8=21:30、3d=20:30、pl3=20:30。
- `draw_time` 为空 → 该彩种不参与智能轮询(向后兼容)。
- `draw_days`(已存在,isoweekday 1..7)继续用于"今天是否开奖日"。

### 配置

`settings.py`:

```python
INSTALLED_APPS += ["django_rq"]
RQ_QUEUES = {
    "default": {
        "HOST": os.environ.get("REDIS_HOST", "127.0.0.1"),
        "PORT": int(os.environ.get("REDIS_PORT", 6379)),
        "DB": int(os.environ.get("REDIS_DB", 0)),
        "DEFAULT_TIMEOUT": 300,
    }
}
POLL_WINDOW_MINUTES = int(os.environ.get("POLL_WINDOW_MINUTES", 90))
```

`requirements.txt` 增加:`redis`、`django-rq`、`rq-scheduler`。

### 核心逻辑(`crawler/schedule.py`)

```python
def due_codes(now):
    """返回当前应入队抓取的彩种 code 列表。"""
    # 遍历 is_active 且 draw_time 非空的彩种：
    #   今天 isoweekday 在 draw_days 内
    #   且 draw_time <= now.time() <= draw_time + POLL_WINDOW_MINUTES
    #   且该彩种最新 published draw 的 draw_date < today（今日未出）
```

```python
def dispatch_due_polls():
    """rqscheduler 周期调用：把 due_codes(now()) 入队。"""
    import django_rq
    q = django_rq.get_queue("default")
    for code in due_codes(timezone.localtime()):
        q.enqueue(poll_lottery, code)
```

### 抓取任务(`crawler/tasks.py`)

```python
def poll_lottery(code):
    """抓取单个彩种最新开奖并发布。幂等(update_or_create)。"""
    spider_cls = SPIDERS.get(code)          # 缺失/异常记 logging 并返回
    lottery = Lottery.objects.get(code=code)
    for item in spider_cls().run():          # crawl 版 run() 抓最新
        obj, errors = persist_draw(lottery, item)
        if obj is not None:
            obj.status = DrawResult.STATUS_PUBLISHED
            obj.save(update_fields=["status"])
```

- 复用 `SPIDERS` / `persist_draw`。与 `load_history` 的发布方式一致,只是 count=最新。
- 幂等:`persist_draw` 用 `update_or_create`,重复抓不产生重复记录。

### 调度注册(`crawler/management/commands/setup_schedules.py`)

- 部署时运行一次:清掉旧的同名任务,用 rq-scheduler 的 `cron()` 注册
  `dispatch_due_polls` 每分钟执行一次。
- 幂等:重复运行不会叠加(先按 id/func 清理再注册)。

### 常驻服务(部署,补进 `docs/deploy-ecs.md`)

- 装 Redis(`apt install redis-server`,仅监听 127.0.0.1)。
- systemd `lottery-rqworker.service`:`manage.py rqworker default`。
- systemd `lottery-rqscheduler.service`:`manage.py rqscheduler`(rq-scheduler 提供)。
- 部署后跑一次 `manage.py setup_schedules`。

### 时效与容错

- 官网出结果后,最迟下一次巡检(≤1 分钟)入队,worker 秒级抓取并发布 → 满足"第一时间"。
- 抓取失败(网络/官网未更新)只记日志,下一分钟自动重试,直到今日结果到手。
- 窗口外、非开奖日、今日已出 → 完全不抓,零无效请求。

## 测试策略

后端(不联网、不依赖 Redis;spider 与 now 用 mock/freeze):

- `due_codes`:开奖日+窗口内+今日未出 → 命中;非开奖日/窗口外/今日已出 → 不命中;`draw_time` 空 → 不命中。
- `poll_lottery`:mock spider 返回一条 → 写库且 `status=published`;再抓一次不产生重复(幂等)。
- `dispatch_due_polls`:mock `due_codes` 与 queue,断言按 code 入队。

前端:

- `menu.test.js`:`HOME_MENU` 不含 guide、长度 6。
- ThemePicker 为纯 CSS,不加测试。

## 不做(YAGNI)

- 不做 WebSocket 推送/长连接(小程序/H5 用现有拉取即可)。
- `draw_time` 暂用常量窗口,不做每彩种独立窗口时长(需要再加)。
- 不改 `crawl_draw`(保留草稿语义,供人工核对场景)。
