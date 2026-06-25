# 里程碑B 开奖详情修正 设计（note 39）

**目标：** 修正开奖详情/当期页的几处展示问题。纯前端。

## 子项

1. **空/0 奖池不显示**：福彩3D 奖池为空、排列三为 0。当期(latest)与详情(detail)的「奖池：X 元」无有效奖池时整行不显示。
2. **快乐8 档头去红**：`PrizeGrades` 快乐8 分组档头「选X（N档）」现用红色 `#e53935`，改中性色。
3. **移除分省展开**：`PrizeGrades` 一等奖后的「▼分省」可展开块整体移除（note 39：双色球一等奖不加分省文字；大乐透本无省份数据 → 统一不展示分省）。

## 方案

- `utils/format.js` 新增 `hasPool(raw)`：去逗号转数字，`Number.isFinite && > 0` 返回 true。
- `draw/detail.vue`、`draw/latest.vue`：奖池行加 `v-if="hasPool(draw.pool_amount)"`；不再向 `PrizeGrades` 传 `:area`。
- `components/PrizeGrades.vue`：
  - 删除 `area` prop、`areaText`/`open1`、`stripAreaPrefix` 引用，及模板中一等奖的 clickable/`▼分省`/area 文本块；flat 分支只渲染 label/count/amount。
  - `.ghead` 颜色 `#e53935` → `#555`（中性）。
- `utils/prize.js` 的 `stripAreaPrefix` 不再被使用，可保留(无害)或删除导出；本里程碑保留以减小面。

## 文件

- 修改：`src/utils/format.js`（hasPool）、`src/components/PrizeGrades.vue`、`src/pages/draw/detail.vue`、`src/pages/draw/latest.vue`
- 测试：`tests/format.test.js`（hasPool；若无则新增）

## 测试

- `hasPool`：'' / null / '0' / 0 → false；'1234' / 1234 / '1,234' → true。
- PrizeGrades 去分省为模板改动，无单测；prize.js 逻辑未改。
- 全量前端测试通过 + 手测：3D/排列三无奖池行；快乐8 档头非红；双色球无分省展开。
