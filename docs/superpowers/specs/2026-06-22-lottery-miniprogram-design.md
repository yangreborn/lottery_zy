# 彩票工具小程序 · 设计文档

- 日期：2026-06-22
- 定位：开奖查询 + 选号记录 + 玩法资讯 的**工具/资讯类**小程序
- MVP 彩种：双色球(ssq) + 超级大乐透(dlt)

---

## 0. 合规前提（重要）

国内彩票"销售 / 代购 / 预测"类功能为微信小程序禁止类目（2015 年起网售彩票全面叫停）。本项目仅做**查询、记录、资讯**，属工具/资讯类，合规可上架。设计须守住边界：

- **不做**：售彩、代购、号码预测/推荐。
- 统计功能（号码出现次数、遗漏值、冷热）仅作**数据陈列**，不得包装成"推荐/预测"。
- 付费点（后续）须绑定到**统计/数据/工具**类增值，不得绑定预测，避免被判变相博彩。

## 1. 技术栈

- **前端**：uni-app (Vue)，一套代码编译到 **微信小程序（主，优先）** + H5/PC。
- **后端**：Django 5.2 LTS（支持到 2028-04）+ DRF，Python 3.12（爬虫用 Python 顺手；后台蹭 Django Admin 起步）。
- **数据库**：PostgreSQL 17（EOL 2030-11；JSONB 支持好）。不用快 EOL 的 PG14。
- **管理后台**：Django Admin 起步，运营看板用 admin 自定义视图 / 简单页面。
- API 返回格式统一 `{code, msg, data, error}`。
- 日志用 `logging` 标准库（`logging.info/warning/error`，异常用 `exc_info=True`），不用 `print`。

### 部署与成本（完全独立项目，新服务器，成本优先）

MVP 流量小，**单台轻量应用服务器全包**，避免使用贵的托管组件：

| 项 | 方案 | 成本 |
|---|---|---|
| 服务器 | 腾讯云/阿里云**轻量应用服务器** 2C2G/2C4G，单台跑 Django+PG+nginx+爬虫 | ~¥70–120/月（活动/新用户更低） |
| 数据库 | PG **自建在同一台机器**，不用 RDS | ¥0（RDS PG ¥100+/月，MVP 不值） |
| 任务调度 | **crontab** 调 management command，不上 Celery/Redis | ¥0 |
| 静态/图片 | OSS/COS | 接近免费 |
| 域名 | 必备，小程序要求 HTTPS + **ICP 备案**（免费但要办，个人可备案） | ~¥50/年 |
| SSL | Let's Encrypt | ¥0 |

- **砍掉**：RDS、K8s、负载均衡、Celery/Redis。备份用 `pg_dump` 定时打包传 OSS。
- 整体 **~¥100/月起**。流量起来后再把 PG 拆 RDS、加 Redis，架构不返工。

## 2. 整体架构

```
前端 (uni-app)  —— 微信小程序(主) / H5(PC)
        │ HTTPS JSON (DRF)
后端 (Django+DRF)
        ├─ openapi : 只读查询接口（无需登录）
        ├─ user    : 登录 / 我的号码 /（预留会员）
        └─ admin   : 管理后台（数据维护 + 运营看板）
数据采集层
        ├─ 爬虫（定时任务，每期开奖后触发）
        ├─ 人工兜底（后台录入/修正）
        └─ 数据校验 / 失败告警
```

**关键原则**：前端**永远只读后端自有库**，不直接依赖第三方。爬虫只是灌库手段之一，挂了不影响用户查询；人工随时能补。

### 数据来源链路（爬虫为主 + 人工兜底）

1. **定时爬虫**：开奖后触发（双色球 周二/四/日，大乐透 周一/三/六，约 21:30）。MVP 用 crontab 调 management command；量大再上 Celery beat。
2. **数据校验**：读 `rule_config` 校验号码个数/范围、期号连续性；异常**不入库 + 告警**。
3. **人工兜底**：失败/可疑时后台手动录入或修正；每条记录带 `source` 与审核状态。
4. **奖池/奖金**：官网结构常变，爬虫抓不到时后台手动维护。

## 3. 数据模型

### Lottery 彩种表（配置化，加彩种不改代码）
| 字段 | 说明 |
|---|---|
| code | 唯一标识（ssq / dlt） |
| name | "双色球" |
| category | 福彩 / 体彩 |
| rule_config | JSON：`{red:{count:6,min:1,max:33}, blue:{count:1,min:1,max:16}}` |
| draw_days | 开奖星期 `[2,4,7]` |
| is_active | 是否上架 |

> 号码区规则放 JSON，选号器、随机算法、校验统一读这份配置；加新彩种只插一条数据。

### DrawResult 开奖结果表（核心）
| 字段 | 说明 |
|---|---|
| lottery_id | 外键 |
| issue | 期号（唯一约束：lottery+issue） |
| draw_date | 开奖日期 |
| numbers | JSON `{red:[...], blue:[...]}` |
| sales_amount | 当期销售额 |
| pool_amount | 奖池金额（人工可改） |
| prize_grades | JSON `[{level, count, amount}, ...]` |
| source | crawler / manual |
| status | draft / published（人工审核后才 published，前端只查 published） |
| created_at / updated_at / updated_by | 审计 |

### UserNumber 用户记录号码表
| 字段 | 说明 |
|---|---|
| user_id | 外键（**hash 形式存，不暴露真实 id**） |
| lottery_id | 外键 |
| numbers | JSON `{red:[...], blue:[...]}` |
| gen_type | manual / random / dan_random（定胆随机） |
| dan_numbers | JSON 定胆锁定号码（可空） |
| note | 备注（可空） |
| target_issue | 目标期号（可空，用于自动比对） |
| created_at | |

