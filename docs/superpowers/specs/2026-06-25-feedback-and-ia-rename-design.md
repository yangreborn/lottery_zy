# IA 改名 + 我要反馈 · 设计文档

- 日期：2026-06-25
- 定位：里程碑 3「记录区重构」的第一个子里程碑。对应 note.txt 第 15 项（我的号码/选号记录命名重复 + 新增「我要反馈」）。
- 后续子里程碑：25 批量删除/归组、23 购买记录（各自独立 spec）。

---

## 0. 范围

**本期做**：① 改名消除「选号记录/我的号码」混淆；② 新增「我要反馈」（后端存储 + 首页入口 + 反馈页）。
**不做**：不合并选号页与我的号码页（仅改名）；不做批量操作(25)、购买记录(23)；不做反馈的回复/审核流程。

## 1. IA 改名（note 15 前半）

根因：`src/utils/menu.js` 的 `HOME_MENU` 里 picker 页标题叫「选号记录」，但该页（`pages/mine/picker.vue`）是选号生成器、不是记录；真正的记录是「我的号码」（`pages/mine/index.vue`）。两个名字让用户以为有两个记录页。

改动：`HOME_MENU` 中 picker 项 `title: '选号记录'` → `'选号'`（与 tabBar 现有「选号」一致）。「我的号码」(mine) 项不动。纯文案改动，无逻辑变化。

## 2. 我要反馈 · 后端（note 15 后半）

放 `usernumber` app（归属"用户提交"，避免新建 app 脚手架）。

### 2.1 Feedback 模型（`usernumber/models.py`）
沿用现有 model 风格（中文 verbose_name、`-created_at` 排序）：
- `user_id`：CharField(max_length=64, blank=True, default="", db_index=True) — 用户 hash，匿名时空串。
- `content`：TextField — 反馈内容。
- `contact`：CharField(max_length=100, blank=True, default="") — 可选联系方式。
- `created_at`：DateTimeField(auto_now_add=True)。
- Meta：verbose_name「用户反馈」，ordering `["-created_at"]`。

### 2.2 admin（新建 `usernumber/admin.py`）
- 注册 `Feedback`：list_display = (content 摘要/contact/user_id/created_at)，便于后台查看。
- 顺带注册 `UserNumber`（当前 usernumber 无 admin.py）。

### 2.3 接口 `FeedbackCreateView`
- `POST /api/user/feedback`（注册于 `usernumber/urls.py`，路径名 `user-feedback`）。
- `authentication_classes = []`，沿用 `current_user_id(request)`。
- body：`{ content: str, contact?: str }`。
- 逻辑：
  - `uid = current_user_id(request) or ""`（匿名允许提交）。
  - `content` 去首尾空白后为空 → `make_response(code=1, msg="请填写反馈内容")`，不落库。
  - `content` 长度 > 500 → `make_response(code=1, msg="反馈内容过长")`，不落库。
  - 否则 `Feedback.objects.create(user_id=uid, content=content, contact=contact)`，返回 `make_response(data={"id": rec.id})`。
- 用 `logging`（标准库）记录异常，不用 print。

## 3. 我要反馈 · 前端

- `src/utils/menu.js` `HOME_MENU` 追加：`{ key: 'feedback', title: '我要反馈', icon: '💬', path: '/pages/feedback/index', nav: 'navigateTo' }`。
- 新页 `src/pages/feedback/index.vue`：
  - `TopBanner :title="'我要反馈'" :back="true"`。
  - `textarea` 绑定 `content`（placeholder「请写下你的意见或建议…」）。
  - `input` 绑定 `contact`（placeholder「联系方式（可选）」）。
  - 提交按钮：`content` 去空为空时禁用；点提交调 `submitFeedback`，成功 `uni.showToast('已收到，谢谢反馈')` 后 `uni.navigateBack()`，失败 `uni.showToast(e.msg)`。
- `src/api/user.js` 新增 `submitFeedback({ content, contact })` → `POST /api/user/feedback`（沿用现有 request 封装）。
- `src/pages.json` `pages` 数组注册 `{ "path": "pages/feedback/index", "style": { "navigationBarTitleText": "我要反馈" } }`。

## 4. 错误处理

- 匿名（无 uid）→ `user_id=""`，正常提交。
- content 空/超长 → `code=1` 提示，不落库。
- 网络/服务端异常 → 前端 toast 错误信息。

## 5. 测试

- 后端 pytest（`usernumber/tests/test_feedback.py`，照现有 test 模式用 Django test client）：
  - 正常提交落库（匿名 `user_id==""`，返回含 id）。
  - 空 content → code=1，不落库（count 不变）。
  - 超长 content（>500）→ code=1，不落库。
- 前端 vitest（`tests/userapi_feedback.test.js` 或并入现有 user api 测试，照现有 api 测试 mock request 的模式）：`submitFeedback` 命中 `/api/user/feedback`、透传 content/contact。
- 不删既有测试。

## 6. 里程碑定位

note.txt 第 15 项。里程碑 3 后续：25 批量删除/归组 → 23 购买记录。之后里程碑：通知体系(19/17/18) → 微信登录(14) → 开奖海报(22)。
