# 通知体系 · 设计文档

- 日期：2026-06-25
- 定位：里程碑 4。对应 note.txt 第 17、18、19 项。
- 后续里程碑：微信登录(14) → 开奖海报(22)。

---

## 0. 范围

**本期做**：① 玩法介绍改名「玩法说明」并新增「通知」类型承载彩票中心历史通知（17）；② 首页通知栏展示重要通知（18）；③ note 19 调研结论：通知由运营 admin 录入。
**不做**：不接官方通知 API（无稳定开放接口）；不做通知推送/订阅；不改开奖爬虫。

## 1. note 19 调研结论

开奖数据有 cwl.gov.cn 接口（爬虫已用 ssq/kl8/3d），但 cwl.gov.cn / lottery.gov.cn 的**通知/公告无稳定开放免费 API**。故通知内容由运营在 Django admin 手动录入（PlayGuide 的 notice 类型），不依赖第三方接口。

## 2. 后端（`guide` app，复用 PlayGuide）

### 2.1 模型改动（`guide/models.py`）
- 加字段 `is_important = BooleanField("重要通知", default=False)` —— 首页通知栏只展示重要通知。
- `TYPE_CHOICES` 加 `TYPE_NOTICE = "notice"`，label「通知公告」—— 承载彩票中心历史通知。
- `Meta.verbose_name`「玩法介绍」→「玩法说明」（note 17）。
- migration：makemigrations guide。

### 2.2 serializer（`guide/serializers.py`）
- `GuideListSerializer` fields 加 `is_important`（GuideDetailSerializer 同步加，便于详情区分）。

### 2.3 接口（`guide/views.py`）
- `GuideListView` 加查询参数 `important`：`?important=1` 时 `filter(is_important=True)`。其余逻辑（code/type 过滤、_visible_qs 上架+已发布）不变。
- 首页通知栏调 `GET /api/openapi/guide/list?important=1`（可不带 code，取通用+全部彩种重要通知，按现有 ordering `sort,-publish_at`）。

### 2.4 admin（`guide/admin.py`）
- `PlayGuideAdmin` 的 list_display/list_filter 加 `is_important`，list_editable 加 `is_important`，方便运营快速标记重要通知。

## 3. 前端 17（玩法说明 + 通知类型）

- `pages/guide/index.vue`：TopBanner 标题「玩法介绍」→「玩法说明」；`types` 数组加 `{ key: 'notice', label: '通知' }`。
- `utils/menu.js`：HOME_MENU 的 guide 项 `title`「玩法介绍」→「玩法说明」。
- 历史通知 = `notice` 类型 PlayGuide，复用现有列表行 + 详情页展示，无需新页面。

## 4. 前端 18（首页通知栏）

- 新组件 `components/NoticeBar.vue`：📢 图标 + 最新一条重要通知标题（单条、省略号截断）；`@click` 触发 `tap` 事件。
- `pages/home/index.vue`：banner 下、grid 上插入 `<NoticeBar :notice="topNotice" @tap="goNotices" />`；onShow/onLoad 调 `getNotices()` 取重要通知列表，取第一条为 `topNotice`；无重要通知（空或失败）→ 不渲染通知栏。
- `goNotices`：`uni.navigateTo` 到 `/pages/guide/index`（玩法说明页，用户可切到「通知」tab 看全部）。
- `api/guide.js` 加 `getNotices(code)` → `GET /api/openapi/guide/list?important=1`（带 code 可选）。

## 5. 错误处理

- 首页 `getNotices` 失败 → `topNotice` 保持空，通知栏不渲染，不阻塞首页其余内容。
- 通知列表空 → 玩法说明页现有空态提示。

## 6. 测试

- 后端 pytest（`guide/tests/` 照现有 guide 测试模式）：
  - `?important=1` 只返回 `is_important=True` 且可见的条目；不带 important 返回全部可见。
  - `type=notice` 过滤返回 notice 类型。
  - serializer 输出含 `is_important`。
- 前端 vitest：`getNotices('ssq')` 命中 `/api/openapi/guide/list` 且 data 含 `important: 1`（+ code）；`getNotices('')` 不带 code；HOME_MENU guide 改名后 title 断言（如有）。
- 不删既有测试。

## 7. 里程碑定位

note.txt 第 17、18、19 项。后续：微信登录(14) → 开奖海报(22)。
