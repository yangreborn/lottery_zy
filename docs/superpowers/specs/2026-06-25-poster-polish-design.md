# 里程碑1 开奖海报优化 设计（note 26 + 27）

**目标：** 修复海报「只显示一部分」的截断问题，并把海报样式做得更美观。纯前端 canvas，无后端改动。

## 背景问题

- **note 26 截断：** `<canvas>` 元素 CSS 尺寸用 rpx（`600rpx × 840rpx`），在 375px 宽机型上真实绘图区只有约 `300px × 420px`；而 `drawPoster` 用固定的 `600 × 840` px 坐标系绘制，右半 / 下半超出画布边界 → 用户只看到左上一部分。
- **note 27 样式简单：** 纯色背景 + 一排号码球 + 单行来源文字，缺少层次、分区标签和装饰，观感单薄。

## 方案

### 一、截断修复（坐标缩放）

保持 `600 × 840` 这套「设计坐标系」不变，让绘制逻辑继续用整洁的整数坐标。页面在绘制前用 `uni.upx2px(600)` 求出画布真实 px 宽度，计算 `scale = realPx / 600`，调用时把 scale 传入 `drawPoster`，函数开头执行 `ctx.scale(scale, scale)`，之后所有绘制坐标沿用 600×840 设计系，自动铺满真实画布。

因为画布等比（600rpx × 840rpx），`upx2px` 是线性换算，x/y 缩放因子相同，单个 scale 即可。

导出时 `canvasToTempFilePath` 传 `width/height`（真实 px）与 `destWidth/destHeight`（设计尺寸的 2 倍）得到高清图。

**为什么不直接把画布尺寸改成 px：** rpx 会随机型宽度自适应，改成固定 px 会在大屏留白、小屏溢出；scale 方案一处适配全部机型，且不污染绘制逻辑。

### 二、样式美化（重绘 `drawPoster`）

- **主题扩展：** 每个主题新增 `bg2`（渐变末端色）、`card`（号码卡片底色）、`accent`（强调色）。仍 3 套：红色喜庆 / 金色尊贵 / 蓝色简约。
- **背景：** 垂直线性渐变 `bg → bg2`（`ctx.createLinearGradient`）。
- **顶部：** 彩种名（大号粗体）+ 小标签「开奖公告」；其下期号·日期做成圆角胶囊条。
- **号码区：** 一张圆角卡片（`card` 色），按 zone 分行；每行左侧显示区名（红球 / 蓝球 / 前区 / 后区 / 号码，取自 `rule_config.zones[].label`），右侧号码球带渐变填充 + 轻微阴影 + 白色粗体数字。沿用已修复的 `perRow` 自动换行（快乐8 20 球不溢出）。
- **球颜色：** 优先用 `zone.color`（rule_config 内已有），回退 `ballColor(key)`。
- **底部：** 数据来源只显示网址（`cwl.gov.cn` 或 `sporttery.cn`，福彩 / 体彩区分），按 note 31 方向不加「数据来源：」前缀文字；再加一行品牌小字「彩票工具」。

## 接口变更

- `POSTER_THEMES`：每项增加 `bg2` / `card` / `accent` 字段。
- `buildPosterData(detail, lottery)`：签名由 `(detail, lotteryName, category)` 改为接收整个 lottery 对象（含 `name` / `category` / `rule_config.zones`）。输出：
  ```js
  { name, issue, date, zones: [{ key, label, color, nums }], source }
  ```
  - `zones` 的 `label` / `color` 来自 `rule_config.zones`（按 key 匹配），匹配不到时 `label` 回退为 key、`color` 回退 `ballColor(key)`。
  - `source` 只含网址：体彩 → `sporttery.cn`，其它 → `cwl.gov.cn`（不含「数据来源」字样）。
- `drawPoster(ctx, data, theme, scale)`：新增 `scale` 参数，开头 `ctx.scale(scale, scale)`。

## 文件

- 修改：`lottery_frontend/src/utils/poster.js`（主题、buildPosterData、drawPoster）
- 修改：`lottery_frontend/src/pages/poster/index.vue`（计算 scale、传 lottery 对象、高清导出）
- 修改：`lottery_frontend/tests/poster.test.js`（更新 buildPosterData 用例）

## 测试

- `buildPosterData`：传入含 `rule_config.zones` 的 lottery 对象，断言
  - `zones` 每项带 `label` / `color`（来自 rule_config，dlt 为「前区/后区」）；
  - rule_config 缺该 zone 时 label 回退 key、color 回退 ballColor；
  - 体彩 `source` 含 `sporttery.cn`、福彩 `source` 含 `cwl.gov.cn`，且都不含「数据来源」字样。
- `POSTER_THEMES`：仍 3 套，且每项含 `bg2` / `card` / `accent`。
- `drawPoster` 涉及 canvas，不做单元测试。
