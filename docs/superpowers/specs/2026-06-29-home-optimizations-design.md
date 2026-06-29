# 首页优化设计(协议弹窗 / 数据来源 / 当期中奖上首页)

> 三条独立的前端优化,均在 `lottery_frontend`,**后端无改动**。

## 背景

来自用户的功能优化清单:

1. 用户协议、隐私协议应弹出小窗口,而不是整页跳转。
2. 首页底部的 `cwl.gov.cn` / `sporttery.cn` 前面要加「数据来源」说明。
3. 当期中奖应直接展示在首页(无需点进二级页),并把九宫格选项列在中奖信息下方。

## 决策(已与用户确认)

- 首页顶部当期中奖卡片**带彩种切换标签**(双色球/大乐透/福彩3D/排列3/快乐8)。
- 当期中奖上首页后,九宫格里原「当期中奖」入口**移除**(剩 7 项)。

## 设计

### ① 协议弹窗

- 新建 `src/components/LegalPopup.vue`:半透明遮罩 + 居中白卡,卡内含标题、`scroll-view` 滚动段落、底部关闭按钮。
  - props:`visible`(Boolean)、`type`('agreement' | 'privacy')。
  - emit:`close`。
  - 内容取自 `src/utils/legal.js` 的 `getLegalDoc(type)`,**文案不改**。
  - 跨端:仅用基础 `view` / `scroll-view` 实现,H5 与小程序通用,不引三方组件。
- `src/pages/home/index.vue`:`openDoc(type)` 改为打开弹窗(设 `popupVisible=true`、`popupType=type`),不再 `uni.navigateTo`。
- `src/pages/legal/doc.vue` 整页**保留**(深链/兜底),首页不再跳它。

### ② 数据来源前缀

- `src/pages/home/index.vue` footer:`cwl.gov.cn · sporttery.cn` → `数据来源：cwl.gov.cn · sporttery.cn`。全项目仅此一处裸域名(协议正文里的「中国福彩网(cwl.gov.cn)」不动)。

### ③ 当期中奖上首页

- 新建 `src/components/DrawCard.vue`:接 `draw` prop,渲染整张开奖卡——期号+日期、号码球(`Ball`)、奖池(`hasPool`/`formatAmount`)、奖级表(`PrizeGrades`)。无 `draw` 时由父组件控制占位。
- `src/pages/draw/latest.vue`:重构为复用 `DrawCard`(DRY),行为不变(仍 `getLatest` / `LotteryTabs`)。
- `src/pages/home/index.vue` 顶部(banner 与九宫格之间)新增:`LotteryTabs`(彩种切换)+ `DrawCard` + 加载逻辑(`onMounted` 拉 `getLotteryList`、`onShow` 拉 `getLatest(store.code)`、切换 `setCode` 后重载)。
- `src/utils/menu.js`:`HOME_MENU` 移除 `latest` 项 → 7 项(往期开奖/号码统计/选号/玩法说明/通知/开奖海报/走势图)。

## 测试 / 验收

- `src/utils/__tests__/menu.test.js`(或现有 menu 测试):断言 `HOME_MENU` 长度 8 → **7**,且不含 key 为 `latest` 的项。
- `latest.vue` 重构后渲染行为不变(同样的号码球与奖级表)。
- 收尾:`npm run test`、`npm run build:h5`、`npm run build:mp-weixin` 全部通过。

## 非目标

- 不改协议/隐私文案内容。
- 不改后端、API、数据来源逻辑。
- 不删除 `legal/doc.vue` 与 `draw/latest.vue` 页面(仅移除首页对前者的跳转、九宫格对后者的入口)。
