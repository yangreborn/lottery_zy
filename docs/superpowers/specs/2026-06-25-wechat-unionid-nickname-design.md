# 里程碑F 微信 unionid/昵称/授权 设计（note 44）

**目标：** 微信登录时除 openid 外尽量拿 unionid 落库；通过授权弹窗获取微信昵称写入档案。

## 背景

note 44：openid 已记录；想要 unionid（开放平台账号绑定后微信才返回）与微信昵称；获取昵称需弹用户授权。

约束说明：
- unionid 只有小程序绑定了**微信开放平台**账号时 code2session 才返回；未绑定则为空——代码"有就存"。
- 微信已收紧用户信息，昵称用 `uni.getUserProfile`（弹授权框）获取；非微信环境(H5)拿不到则跳过。

## 方案

### 后端

- `AppUser` 增字段 `unionid`（CharField max_length=128, blank, default="", db_index=True，非唯一——可为空且多用户可空）。迁移 0006。
- `common/auth.py` 新增 `wechat_code_to_session(code)` → 返回 `{"openid":..., "unionid":...}` 或 None（真实 code2session，unionid 缺省空串）。保留原 `wechat_code_to_openid`（mock selector `code_to_openid` 仍用，保持 provider 实现分开）。
- `WechatLoginView` 改用 `wechat_code_to_session`：拿到 openid 后 `set_user_session` + `get_or_create_app_user(uid, openid)`；若返回 unionid 且与档案不同则更新落库。昵称由前端登录后调既有 `POST /api/user/profile` 写入（不另开接口）。
- admin `AppUserAdmin` list_display 增 `unionid`。

### 前端

- `mine/index.vue` `doWechatLogin`：在用户点击手势内先 `uni.getUserProfile({desc})` 弹授权拿 `nickName`（失败则置空继续）；再 `uni.login` 拿 code → `wechatLogin(code)` → `setToken` → 若有 `nickName` 调 `setProfile(nickName)` → `loadProfile`。

## 文件

**后端**：`usernumber/models.py`(unionid)、`migrations/0006_*`、`common/auth.py`(wechat_code_to_session)、`usernumber/views.py`(WechatLoginView)、`usernumber/admin.py`(unionid 列)
**前端**：`src/pages/mine/index.vue`(doWechatLogin)

## 测试

- `common/auth`：`wechat_code_to_session` 解析 openid+unionid（monkeypatch urlopen 返回含 unionid 的 json；无 unionid 时为空串；请求失败/无 openid 返回 None）。
- `WechatLoginView`：登录落 unionid（monkeypatch wechat_code_to_session 返回带 unionid）；无 unionid 时 unionid 为空；保留未配置/失败/缺 code 分支。
- 迁移 0006 仅加字段。
- 前端 doWechatLogin 为 uni API 接线，靠手测（getUserProfile 需真机微信）。
