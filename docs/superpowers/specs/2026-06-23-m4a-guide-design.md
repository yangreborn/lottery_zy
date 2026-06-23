# M4a · 玩法介绍 · 设计文档

- 日期：2026-06-23
- 定位：彩种玩法说明 / 奖级规则 / 活动公告的资讯展示，补齐"查询 / 记录 / 玩法"三大模块的最后一块。
- 前置：M1/M2a/M3 后端 + M2b/M3b H5 前端均已合并到 master。

---

## 0. 范围

**本期做**：PlayGuide 模型 + 只读接口(guide/list、guide/detail) + Django Admin 内容管理 + 示例数据命令 + H5"玩法"页(列表+详情)。
**不做**：运营看板(M4b，独立子项)；富文本所见即所得编辑器(Admin 用 textarea 编 HTML)；微信小程序端编译。

## 1. 合规

玩法说明、奖级规则、活动公告均为**资讯陈列**，不含"预测/推荐"；活动公告不得导向售彩/代购。与统计页同一红线。

## 2. 数据模型 PlayGuide

| 字段 | 类型/说明 |
|---|---|
| lottery | FK(Lottery, on_delete=CASCADE, **null=True/blank=True** = 通用，如活动公告)，related_name="guides" |
| type | CharField choices：`intro`(玩法说明) / `rule`(奖级规则) / `activity`(活动公告) |
| title | CharField(100) |
| content | TextField 富文本(存 HTML 字符串，H5 用 `<rich-text>` 渲染) |
| sort | IntegerField(default=0，小在前) |
| is_active | BooleanField(default=True) |
| publish_at | DateTimeField(null=True, blank=True；空或 ≤ now 才对外可见) |
| created_at / updated_at | auto |

Meta：`ordering = ["sort", "-publish_at"]`。常量 `TYPE_INTRO="intro"`/`TYPE_RULE="rule"`/`TYPE_ACTIVITY="activity"`。

## 3. 后端接口（只读，免登录）

```
GET /api/openapi/guide/list?code=ssq&type=intro
GET /api/openapi/guide/detail?id=12
```

- **list**：返回 `is_active=True` 且(`publish_at` 为空 或 ≤ now) 的条目；按 code 过滤为"该彩种的条目 + 通用条目(lottery 为空)"；`type` 可选过滤；按 Meta ordering。`code` 缺省返回全部(含通用)。返回字段：`{id, type, type_label, title, sort, publish_at}`(列表不含 content)。
- **detail**：按 id 取单条(同样受 is_active/publish_at 约束)，返回含 `content`。不存在/未发布 → code=1。
- 统一走 `make_response`；时间用 `django.utils.timezone.now()`。
- `type_label`：intro→"玩法说明"，rule→"奖级规则"，activity→"活动公告"（serializer 提供，前端直接展示）。

## 4. Django Admin（内容管理）

`PlayGuideAdmin`：
- `list_display = ("title", "type", "lottery", "is_active", "sort", "publish_at")`
- `list_filter = ("type", "is_active", "lottery")`
- `search_fields = ("title", "content")`
- `list_editable = ("is_active", "sort")`

运营在 Django Admin 直接增删改 = "玩法内容管理"，无需自定义视图。

## 5. 示例数据命令 seed_sample_guides

幂等(update_or_create 按 title+type+lottery 唯一近似，用固定 sort/title 标识)，灌：
- 双色球：玩法说明(intro)、奖级规则(rule) 各 1 条。
- 大乐透：玩法说明(intro)、奖级规则(rule) 各 1 条。
- 通用(lottery 空)：活动公告(activity) 1 条。
content 为合理 HTML 示例(段落/列表)，不含预测/推荐字样。

## 6. 前端（lottery_frontend）

```
src/api/guide.js          getGuideList(code,type) / getGuideDetail(id)
src/pages/guide/
  index.vue               玩法页(彩种切换 + 类型切换 + 标题列表 -> 详情)
  detail.vue              rich-text 渲染 content
src/pages.json            注册 guide 两页 + tabBar 加"玩法"(第5项)
```

- **index.vue**：复用 LotteryTabs 切彩种；类型切换三按钮(玩法说明/奖级规则/活动)；onShow 按 code+type 拉 list；条目为可点标题行(显 title + type_label) → navigateTo detail。空态/错误 toast。
- **detail.vue**：onLoad 取 id 调 detail；`<rich-text :nodes="draw.content">` 渲染；标题区显 title。空态。
- tabBar 5 项：当期 / 历史 / 统计 / 玩法 / 我的（uni-app tabBar 上限 5，正好）。

## 7. 错误处理

- 接口 code!=0 / 网络失败：request reject，页面 toast + 空态。
- 详情 id 不存在/未发布：后端 code=1，前端提示。

## 8. 测试

- **后端 pytest**：
  - PlayGuide 模型默认值/字符串/通用(lottery 空)。
  - list：按 code 含通用、type 过滤、is_active 过滤、publish_at 未来不返回；list 不含 content。
  - detail：返回 content；未发布/不存在 code=1。
  - seed_sample_guides 幂等 + 条目数。
- **前端 vitest**：guide api 函数(path/data，type 空不带)。
- **人工**：`npm run dev:h5` 浏览器目测玩法 tab。

## 9. 怎么看效果

后端 `seed_sample_guides` + runserver 8123，前端 dev:h5：多出"玩法"tab，切双色球/大乐透与类型看玩法说明、奖级规则、活动，点进看富文本详情。

## 10. 里程碑定位

总设计文档模块三(玩法介绍)落地，即 M4 的前半(M4a)。后半 M4b 运营看板(AccessLog 埋点+看板)为独立子项，随后做。再后：微信小程序端编译。
