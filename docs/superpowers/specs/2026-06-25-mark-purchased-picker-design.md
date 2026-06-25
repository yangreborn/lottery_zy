# 里程碑D 标为已购改选择列表 设计（note 41）

**目标：** 「我的号码」把一注标为已购时，期号不再手动输入，改为从该彩种近期期次中选择。纯前端。

## 现状

`mine/numbers.vue` 的 `doMarkPurchased(rec)` 用 `uni.showModal({editable:true})` 让用户手输期号，易错。

## 方案

- 进入页面/切彩种时拉取该彩种近期开奖列表 `getHistory(store.code, {page:1})` 存入 `issues` ref（results[].issue / draw_date）。
- 「标为已购」用原生 `<picker mode="selector">` 包裹，range 为期次标签（`${issue}期 ${draw_date}`），用户选中后用所选期号调 `purchaseCreate`（沿用 numbers/date 逻辑：numbers=rec.numbers, bet_count=1, purchase_date=todayStr()）。
- 期次列表为空时点选给「暂无可选期次」提示。
- 删除原手输期号的 showModal 流程。

picker 原生组件可滚动、支持任意条数，优于 actionSheet（条数受限）。

## 文件

- 修改：`src/pages/mine/numbers.vue`（issues 加载 + picker 标为已购，替换 doMarkPurchased）

## 测试

- 期次标签构建抽成纯函数 `issueLabel(item)`（util 或页面内），便于单测；选择→购买为组件接线靠回归+手测。
- 全量前端测试通过。