### PlayGuide 玩法介绍表
| 字段 | 说明 |
|---|---|
| lottery_id | 外键（可空 = 通用） |
| type | 玩法说明 / 奖级规则 / 活动 |
| title / content / sort / is_active / publish_at | content 为富文本 |

### AccessLog 埋点 / 统计
- 字段：`user_id, path, lottery_code, action, created_at`
- 后台聚合 DAU、热门彩种、功能使用分布；高频写，后期再考虑异步/聚合表。

**取舍**：`numbers`/`prize_grades` 用 JSON 而非拆列——双色球(6+1)与大乐透(5+2)结构不同，JSON 配合 `rule_config` 一张表通吃。`status` 两态防脏数据直面用户。

## 4. 功能模块

### 模块一：中奖号码查看（只读，无需登录）
- 当期：开奖号码、日期、期号、奖池、各奖级中奖注数+单注奖金。
- 历史：期号倒序分页，支持日期区间筛选。
- 出现情况统计：最近 N 期（10/30/50/100）每个号码的出现次数 / 遗漏值 / 冷热，热力图展示。**纯陈列，不预测。**

API：
```
GET /api/openapi/lottery/list
GET /api/openapi/draw/latest?code=ssq
GET /api/openapi/draw/history?code=ssq&page=&date_from=&date_to=
GET /api/openapi/draw/detail?code=ssq&issue=2026073
GET /api/openapi/draw/stats?code=ssq&periods=30
```

### 模块二：记录自己的号码（需登录）
- 选号器读 `rule_config` 动态渲染。
- 手动选 / 机选(随机) / 定胆随机（锁定胆码，剩余位随机补全）。
- 保存到"我的号码"，可备注、标记目标期号。
- 中奖比对：目标期开奖后自动比对命中红/蓝个数，提示中几等奖（仅比对展示，不兑奖）。
- 随机 / 定胆随机算法放**后端**统一。

API：
```
POST   /api/user/login           微信 code 换 session
POST   /api/user/number/create   {code, numbers, gen_type, dan_numbers, note, target_issue}
GET    /api/user/number/list?code=
DELETE /api/user/number/{id}
GET    /api/user/number/check?id=
```

### 模块三：玩法介绍（只读）
- 彩种介绍、投注玩法、奖级规则表、活动公告，走 `PlayGuide` 表。

API：
```
GET /api/openapi/guide/list?code=ssq&type=
GET /api/openapi/guide/detail?id=
```

### 模块四：管理后台
- 开奖数据维护：列表/编辑开奖号码、奖池、奖金；draft 一键审核发布；手动新增/修正。
- 爬虫管理：手动触发抓取、查看抓取日志/失败告警。
- 玩法内容管理：增删改 PlayGuide。
- 运营看板：DAU/新增用户、热门彩种、功能使用分布、记录号码趋势（来自 AccessLog 聚合）。

## 5. 变现（不做收费会员）

**会员收费功能不做** —— 应用所有功能对所有用户免费，**不建会员表、不做付费墙、不接任何支付**。本节仅作背景说明，不进入实现范围。

- 不做付费的背景：个人主体小程序无法开通微信支付（个人开发者禁用支付类接口）；商户号需营业执照；"跳 H5 付费"也不绕过商户号门槛。综合决定 MVP 及当前阶段不收费。
- 唯一可选、且不需收费会员的变现：**流量主广告**（个人主体小程序即可开通，条件 UV≥1000 且无违规，无需商户号）。是否接入广告后续再定，**不在当前实现范围**。
- 数据模型中**不再预留** Membership / FeatureFlag 表。

## 6. 爬虫设计

抓取源：优先中彩网/体彩官网开奖接口（JSON 比 HTML 稳），失败回退新浪/500 解析。每彩种独立 spider 类（不强行合并成分发器）。

```
spiders/
  base.py   # 抽象 fetch() / parse() / validate()
  ssq.py    # 双色球
  dlt.py    # 大乐透
```

流程：定时触发 → fetch → parse（转统一结构）→ validate（读 rule_config）→ 通过写 draft，失败记日志+告警等人工。调度 MVP 用 crontab：`python manage.py crawl_draw --code=ssq`。

## 7. 目录结构

后端（Django app）：
```
lottery_backend/
  lottery/      # 彩种配置 + 开奖结果（模型/openapi）
  usernumber/   # 用户记录号码
  guide/        # 玩法介绍
  stats/        # 埋点 AccessLog + 看板聚合
  crawler/      # spiders + management commands
  common/       # make_response / 登录鉴权 / JSON 校验工具
```

前端（uni-app）：
```
pages/
  draw/   # 当期/历史/详情/统计
  mine/   # 我的号码：选号器/列表/比对
  guide/  # 玩法介绍
components/
  number-picker  # 选号器（读 rule_config）
  ball           # 号码球
  heatmap        # 出现统计热力图
```

## 8. 实施阶段（里程碑）

1. **M1 数据底座**：彩种配置 + 开奖表 + 双色球/大乐透爬虫 + Django Admin 维护 → 稳定灌库。
2. **M2 查询前端**：uni-app 搭起，当期/历史/详情，跑通小程序。
3. **M3 统计 + 记录号码**：出现/遗漏统计、选号器、随机/定胆随机、中奖比对。
4. **M4 玩法介绍 + 运营看板**：内容管理 + 埋点 + 后台看板。
5. **M5 PC(H5) 适配**：H5 build 调样式，PC 端布局适配。
