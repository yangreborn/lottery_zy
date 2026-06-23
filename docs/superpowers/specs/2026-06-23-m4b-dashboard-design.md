# M4b · 运营看板（埋点 + 聚合 + Admin 看板）· 设计文档

- 日期：2026-06-23
- 定位：埋点记录访问行为，后台聚合出 DAU/热门彩种/功能使用分布，运营在 Django Admin 自定义看板页查看。
- 前置：M1–M4a 全部已合并到 master（含 token-in-header 鉴权、device code、各前端页面）。

---

## 0. 范围

**本期做**：AccessLog 埋点模型 + 上报接口 + 前端各页/关键动作上报 + 聚合函数 + Django Admin staff 看板视图 + AccessLog Admin。
**不做**：异步写/聚合表（高频优化后期再说）；图表库（看板用服务端渲染表格）；新增用户(注册)趋势（当前无注册概念，用 UV 近似）；微信小程序端编译。

## 1. 埋点身份（匿名设备 id）

- App 启动时确保有 token：`App.vue onLaunch` 先 `loadToken()`，若为空则 `ensureLogin()`（device code 走 mock 登录拿 token=hash）。每个浏览器一个稳定匿名身份，含纯浏览查询/玩法的访客。
- 上报请求带 `X-User-Id` 头；后端据此记 `user_id`（hash，不暴露真实 openid/IP）。

## 2. 数据模型 AccessLog（新建 stats app）

| 字段 | 类型/说明 |
|---|---|
| user_id | CharField(64, db_index, blank/default="")，匿名 hash；无头时空串 |
| path | CharField(100)，页面/动作路径，如 `draw/latest`、`mine/create` |
| lottery_code | CharField(20, blank, default="")，当前彩种 |
| action | CharField(20, default="view")，`view`/`save_number`/`check_number` |
| created_at | DateTimeField(auto_now_add, db_index) |

Meta：`ordering = ["-created_at"]`。常量 `ACTION_VIEW="view"`/`ACTION_SAVE="save_number"`/`ACTION_CHECK="check_number"`。

## 3. 上报接口

`POST /api/openapi/log`（免登录，authentication_classes=[]）：
- body `{path, lottery_code?, action?}`。
- user_id 取自 `current_user_id(request)`（已含 X-User-Id 头兜底；无则空串）。
- 写一条 AccessLog（path 缺失则不记/返回 code=1）；成功返回 `make_response(data={"logged": True})`。
- 高频写，MVP 同步插一行；后期再异步/聚合。

## 4. 聚合函数 compute_dashboard

`stats/aggregate.py` 的 `compute_dashboard(days=7) -> dict`（纯查询，可单测）：
- `pv`：近 days 天 AccessLog 总条数。
- `uv`：近 days 天 distinct user_id 数（排除空串）。
- `dau`：`[{date, count}]`，每天 distinct user_id（按日期分组，倒序近 days 天）。
- `top_lotteries`：`[{lottery_code, count}]`，按 lottery_code 计数(排除空)，降序。
- `actions`：`[{action, count}]`，按 action 计数，降序。
- 时间窗用 `timezone.now() - timedelta(days)`；按天分组用 `TruncDate`。

## 5. 看板视图（Django Admin 自定义/staff 页）

- `stats/views.py` 的 `dashboard_view`：`@staff_member_required`，调 `compute_dashboard(7)`，渲染 `stats/templates/stats/dashboard.html`（表格：PV/UV 概览、每日 DAU、热门彩种、功能分布）。无图表库。
- URL：`config/urls.py` 加 `path("dashboard/", dashboard_view, name="dashboard")`。
- `AccessLogAdmin`：list_display(user_id 截断/path/lottery_code/action/created_at)、list_filter(action/lottery_code)、date_hierarchy(created_at)，运营可查原始记录。
- 非 staff 访问 `/dashboard/` → 重定向到 admin 登录（staff_member_required 默认行为）。

## 6. 前端埋点接入

- `utils/report.js` 的 `reportAccess(path, opts={})`：POST `/api/openapi/log` `{path, lottery_code, action}`，**fire-and-forget**（`.catch(()=>{})` 静默，不阻塞页面、不弹错）。
- `App.vue onLaunch`：`loadToken()`；若 `!authState.token` 则 `await ensureLogin()`（保证每访客有 token）。
- 页面浏览（`action=view`）：5 个 tab 页（draw/latest、draw/history、draw/stats、guide/index、mine/index）+ 详情页（draw/detail、guide/detail）在 onShow/onLoad 调 reportAccess。
- 关键动作：存号成功后 `reportAccess('mine/create', {lottery_code, action:'save_number'})`；中奖比对后 `reportAccess('mine/check', {action:'check_number'})`。

## 7. 隐私 / 合规

- user_id 全程 hash；不记真实 openid、不记 IP、不记号码内容。埋点仅路径/彩种/动作/时间。
- 看板仅 staff 可见。合规与免费定位无冲突。

## 8. 错误处理

- 上报失败（网络/code!=0）：前端静默吞（fire-and-forget），绝不影响用户操作。
- log 接口 path 缺失 → code=1（前端本就不传空 path）。
- 看板聚合：无数据时各列表为空，模板显示"暂无数据"。

## 9. 测试

- **后端 pytest**：
  - AccessLog 模型默认值/常量。
  - log 接口：带 X-User-Id 头记对 user_id；不带头记空串；缺 path → code=1。
  - compute_dashboard：构造跨天/跨彩种/跨 action 的 AccessLog，断言 pv/uv/dau/top_lotteries/actions 正确；排除空 user_id/lottery_code。
  - dashboard_view：staff 访问 200、含关键字；非 staff 重定向（302）。
- **前端 vitest**：reportAccess 调用参数；上报失败被静默吞（不抛）。
- **人工**：浏览各页/存号/比对后，Admin `/dashboard/` 看聚合。

## 10. 怎么看效果

后端 runserver 8123、前端 dev:h5；浏览各页、存号、比对产生埋点；用 admin 账号登录 `http://127.0.0.1:8123/dashboard/` 看近 7 天 PV/UV、每日 DAU、热门彩种、功能使用分布。

## 11. 里程碑定位

总设计文档模块四（运营看板）落地，即 M4 后半（M4b）。至此后端 + H5 全功能完成。后续：微信小程序端编译。
