# 小程序导航/通知/昵称交互 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development / executing-plans. Checkbox steps.

**Goal:** 返回键统一(36)、通知去彩种(37)、昵称点名称设置(38)。

**Architecture:** 全局隐藏原生栏 + TopBanner 统一头；notice 去 LotteryTabs；hub 昵称并入头部。

**Tech Stack:** uni-app Vue3 + vitest（回归）。

## Global Constraints

- `navigationStyle: custom` 全局；TopBanner/home banner 加 `var(--status-bar-height, 0px)` 顶部内边距。
- 二级页 :back="true"；tab 页(stats/picker/mine/home)无返回。
- notice 不带 code 拉取；类型 Tab 保留。
- 中文。

---

### Task 1: 返回键统一(note36)

**Files:** pages.json、components/TopBanner.vue、pages/home/index.vue、draw/latest.vue、draw/history.vue、draw/detail.vue、guide/index.vue、guide/detail.vue、draw/stats.vue、mine/picker.vue

- [ ] **Step 1:** `pages.json` `globalStyle` 增 `"navigationStyle": "custom"`。
- [ ] **Step 2:** `TopBanner.vue` `.top-banner` 的 `padding: 28rpx 0;` 改 `padding: calc(28rpx + var(--status-bar-height, 0px)) 0 28rpx;`。
- [ ] **Step 3:** `home/index.vue` `.banner` 的 `padding: 44rpx 0;` 改 `padding: calc(44rpx + var(--status-bar-height, 0px)) 0 44rpx;`。
- [ ] **Step 4:** 补 `:back="true"`：latest/history/guide/index/draw/detail/guide/detail 的 `<TopBanner title="…" />` → `<TopBanner title="…" :back="true" />`。
- [ ] **Step 5:** 去 tab 返回：stats、picker 的 `<TopBanner title="…" :back="true" />` → 去掉 `:back="true"`。
- [ ] **Step 6:** `npm test` 全绿；提交 `feat(nav): 隐藏原生栏统一 TopBanner 返回键(note36)`。

### Task 2: 通知去彩种(note37)

**Files:** pages/notice/index.vue

- [ ] **Step 1:** 移除模板 `<LotteryTabs .../>`。
- [ ] **Step 2:** 脚本删除 LotteryTabs/lotteryStore/setCode/getLotteryList 相关：`store`/`lotteries`/`onChange`/onShow 里拉彩种逻辑；`load()` 改 `getGuideList('', curType.value)`；onShow 只 `reportAccess` + `load()`。
- [ ] **Step 3:** `npm test` 全绿；提交 `feat(notice): 通知活动不分彩种统一展示(note37)`。

### Task 3: 昵称点名称(note38)

**Files:** pages/mine/index.vue

- [ ] **Step 1:** 模板：删除 `.profile` 行；authbar 左侧 `<text class="astate">…` 换成可点昵称：

```html
    <view class="authbar">
      <text class="uname" @click="editNickname">{{ nickname || '点击设置昵称' }}</text>
      <text class="abtn" @click="auth.isWechat ? doLogout() : doWechatLogin()">{{ auth.isWechat ? '退出' : '微信登录' }}</text>
    </view>
```

- [ ] **Step 2:** 样式：`.astate` 改/补 `.uname { font-size: 32rpx; color: #333; font-weight: 600; }`；删 `.profile/.plabel/.pval` 样式。其余脚本(nickname/editNickname/loadProfile)不变。
- [ ] **Step 3:** `npm test` 全绿；提交 `feat(user): 昵称改为点头部名称设置(note38)`。

---

## Self-Review

- 36→Task1(全局栏+返回归位)；37→Task2(去彩种)；38→Task3(点名称)。
- 无 placeholder；纯前端，靠回归 + 手测。
