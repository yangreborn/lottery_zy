# E · UI/导航改版 · 设计文档

- 日期：2026-06-23
- 定位：把 H5/小程序前端从"直接 tabBar 进当期页"改成"**菜单选项首页**"，并整体加暖色渐变底色、放大关键字号。对应 note.txt 第 5/9/12 项。
- 前置：M1–M4b 全部已合并 master；前端基座（各页/组件/store/api）已就绪。纯前端改动，不动后端。

---

## 0. 范围

**本期做**：① 新增菜单选项首页（6 卡片网格）作为入口；② tabBar 重构为 首页/统计/选号/我的；③ 全局暖色渐变底色（G4）；④ 关键字号放大约 15%。
**不做**：新增彩种（A）、选号器改造（B）、统计筛选（D）、记录分组（C）——后续里程碑；后端不动。

## 1. 菜单选项首页（新 pages/home/index.vue）

- 顶部**渐变红横幅**："彩票查询"，背景 `linear-gradient(180deg, #e53935 0%, #ff6f61 100%)`，白色大标题。
- 下方 **2 列卡片网格**，6 张：
  | 卡片 | 图标 | 跳转 |
  |---|---|---|
  | 当期中奖 | 🎯 | navigateTo `pages/draw/latest` |
  | 往期开奖 | 📅 | navigateTo `pages/draw/history` |
  | 号码统计 | 📊 | switchTab `pages/draw/stats` |
  | 选号记录 | ✏️ | switchTab `pages/mine/picker` |
  | 玩法介绍 | 📖 | navigateTo `pages/guide/index` |
  | 我的号码 | ⭐ | switchTab `pages/mine/index` |
- 每张卡片：白底圆角 + 浅红阴影，大图标 + 大字标题。
- **跳转方式按目标分型**：目标是 tabBar 页（统计/选号/我的）用 `uni.switchTab`；非 tabBar 页（当期/往期/玩法）用 `uni.navigateTo`。这点是实现关键，混用会报错。
- 首页本身是 tabBar 第 1 项。

## 2. tabBar 重构（pages.json）

tabBar（uni-app 上限 5，本期 4 项）：**首页 / 统计 / 选号 / 我的**
- `pages/home/index`（首页）、`pages/draw/stats`（统计）、`pages/mine/picker`（选号）、`pages/mine/index`（我的）。
- 当期/历史/玩法/详情仍是注册页，但**不在 tabBar**，从首页卡片或页内进。
- pages 列表新增 `pages/home/index`，且置于数组首位（小程序默认首页 = pages 第一项）。
- 备注：核心「当期中奖」不在 tabBar、在首页卡片（一点即达）。若后续想把当期放回 tabBar 替掉选号，改 pages.json 即可。

## 3. 暖色渐变底色（G4）

- **全局**：`pages.json globalStyle.backgroundColor` 由 `#f5f5f5` 改为浅红 **`#fff0ee`**（小程序/H5 的 globalStyle 只能纯色，作全局兜底底色）。
- **首页 body**：根 view 加 G4 渐变身 `linear-gradient(180deg, #ffd9d4 0%, #fff0ee 35%, #fbfbfb 100%)`，`min-height:100vh`。
- **各页顶部横幅**：当期/历史/详情/统计/玩法/我的等页，在内容区顶部加一条渐变红 banner（`linear-gradient(180deg,#e53935,#ff6f61)` + 白字页名），与首页风格统一。
- 卡片/列表项保持白底，阴影改用浅红 `rgba(229,57,53,.10)` 以呼应主题。
- 技术说明：uni-app 中页面级渐变要写在根 view 的 `background`（H5 与 mp-weixin 均支持 CSS `linear-gradient`），不能放 globalStyle（只支持纯色）。

## 4. 字号放大（约 +15%）

集中调大关键文字（rpx）：
- 号码球 `Ball`/`BallSelectable`：28 → 32rpx。
- 页面标题/卡片标题：28 → 34rpx。
- 列表项主文字：26 → 30rpx。
- 次要说明文字（日期/标签）保持或略调（22→24rpx）。
- 不引入全局字号变量系统（YAGNI），按页/组件就地调。

## 5. 组件/页面改动清单

- 新建：`pages/home/index.vue`（菜单首页）。
- 改 `pages.json`：pages 加 home 且置首位；tabBar 改 4 项。
- 改样式（底色横幅 + 字号）：`pages/draw/{latest,history,detail,stats}.vue`、`pages/guide/{index,detail}.vue`、`pages/mine/{index,picker}.vue`、组件 `Ball.vue`/`BallSelectable.vue`。
- 可选抽一个公共 banner 组件 `TopBanner.vue`（props title），各页复用，避免重复渐变样式。

## 6. 错误处理 / 兼容

- 跳转分型错误（switchTab 跳非 tab 页 / navigateTo 跳 tab 页）会运行时报错——实现时严格按第 1 节表格区分。
- 渐变在 mp-weixin 用 `background: linear-gradient(...)`（等价 background-image），已验证支持；rpx 自适应不变。
- 不改任何接口/数据，纯展示层。

## 7. 测试

- **前端 vitest**：首页菜单配置可单测——把 6 个菜单项抽成 `utils/menu.js` 的数组（每项 {key,title,icon,path,nav:'switchTab'|'navigateTo'}），单测项数、每项 nav 类型与 path 正确（保证 switchTab/navigateTo 分型不写错）。
- **人工目测**：`npm run dev:h5`（浏览器）/ `npm run dev:mp-weixin`（开发者工具）看首页菜单、渐变底色、字号、各卡片跳转正确、tabBar 4 项。
- 既有单测不受影响（纯样式/新增页）。

## 8. 怎么看效果

`dev:h5` 或 `dev:mp-weixin` 跑起来：进入即菜单首页（渐变红横幅 + 6 卡片 + 浅红渐变身），点卡片进各功能页，底部 tabBar 首页/统计/选号/我的，整体字更大、暖色不再发白。

## 9. 里程碑定位

note.txt 第一批改造（E. UI/导航改版）。后续：B 选号器改造 → D 统计筛选 → C 记录分组 → A 新彩种 → G 体验版。
