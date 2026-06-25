# 购买记录 · 设计文档

- 日期：2026-06-25
- 定位：里程碑 3「记录区重构」第三个（最后）子里程碑。对应 note.txt 第 23 项。
- 前置：子项 15（反馈）、25（批量操作）已合并。

---

## 0. 范围

**本期做**：记录用户每期实际购买的号码（独立于「我的号码」=只选不买）。含后端独立表 + CRUD 接口、前端购买记录列表页 + 手动新增选号页 + 从「我的号码」一键转入。
**不做**：金额/盈亏账本、自动比对开奖中奖（后续可扩展）；机选（新增页仅手选）。

## 1. 数据模型（`usernumber` app，与 UserNumber 并列、独立表）

`PurchaseRecord`（沿用现有 model 风格）：
- `user_id`：CharField(64, db_index)，用户 hash。
- `lottery`：ForeignKey(Lottery, on_delete=CASCADE, related_name="purchases")。
- `issue`：CharField(20)，期号。
- `numbers`：JSONField，号码（结构同 UserNumber.numbers）。
- `bet_count`：PositiveIntegerField，注数，默认 1。
- `purchase_date`：DateField，购买日期。
- `created_at`：DateTimeField(auto_now_add)。
- Meta：verbose_name「购买记录」，ordering `["-purchase_date", "-created_at"]`。
- 与 UserNumber 完全独立（不同表，互不影响）。

migration：makemigrations usernumber。admin：注册 PurchaseRecord（list_display id/user_id/lottery/issue/bet_count/purchase_date）。

## 2. 后端接口（`/api/user/purchase/...`）

沿用 APIView + `current_user_id` + `make_response` 模式；新增 `PurchaseRecordSerializer`（code from lottery.code，fields id/code/issue/numbers/bet_count/purchase_date/created_at）。

### 2.1 `PurchaseCreateView` `POST /api/user/purchase/create`
- body `{code, issue, numbers, bet_count?, purchase_date?}`。
- 未登录 → `code=1`。
- `lottery = _get_active_lottery(code)`，None → `code=1`。
- `issue` strip 后为空 → `code=1, msg="请填写期号"`。
- `validate_numbers(lottery.rule_config, numbers)` 有错 → `code=1`。
- `bet_count`：int 化，<1 取 1。
- `purchase_date`：取 body，缺省用今天（`timezone.now().date()`）；非法日期 → `code=1`。
- 落库，返回 `PurchaseRecordSerializer(rec).data`。

### 2.2 `PurchaseListView` `GET /api/user/purchase/list?code=`
- 未登录 → `code=1`。
- `filter(user_id=uid)`，有 code 再 `filter(lottery__code=code)`。
- 返回 `PurchaseRecordSerializer(qs, many=True).data`（按 model ordering）。

### 2.3 `PurchaseDeleteView` `DELETE /api/user/purchase/<id>`
- 未登录 → `code=1`。
- `filter(id=pk, user_id=uid).first()`，None → `code=1`。
- delete，返回 `{deleted: True}`。

路由注册 `usernumber/urls.py`：`purchase/create`、`purchase/list`、`purchase/<int:pk>`（delete 放最后）。

## 3. 前端

### 3.1 入口
`utils/menu.js` `HOME_MENU` 加 `{ key:'purchase', title:'购买记录', icon:'🛒', path:'/pages/purchase/index', nav:'navigateTo' }`。

### 3.2 列表页 `pages/purchase/index.vue`
- `TopBanner :back` + `LotteryTabs`（彩种切换，复用 lotteryStore.code）。
- 列表：每条显示 期号、号码球（复用 Ball）、注数、购买日期。
- 顶部「新增」按钮 → `navigateTo pages/purchase/create`。
- 单条「删除」→ `showModal` 确认（note 24）→ `purchaseDelete(id)` → reload。
- 空态提示。

### 3.3 新增页 `pages/purchase/create.vue`
- 选彩种（默认 lotteryStore.code）。
- 手选号码：复用 `getZones` + `BallSelectable` + `picker.js`（`toggleBall`/`selectionComplete`/digit 工具），仅手选、不做机选。与 picker 的手选各自独立实现（复用底层工具，不合并组件）。
- 输入：期号（必填）、注数（默认 1）、购买日期（默认今天，`input type` 或日期选择）。
- 保存 → `purchaseCreate({code, issue, numbers, bet_count, purchase_date})` → 成功 toast + `navigateBack`。

### 3.4 从「我的号码」一键转入
- `mine/index.vue` 每条记录（非 manageMode）ops 加「标为已购」。
- 点击 → `showModal`（可分两步：先填期号，再用默认注数 1 + 今天日期；为简化用单个 editable modal 填期号，注数默认 1、日期默认今天）→ `purchaseCreate`（numbers 取该记录 numbers，code 取当前彩种）→ 成功 toast。

### 3.5 api（`api/user.js`）
- `purchaseCreate(payload)` → POST `/api/user/purchase/create`
- `purchaseList(code)` → GET `/api/user/purchase/list`（带 code）
- `purchaseDelete(id)` → DELETE `/api/user/purchase/<id>`

## 4. 错误处理
- 未登录/号码非法/issue 空/日期非法 → `code=1` 提示。
- 删除只删本人记录。
- 一键转入若号码不完整（理论上我的号码已校验过）→ 后端 validate 兜底 code=1。

## 5. 测试
- 后端 pytest（`usernumber/tests/test_purchase.py`，照 test_number_list_delete 模式 auth_client + _make_record）：
  - create 正常落库（含 issue/bet_count/purchase_date）；issue 空 → code=1；号码非法 → code=1；bet_count 缺省=1；purchase_date 缺省=今天。
  - list 只返回本人、按彩种过滤。
  - delete 本人成功、他人 code=1。
- 前端 vitest（并入 user.test.js）：purchaseCreate/purchaseList/purchaseDelete 命中端点/参数。
- 不删既有测试。

## 6. 里程碑定位
note.txt 第 23 项（里程碑 3 收官）。之后里程碑：通知体系(19/17/18) → 微信登录(14) → 开奖海报(22)。
