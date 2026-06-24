# C · 选号记录显示时间 + 分组 · 设计文档

- 日期：2026-06-24
- 定位：选号记录显示选号时间，支持用户把已有记录归到分组，"我的号码"按组展示。对应 note.txt 第 7 项。
- 前置：UserNumber 模型 + create/list/delete/check/generate 接口、mine/index.vue 列表均已就绪。

---

## 0. 范围

**本期做**：① UserNumber 加 group_name 字段 + 归组接口；② 前端纯函数 formatTime/groupRecords；③ mine/index.vue 显示选号时间 + 按组展示 + 每条"归组"操作。
**不做**：不动选号器(picker)；保存时不加分组输入（归组在列表里做）；不做删组/拖拽排序；不动其他页。

## 1. 后端：分组字段 + 归组接口

- `UserNumber` 加 `group_name = models.CharField("分组", max_length=50, blank=True, default="")`；生成迁移。
- `UserNumberSerializer` fields 加 `"group_name"`（`created_at` 已在）。
- 新增 `NumberGroupView`（`POST /api/user/number/group`，body `{id, group_name}`）：
  - 未登录 → code=1；
  - 本人记录 `UserNumber.objects.filter(id=id, user_id=uid).first()`，不存在 → code=1 "记录不存在"；
  - `group_name` 取 `str(group_name or "").strip()[:50]`（去空白、超 50 截断；空字符串=取消分组）；
  - 设置并 `save(update_fields=["group_name"])`，返回 `make_response(data=UserNumberSerializer(rec).data)`。
- urls：`path("number/group", views.NumberGroupView.as_view(), name="user-number-group")` 放在 `number/<int:pk>` **之前**。
- authentication_classes=[]（与其他 number 接口一致，认证靠 current_user_id 读 X-User-Id/session）。

## 2. 前端纯函数（utils/records.js）

- `formatTime(iso) -> string`：把 ISO 时间（如 `2026-06-23T10:05:00Z` 或带毫秒）格式化为 `YYYY-MM-DD HH:mm`。解析失败/空返回 `''`。用本地时间的年月日时分（new Date(iso) 各字段补零）。
- `groupRecords(items) -> [{name, records}]`：按 `group_name` 分组；空名（含未定义）归 `'未分组'`。命名组按 name 升序在前，`'未分组'` 殿后。非数组/空返回 `[]`。不改入参。

## 3. 前端"我的号码"页 mine/index.vue

- 列表渲染由"平铺 items"改为"按 `groupRecords(items)` 分组"：外层 `v-for group`，组名标题（如"未分组"/"机选一组"），内层 `v-for rec`。
- 每条卡片加**选号时间**：`formatTime(rec.created_at)`，小字灰色。
- 每条卡片操作区加**"归组"**：点击 → `uni.showModal({ editable: true, content: rec.group_name || '', placeholderText: '输入组名(留空取消分组)' })` → 确认取 `res.content` → `setGroup(rec.id, 组名)` → 成功后 `load()` 刷新。
- 既有"比对/删除"操作保留；空态保留。

## 4. 前端 api/user.js

- 加 `setGroup(id, group_name)` → `request('/api/user/number/group', { method: 'POST', data: { id, group_name } })`。

## 5. 错误处理

- 归组接口失败：toast 提示，沿用现有错误处理。
- formatTime/groupRecords 对空/非法返回安全值（''、[]），不崩。
- 取消分组：组名留空 → group_name='' → 该记录回到"未分组"组。

## 6. 测试

- **后端 pytest**（`usernumber/tests/test_number_group.py`）：本人记录设组名成功且 group_name 进序列化；非本人/不存在 id → code=1；未登录 → code=1；超 50 字符截断；空字符串清除分组。
- **前端 vitest**（`tests/records.test.js`）：formatTime 正常格式化 + 空/非法返回 ''；groupRecords 分组正确、未分组殿后、命名组升序、空列表返回 []、不改入参。
- **人工**：dev:h5/开发者工具看"我的号码"：每条显示时间；点"归组"输入组名后该条移到对应组；留空回到未分组。

## 7. 怎么看效果

"我的号码"页：记录按组分块展示（未分组在最下）；每条带选号时间；点某条"归组"输入"周末跟号"→ 该条移入"周末跟号"组；再点输入空 → 回未分组。

## 8. 里程碑定位

note.txt 第 7 项（记录显示时间 + 分组）。后续：A 新彩种（3/4）→ F 中奖信息（1）→ G 体验版（10）→ dlt 翻页抓满一年（可选）。
