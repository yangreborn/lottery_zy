# 登录用户自定义首页彩种设计

> 上一里程碑(前端 5 点)的延续:登录用户可自定义首页展示哪些彩种。涉及后端(加字段+迁移+API)与前端。

## 决策(已与用户确认)

- **仅微信登录用户**可自定义(偏好随微信号跨设备;匿名用户首页显示全部)。
- 偏好为**勾选子集**,顺序仍按固定规范顺序(不自定义排序)。
- **一个都不选 = 显示全部**(空数组即不限定)。
- 自定义只影响**首页**;统计/选号/走势等页的彩种 tab 不受影响。

## 后端

### Model
- `usernumber/models.py` `AppUser` 增加 `home_lotteries = models.JSONField("首页彩种", default=list, blank=True)`(存彩种 code 列表)。
- 新增迁移。

### API(扩展现有 `ProfileView`,`/api/user/profile`)
- `GET`:返回值增加 `home_lotteries`。
- `POST`:同时支持可选 `nickname` 与可选 `home_lotteries`——只更新请求体中出现的字段(向后兼容现有只传 nickname 的调用)。`home_lotteries` 必须是数组,过滤掉非 `is_active` 彩种 code 后存储。
- 仍要求已登录且有 `AppUser` 档案,否则 `code=1`。

## 前端

### 工具
- `src/utils/lottery.js` 新增 `filterHomeLotteries(list, codes)`:`codes` 为空/缺省 → 原样返回;否则按 `codes` 过滤(顺序仍随入参 `list`,即已排序)。

### API
- `src/api/user.js` 新增 `setHomeLotteries(codes)` → `POST /api/user/profile { home_lotteries: codes }`;`getProfile` 返回值已含 `home_lotteries`。

### 首页
- `src/pages/home/index.vue` `loadCards`:仅当 `authState.isWechat` 时 `getProfile` 取 `home_lotteries`,用 `filterHomeLotteries` 过滤彩种卡;匿名或失败则显示全部。

### 设置页
- 新建 `src/pages/mine/home_lotteries.vue`:列出全部彩种 + 勾选(预填当前偏好),底部「保存」调 `setHomeLotteries`,保存后返回。空选提示「不选=显示全部」但允许保存。
- `src/pages/mine/index.vue`:菜单加「首页彩种」入口,**仅 `auth.isWechat` 显示**。
- `src/pages.json` 注册 `pages/mine/home_lotteries`。

## 测试 / 验收

- 后端 `usernumber/tests/test_profile.py`:新增 `home_lotteries` 读写用例 + 非法 code 过滤用例 + 只传 nickname 不影响 home_lotteries(向后兼容)。
- 前端 `tests/lottery_util.test.js`:`filterHomeLotteries`(空返回全部、子集过滤、未知 code 安全)。
- 收尾:后端 `pytest`、前端 `npm run test`、`build:h5`、`build:mp-weixin` 全过。

## 非目标

- 不做自定义排序(顺序固定)。
- 匿名用户不提供自定义(显示全部)。
- 不改其它页的彩种 tab。
