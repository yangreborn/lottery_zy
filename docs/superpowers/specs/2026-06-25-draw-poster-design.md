# 开奖海报 · 设计文档

- 日期：2026-06-25
- 定位：里程碑 6（末个）。对应 note.txt 第 22 项。
- 纯前端 canvas，无后端改动。

---

## 0. 范围

**本期做**：开奖海报页 —— 选彩种 + 从往期选一期 + 选配色主题（红/金/蓝）→ canvas 绘制开奖海报 → 保存到相册。
**不做**：不接后端（复用现有 getHistory/getDetail）；不做自定义文案/图片上传；不做分享转发卡片（用户自行从相册分享）；海报不含购彩诱导（免费定位）。

## 1. 页面 `pages/poster/index.vue`

- 顶部 `LotteryTabs`（复用 lotteryStore.code）选彩种。
- 期次选择：`getHistory(code)` 列出期次（期号 + 开奖日期）；用户点选一期 → `getDetail(code, issue)` 取该期 → `buildPosterData` → 触发 canvas 重绘。
- 配色主题：3 个 chip（红色喜庆/金色尊贵/蓝色简约），点选切 `theme` → 重绘。
- canvas：竖版 600×840px（canvas-id="poster"），`drawPoster(ctx, data, theme)` 绘制。
- 「保存到相册」按钮：`uni.canvasToTempFilePath({canvasId:'poster'})` → `uni.saveImageToPhotosAlbum({filePath})`。

## 2. 可测纯逻辑 `utils/poster.js`

### 2.1 `POSTER_THEMES`
数组，3 个主题对象，每个含绘制所需字段：`key`、`label`、`bg`（背景色）、`titleColor`（标题/号码区主色）、`subColor`（次要文字色）。
- `{ key:'red', label:'红色喜庆', bg:'#e53935', titleColor:'#ffffff', subColor:'#ffd9d4' }`
- `{ key:'gold', label:'金色尊贵', bg:'#2e2a1f', titleColor:'#f5c518', subColor:'#c8a85a' }`
- `{ key:'blue', label:'蓝色简约', bg:'#1e88e5', titleColor:'#ffffff', subColor:'#cfe3ff' }`

### 2.2 `buildPosterData(detail, lotteryName, category)`
→ `{ name, issue, date, zones, source }`：
- `name = lotteryName`；`issue = detail.issue`；`date = detail.draw_date`。
- `zones = Object.entries(detail.numbers).map(([key, nums]) => ({ key, nums }))`（保持 numbers 顺序，号码球分区）。
- `source = category === '体彩' ? '数据来源：中国体彩网 sporttery.cn' : '数据来源：中国福彩网 cwl.gov.cn'`（默认福彩）。

### 2.3 `drawPoster(ctx, data, theme)`（canvas 绘制，靠 build+目测）
- 填充 `theme.bg` 背景。
- 顶部居中标题 `data.name`（theme.titleColor，大字）。
- 副标题 `第 {issue} 期 · {date}`（theme.subColor）。
- 号码球：按 `data.zones` 顺序逐球画圆 + 数字；球填色用 `format.js` 的 `ballColor(zone)`（red/blue/main/digits 各色），数字白色，digit 区按位补 1 位、其余补 2 位。
- 底部 `data.source` 小字（theme.subColor，居中）。

## 3. 入口

`utils/menu.js` `HOME_MENU` 加 `{ key:'poster', title:'开奖海报', icon:'🖼️', path:'/pages/poster/index', nav:'navigateTo' }`。

## 4. 错误处理 / 平台限制

- 未选期 → 不绘制，页面提示「请先选择期次」。
- `getHistory`/`getDetail` 失败 → toast。
- `saveImageToPhotosAlbum` 授权拒绝 → toast「请在设置中开启相册权限」。
- H5 端无相册 API（saveImageToPhotosAlbum 不可用）→ toast「请在微信小程序中保存」。

## 5. 测试

- 前端 vitest（`tests/poster.test.js`）：
  - `buildPosterData`：福彩 source = 中国福彩网、体彩 source = 中国体彩网；zones 由 numbers 正确展开（如 `{red:[1,2],blue:[7]}` → 2 个 zone）；name/issue/date 透传。
  - `POSTER_THEMES`：长度 3，每个含 key/label/bg/titleColor/subColor 且非空。
- 前端 vitest（`tests/menu.test.js`）：`HOME_MENU` 加 poster 后 length 断言 + `byKey.poster.nav==='navigateTo'`。
- canvas 绘制（drawPoster）+ 保存：靠 `npm run build:h5` 通过 + 人工目测。
- 不删既有测试。

## 6. 里程碑定位

note.txt 第 22 项（末个里程碑）。完成后 note 1-25 除 10（预览构建，用户暂缓）外全部完成。
