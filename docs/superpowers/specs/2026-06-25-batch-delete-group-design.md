# 批量删除 + 批量归组 · 设计文档

- 日期：2026-06-25
- 定位：里程碑 3「记录区重构」第二个子里程碑。对应 note.txt 第 25 项。
- 前置：子项 15（IA改名+反馈）已完成合并。后续子项：23 购买记录。

---

## 0. 范围

**本期做**：「我的号码」页支持批量删除、批量归组（多选模式 + 后端批量接口）。
**不做**：不动单条操作（归组/比对/删除保持原样）；不做购买记录(23)；不做跨彩种批量（批量仅作用于当前彩种列表内）。

## 1. 后端（`usernumber` app）

沿用现有 APIView + `current_user_id` + `make_response` 模式；批量操作用 `filter(id__in=ids, user_id=uid)` 保证只动当前用户记录、且原子。

### 1.1 `BatchDeleteView`
- `POST /api/user/number/batch_delete`，body `{ids: [int]}`。
- `uid = current_user_id(request)`；无 uid → `code=1, msg="未登录"`。
- `ids` 非 list 或空 → `code=1, msg="请选择记录"`。
- `n, _ = UserNumber.objects.filter(id__in=ids, user_id=uid).delete()`；返回 `make_response(data={"deleted": n})`。

### 1.2 `BatchGroupView`
- `POST /api/user/number/batch_group`，body `{ids: [int], group_name: str}`。
- 同样未登录/空 ids 校验。
- `group_name = str(request.data.get("group_name") or "").strip()[:50]`（空串=清除分组）。
- `n = UserNumber.objects.filter(id__in=ids, user_id=uid).update(group_name=group_name)`；返回 `make_response(data={"updated": n})`。

### 1.3 路由（`usernumber/urls.py`）
- `path("number/batch_delete", views.BatchDeleteView.as_view(), name="user-number-batch-delete")`
- `path("number/batch_group", views.BatchGroupView.as_view(), name="user-number-batch-group")`
- 注意：放在 `number/<int:pk>` 之前，避免被 `<int:pk>` 误匹配（batch_delete 非整数不会冲突，但顺序上置前更稳）。

## 2. 前端 `pages/mine/index.vue`

### 2.1 多选状态
- `manageMode`（ref bool）、`selectedIds`（ref array，复用 `utils/picker.js` 的 `toggleIndex`）。

### 2.2 顶部 bar
- 加「管理」按钮（与「去选号」并列）：点击切换 `manageMode`，进入后文案变「完成」；退出时 `selectedIds = []`。

### 2.3 卡片
- `manageMode` 时每条 card 左侧显示勾选圈（`✓`/`○`），点 card 调 `toggleSel(rec.id)`。
- `manageMode` 时隐藏单条「归组/比对/删除」ops；非 manageMode 时单条 ops 原样保留。

### 2.4 底部操作栏（仅 manageMode）
- 固定底部：**全选/取消全选**、**批量归组(N)**、**批量删除(N)**（N=`selectedIds.length`，为 0 时归组/删除禁用）。
- 全选：选中当前列表全部记录 id；已全选则清空。
- **批量删除**：`uni.showModal({title:'确认删除', content:'删除选中的 N 条？删除后不可恢复'})` → confirm 才 `batchDelete(selectedIds)` → `load()` + 退出多选。
- **批量归组**：`uni.showModal({editable:true, placeholderText:'输入组名(留空取消分组)'})` → confirm → `batchGroup(selectedIds, content.trim())` → `load()` + 退出多选。

### 2.5 api（`api/user.js`）
- `batchDelete(ids)` → `request('/api/user/number/batch_delete', { method:'POST', data:{ ids } })`
- `batchGroup(ids, group_name)` → `request('/api/user/number/batch_group', { method:'POST', data:{ ids, group_name } })`

## 3. 错误处理

- 未登录/空 ids → `code=1` 提示。
- 批量只作用于 `user_id=uid` 的记录，混入他人 id 静默跳过（不报错、不影响他人数据）。
- 批量操作失败 → 前端 toast 错误信息。

## 4. 测试

- 后端 pytest（`usernumber/tests/test_number_batch.py`，照 `test_number_list_delete.py`：`auth_client` login fixture + `_make_record(openid)` + `hash_user_id`）：
  - batch_delete：删除自己的多条；混入他人 id 时他人记录不被删；空 ids → code=1；未登录 → code=1。
  - batch_group：给自己多条设组名（update 生效）；空 group_name 清除分组；他人 id 不受影响。
- 前端 vitest（并入 `tests/user.test.js`）：`batchDelete([1,2])`、`batchGroup([1,2],'A')` 命中正确端点与参数。`toggleIndex` 多选切换已有测试覆盖。
- 不删既有测试。

## 5. 里程碑定位

note.txt 第 25 项。里程碑 3 后续：23 购买记录。之后里程碑：通知体系(19/17/18) → 微信登录(14) → 开奖海报(22)。
