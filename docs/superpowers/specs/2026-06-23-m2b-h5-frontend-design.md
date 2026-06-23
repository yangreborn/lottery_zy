# M2b · uni-app H5 查询前端 · 设计文档

- 日期：2026-06-23
- 定位：把已就绪的 M1/M2a 只读查询接口，用 uni-app 做成可在**浏览器（H5）**直接看到效果的前端；同一套代码以后可编译微信小程序。
- 前置：M1 数据底座 + M2a 查询 API（5 个只读接口）+ M3 记录号码后端均已合并到 master。

---

## 0. 范围

**本期做**：当期开奖、历史列表、单期详情、号码出现/遗漏统计 —— 全部走免登录只读接口。
**不做（延后）**：我的号码（登录/选号器/机选/定胆/中奖比对，属下一期前端）；微信小程序端编译调试；PC 专门适配（H5 自适应即可）。

## 1. 技术栈

- **前端**：uni-app（Vue3 + Vite），CLI 方式（`uni-preset-vue#vite`），JavaScript（不引 TS，保持轻量）。
- **预览目标**：H5（`npm run dev:h5` 起 Vite 开发服务器，浏览器即看）。
- **测试**：vitest 单测 API 封装层与纯函数；页面视觉人工核对。
- **后端改动**：仅加 `django-cors-headers`，DEBUG 下放开本地源。

## 2. 目录结构

```
lottery_frontend/                 # 仓库根，与 lottery_backend 平级
  src/
    api/
      request.js                  # uni.request 封装，解析 {code,msg,data,error}
      lottery.js                  # 各接口函数 getLotteryList/getLatest/getHistory/getDetail/getStats
    pages/
      draw/
        latest.vue                # 当期开奖（首页）
        history.vue               # 历史列表（分页+日期）
        detail.vue                # 单期详情（奖级表）
        stats.vue                 # 出现/遗漏统计（热力图）
    components/
      Ball.vue                    # 号码球（红/蓝）
      LotteryTabs.vue             # 彩种切换（ssq/dlt）
      Heatmap.vue                 # 统计热力图
    store/
      lottery.js                  # 轻量 reactive，仅存当前彩种 code
    utils/
      format.js                   # 纯函数：奖池金额格式化、号码球颜色判定、统计格子配色分档
    main.js / App.vue / pages.json / manifest.json
  vite.config.js / package.json
  tests/                          # vitest 单测（api 封装 + utils 纯函数）
  .env.development                # VITE_API_BASE=http://127.0.0.1:8000
```

## 3. 架构与数据流

```
浏览器(H5)  ──uni.request──▶  Django(:8000) /api/openapi/*
   │                              │ 已就绪只读接口
 pages/draw/*  ◀── api/lottery.js ── request.js(拆 {code,msg,data,error})
```

- **API 封装** `request.js`：统一拼 `VITE_API_BASE` + path，GET 传 query；返回 resolve `data`（code=0）或 reject `{code,msg}`（code!=0 / 网络错误），页面用 `uni.showToast` 提示。
- **接口函数** `api/lottery.js`：
  - `getLotteryList()` → `/api/openapi/lottery/list`
  - `getLatest(code)` → `/api/openapi/draw/latest?code=`
  - `getHistory(code, {page, date_from, date_to})` → `/api/openapi/draw/history`
  - `getDetail(code, issue)` → `/api/openapi/draw/detail`
  - `getStats(code, periods)` → `/api/openapi/draw/stats`
- **状态**：`store/lottery.js` 用 `reactive({code:'ssq'})`，彩种切换更新它；各页 onShow 读它拉数据。不引 Pinia/Vuex（YAGNI）。

## 4. 页面

- **当期 latest.vue**（首页）：顶部 LotteryTabs 切 ssq/dlt；展示开奖号码（Ball 红+蓝）、期号、开奖日期、奖池金额、各奖级中奖注数+单注奖金。空数据时占位提示。
- **历史 history.vue**：倒序分页列表，每行期号+日期+号码球缩略；可选日期区间筛选；点行跳详情。触底加载下一页。
- **详情 detail.vue**：单期完整信息 + 奖级表（用接口返回的 `level_label` 中文奖级）。
- **统计 stats.vue**：选最近 N 期（10/30/50/100），Heatmap 展示每个号码的出现次数/遗漏值，按次数分档配色。**纯数据陈列，不预测**（合规红线）。

## 5. 组件

- **Ball.vue**：props `{value, zone}`，红区红底、蓝区蓝底，圆形号码球。
- **LotteryTabs.vue**：props `{list, active}`，emit `change(code)`；数据来自 `getLotteryList()`。
- **Heatmap.vue**：props `{cells:[{number,count,miss}], max}`，按 count 占比分档着色，格子显示号码与次数。

## 6. 数据连通（CORS）

H5 浏览器从 Vite 源（如 `http://localhost:5173`）跨域请求 Django(:8000)，需 CORS：

- 后端加 `django-cors-headers`，加入 `INSTALLED_APPS` 与中间件最前。
- **仅 DEBUG** 下 `CORS_ALLOW_ALL_ORIGINS = True`（本地开发便利）；生产关闭、走同域 nginx。CORS 配置不属密钥，直接写 settings（按 DEBUG 分支）。

## 7. 看到效果的前提：示例数据

当前库无已发布开奖，H5 打开会空。M2b 含开发态命令：

- `python manage.py seed_sample_draws`：给 ssq/dlt 各插 3-5 期 `status=published` 开奖（含 numbers/pool_amount/prize_grades，数据为合理示例值），让 H5 一打开即有可见内容。
- 真实数据仍可用 `crawl_draw` 抓取。`seed_sample_draws` 幂等（update_or_create 按 lottery+issue）。

## 8. 错误处理

- 接口 code!=0 或网络失败：`request.js` reject，页面 `uni.showToast({title: msg})`，列表页显示空态。
- 未知彩种/无数据：后端已返回 code=1，前端按 msg 提示，不崩页。

## 9. 测试策略

- **vitest 单测**：
  - `api/request.js`：mock `uni.request`，验证 code=0 resolve data、code=1 reject、网络错误 reject。
  - `utils/format.js`：奖池金额格式化、Ball 颜色判定、统计分档配色等纯函数。
- **人工核对**：四个页面在浏览器跑 `dev:h5` 目测（用户本就要看效果）。
- 不引组件渲染/E2E 框架（uni-app 组件测试成本高，YAGNI）。

## 10. 怎么运行看效果

1. 后端：`lottery_backend` 下 `python manage.py migrate`（如需）→ `seed_lotteries` → `seed_sample_draws` → `python manage.py runserver`。
2. 前端：`lottery_frontend` 下 `npm install` → `npm run dev:h5`，浏览器打开 Vite 地址。
3. 看到：当期开奖（红蓝球+奖池+奖级）、历史分页、详情奖级表、统计热力图，可切双色球/大乐透。

## 11. 里程碑定位

本设计是总设计文档第 8 节 M2 的 H5 落地（M2b）。后续：我的号码前端（M3 前端）→ M4 玩法介绍+看板 → 微信小程序端编译。
