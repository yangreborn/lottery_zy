# 里程碑2 首页/导航重排 设计（note 28 + 32 + 30）

**目标：** 重排信息架构 —— 反馈/购买/我的号码收进「我的」hub；通知活动从玩法说明拆出独立成项；彩种 Tab 缩写长名 + 不热门彩种下拉收纳。

## 背景

- **note 28：** 首页同时铺了「我的号码 / 我要反馈 / 购买记录」等卡片，与底部 tabBar「我的」职责重叠且首页过满。要把这三项收进「我的」，首页不再展示。
- **note 32：** `guide/index` 把「玩法说明 / 奖级规则 / 活动 / 通知」用类型 Tab 混在一页，很乱。前端要把「通知活动」独立成一个入口/页面，后端模型仍共用一张表（只加过滤能力）。
- **note 30：** `LotteryTabs` 横排所有彩种，「超级大乐透」名字过长导致换行。要缩写显示，并在最右加「更多」下拉，收纳后续新增的不热门彩种。

## 方案

### 一、后端：guide 列表支持多类型过滤

`GuideListView` 现仅 `type=单值` 过滤。改为支持逗号分隔多类型（向后兼容单值）：

```python
gtype = request.query_params.get("type")
if gtype:
    types = [t for t in gtype.split(",") if t]
    if types:
        qs = qs.filter(type__in=types)
```

前端「玩法说明」页用 `type=intro,rule`，「通知活动」页用 `type=activity,notice`。模型/表不拆（符合 note 32「后端可以放一起」）。

### 二、彩种 Tab：缩写 + 下拉（note 30）

新增 `src/utils/lottery.js`：

```js
export const SHORT_NAMES = { dlt: '大乐透' }            // 超级大乐透 → 大乐透
export const HOT_CODES = ['ssq', 'dlt', '3d', 'pl3', 'kl8']  // 作为常驻 Tab 的热门彩种

export function shortLotteryName(item) {
  return (item && (SHORT_NAMES[item.code] || item.name)) || ''
}

export function splitTabs(list, hotCodes = HOT_CODES) {
  const visible = (list || []).filter((x) => hotCodes.includes(x.code))
  const overflow = (list || []).filter((x) => !hotCodes.includes(x.code))
  return { visible, overflow }
}
```

`LotteryTabs.vue`：用 `shortLotteryName` 显示名；`splitTabs` 拆成常驻 Tab + 溢出项。溢出非空时最右渲染「更多 ▾」按钮，点开下拉面板列出溢出彩种；选中 emit `change` 并收起。当前选中项落在溢出区时，「更多」按钮高亮。当前 5 个彩种均为热门 → 溢出为空 → 不渲染「更多」（缩写后不再换行）；将来新增的不热门彩种自动进下拉。

设计取舍：用「白名单 HOT_CODES」而非「最多显示 N 个」，避免现有热门彩种被挤进下拉；下拉仅为未来扩展服务，当前对用户无变化（除大乐透缩写）。

### 三、「我的」hub（note 28）

- `pages/mine/index.vue` 重写为 hub 页「我的」：顶部登录状态条（匿名/已微信登录 + 微信登录/退出，原在号码页的登录逻辑迁来），下方三个入口：
  - ⭐ 我的号码 → `/pages/mine/numbers`
  - 🛒 购买记录 → `/pages/purchase/index`
  - 💬 我要反馈 → `/pages/feedback/index`
- 现「我的号码」列表整体迁到新页 `pages/mine/numbers.vue`（除去登录条，其余 LotteryTabs + 管理/批量/归组/比对/标为已购/删除逻辑原样保留）。
- tabBar「我的」仍指向 `pages/mine/index`（现为 hub）。

### 四、首页与通知入口（note 28 + 32）

- `HOME_MENU` 移除 `mine`/`feedback`/`purchase` 三项，新增 `notice`（通知活动）。结果 7 项：当期中奖、往期开奖、号码统计、选号、玩法说明、通知活动、开奖海报。
- 新页 `pages/notice/index.vue`：通知活动列表，LotteryTabs + 类型 Tab（全部=`activity,notice` / 活动 / 通知），调用 `getGuideList(code, type)`。
- `guide/index.vue`：类型 Tab 收窄为玩法相关（全部=`intro,rule` / 玩法说明 / 奖级规则），默认 `intro,rule`。
- `home/index.vue`：`goNotices` 跳转目标由 `/pages/guide/index` 改为 `/pages/notice/index`（通知现归通知页）。NoticeBar 仍用 `getNotices`（important=1）。
- `pages.json`：新增 `pages/mine/numbers`、`pages/notice/index`；`pages/guide/index` 标题「玩法介绍」改「玩法说明」。

## 文件

**后端**
- 修改：`guide/views.py`（`GuideListView` 多类型过滤）
- 测试：`guide/tests/test_api_guide.py`

**前端**
- 新增：`src/utils/lottery.js`、`src/pages/mine/numbers.vue`、`src/pages/notice/index.vue`
- 修改：`src/components/LotteryTabs.vue`、`src/utils/menu.js`、`src/pages/mine/index.vue`（改 hub）、`src/pages/guide/index.vue`、`src/pages/home/index.vue`、`src/pages.json`
- 测试：`tests/lottery.test.js`（新）、`tests/menu.test.js`（更新）

## 测试

- 后端 `test_api_guide`：`type=intro,rule` 只返回 intro+rule；`type=activity,notice` 只返回这两类；单值 `type=notice` 仍正常（向后兼容）。
- `lottery.test.js`：`shortLotteryName` 把 dlt 显示为「大乐透」、其它返回原名；`splitTabs` 按 HOT_CODES 正确切分 visible/overflow，未知彩种进 overflow。
- `menu.test.js`：HOME_MENU 长度 7、含 `notice`(navigateTo)、不含 `mine`/`feedback`/`purchase`，`guide.title` 为「玩法说明」。
- LotteryTabs 下拉为组件交互，逻辑已下沉到 `splitTabs`（单测覆盖），组件本身不做单测。
