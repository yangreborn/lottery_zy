# 里程碑6 用户体系 设计（note 34 + 35）

**目标：** 建立用户档案：注册时记录 openid，用户可设昵称；后台用短 id + 昵称区分用户（不再面对 64 位长哈希）。

## 背景

- 现状无用户模型：`openid` 经 `hash_user_id` 变成 64 位 `user_id` 后即丢弃，记录表(UserNumber/Feedback/PurchaseRecord)只存 `user_id` 字符串。
- note 34：后台只能看到很长的哈希，无法区分是不是同一用户。
- note 35：要记录用户有用信息——可设昵称，注册时记录 openid。

## 方案

### 一、AppUser 模型（usernumber/models.py）

```python
class AppUser(models.Model):
    """登录用户档案。user_id 是 openid 的 hash(对外标识)，openid 仅后台留存。"""
    user_id = models.CharField("用户哈希", max_length=64, unique=True, db_index=True)
    openid = models.CharField("openid", max_length=128, unique=True)
    nickname = models.CharField("昵称", max_length=30, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = verbose_name_plural = "用户"
        ordering = ["-created_at"]

    @property
    def short_id(self):
        return self.user_id[:8]

    def __str__(self):
        return f"#{self.id} {self.nickname or self.short_id}"
```

`id`(自增小整数)就是后台一眼可区分的短标识（解决 note 34）；`openid`、`nickname` 满足 note 35。

模块级辅助：

```python
def get_or_create_app_user(user_id, openid):
    user, _ = AppUser.objects.get_or_create(user_id=user_id, defaults={"openid": openid})
    return user
```

### 二、登录时注册（usernumber/views.py）

`LoginView` 与 `WechatLoginView` 在 `set_user_session` 后调用 `get_or_create_app_user(uid, openid)`，把 openid 落库（匿名登录的 openid 即 device code，作为稳定设备标识）。已注册用户重复登录不新建。

### 三、昵称接口 ProfileView

`GET /api/user/profile`：返回当前用户 `{nickname, short_id}`（未登录 code=1；已登录未建档返回空昵称 + uid[:8]）。
`POST /api/user/profile` `{nickname}`：设置昵称（去空格，≤30 字符，超长 code=1），返回 `{nickname, short_id}`。

均 `authentication_classes=[]`，用 `current_user_id(request)` 鉴权（session 或 X-User-Id 头）。url：`path("profile", views.ProfileView.as_view())`。

### 四、Admin 可区分（usernumber/admin.py）

- 注册 `AppUser`：`list_display=("id","nickname","short_id","openid","created_at")`，`search_fields=("nickname","user_id","openid")`，`readonly_fields=("user_id","openid","created_at","updated_at")`。
- 记录表 admin（UserNumber/Feedback/PurchaseRecord）：`list_display` 里的 `user_id` 换成 `short_uid` 方法（显示 `user_id[:8]`），完整 `user_id` 仍在 `search_fields` 可搜——一眼区分是否同一用户。

### 五、前端昵称 UI（我的 hub）

- `api/user.js`：`getProfile()` / `setProfile(nickname)`。
- `pages/mine/index.vue`：onShow 时 `ensureLogin()` 后 `getProfile()` 填充昵称；在登录条下方加「昵称」行，显示当前昵称（无则「点击设置」），点按 `uni.showModal({editable})` 输入并 `setProfile` 后刷新。

## 文件

**后端**
- 修改：`usernumber/models.py`（AppUser + 辅助）、`usernumber/views.py`（注册 + ProfileView + import settings 已具备）、`usernumber/urls.py`（profile）、`usernumber/admin.py`（AppUser + short_uid）
- 新增：`usernumber/migrations/0005_appuser.py`（makemigrations 生成）
- 测试：`usernumber/tests/test_profile.py`（新）；`test_wechat_login.py`/`test_token_auth.py` 视情况补注册断言

**前端**
- 修改：`src/api/user.js`、`src/pages/mine/index.vue`

## 测试

- 后端：
  - 登录后 AppUser 被创建，openid 落库；重复登录不重复建档。
  - `GET /profile` 未登录 code=1；已登录返回昵称/short_id。
  - `POST /profile` 设置昵称成功并返回；超长 code=1；未登录 code=1。
- 前端：api 封装单测（getProfile/setProfile 调用正确 endpoint）；hub UI 为组件接线靠手测。
- 迁移：`makemigrations` 生成 0005；`migrate --check` 应显示有待应用（迁移由用户执行）。
