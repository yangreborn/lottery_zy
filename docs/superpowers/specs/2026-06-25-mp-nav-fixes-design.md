# 里程碑A 小程序导航/通知/昵称交互 设计（note 36 + 37 + 38）

**目标：** 统一返回键（一个页一个）、通知活动去彩种统一展示、昵称改为点头部名称设置。纯前端。

## note 36 返回键统一（保留 TopBanner，隐藏原生栏）

现状：每个二级页同时有系统原生导航栏（红底带返回）+ 页面内自定义 TopBanner（红底，部分开了返回）。导致：当期/往期 TopBanner 没开返回（用户只见原生栏当背景，感觉"没有返回"）；通知页 TopBanner 开了返回 → 原生 + 自定义两个返回。

方案：
1. `pages.json` `globalStyle` 加 `"navigationStyle": "custom"`，全局隐藏原生导航栏；统一由 TopBanner 提供标题与返回。
2. `TopBanner.vue` 顶部加状态栏高度内边距 `var(--status-bar-height, 0px)`（mp 有刘海安全区，H5 为 0），避免内容顶到状态栏。`home/index.vue` 的 `.banner` 同样加。
3. 二级页（navigateTo）统一 `:back="true"`：当期 latest、往期 history、玩法说明 guide/index、开奖详情 draw/detail、玩法详情 guide/detail（其余 notice/poster/numbers/purchase*/feedback/legal 已是 true）。
4. tab 页（switchTab）统一无返回：stats、picker 去掉 `:back`（mine/index、home 已无）。

## note 37 通知活动去彩种

`notice/index.vue` 移除 `LotteryTabs` 与彩种相关逻辑（store/setCode/getLotteryList/onChange），`getGuideList('', curType)` 不带 code → 后端返回全部彩种的活动/通知，统一展示。类型 Tab（全部/活动/通知）保留。

## note 38 昵称改为点名称设置

`mine/index.vue` 去掉单独的「昵称」行；把昵称显示在头部作为可点名称：authbar 左侧显示昵称（无则「点击设置昵称」），点击即弹窗编辑（复用现有 `editNickname`）；右侧仍是登录状态/按钮。`getProfile`/`setProfile`/`loadProfile` 逻辑保留。

## 文件

- 修改：`src/pages.json`（globalStyle navigationStyle custom）
- 修改：`src/components/TopBanner.vue`（状态栏内边距）
- 修改：`src/pages/home/index.vue`（banner 状态栏内边距）
- 修改：`src/pages/draw/latest.vue`、`draw/history.vue`、`draw/detail.vue`、`guide/index.vue`、`guide/detail.vue`（补 :back="true"）
- 修改：`src/pages/draw/stats.vue`、`mine/picker.vue`（去 :back）
- 修改：`src/pages/notice/index.vue`（去彩种）
- 修改：`src/pages/mine/index.vue`（昵称点名称）

## 测试

- 均为模板/样式/接线，无新增可单测逻辑；全量前端测试保持通过（无回归）+ 手测：每个二级页只有一个返回、tab 页无返回、通知不分彩种、点昵称可编辑。
- notice 去彩种后 `getGuideList` 仍走既有 api（已有单测覆盖 api 形态）。
