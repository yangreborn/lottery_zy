# 前端 5 点优化设计(首页一列/固定顺序/机选可改/统计期数/走势图)

> 纯前端(`lottery_frontend`),**后端无改动、无迁移**。自定义彩种(需后端)不在本里程碑,留作下一里程碑。

## 背景

用户优化清单(本批取其中纯前端的 5 点):

1. 首页当期中奖不分页、显示成一列,奖级默认隐藏、点开查看。
2. 彩种按固定顺序 **ssq · dlt · 3d · kl8 · pl3** 展示(各处一致)。(「登录用户自定义彩种」需后端,下一里程碑做)
3. 机选后支持修改机选号码;改过后再点机选,提示「已手动修改过未保存,是否继续机选」。
4. 统计支持自定义期数。
5. 走势图:折线(和值/单号遗漏等)默认尺寸太小,与号码/遗漏矩阵不一致;放大缩小去掉按钮,改双指捏合缩放 + 提示。

## 设计

### 1. 首页一列多彩种 + 奖级默认折叠

- `src/components/DrawCard.vue` 增加 prop `collapsible: Boolean`(默认 `false`)。为 `true` 时奖级块默认收起,显示「展开奖级 ▾ / 收起奖级 ▲」开关,点击切换;为 `false` 时照旧直接展示奖级。
- `src/pages/home/index.vue`:去掉 `LotteryTabs` + 单 `DrawCard`,改为 `v-for` 遍历**全部彩种**(排序后),每个一张 `DrawCard :collapsible="true"`;并发为每个彩种拉 `getLatest`,存为 `{ code, name, draw }` 列表。
- `src/pages/draw/latest.vue` 保留(带切换的单彩种页,深链兜底),`DrawCard` 不传 `collapsible`(默认展开)。

### 2. 彩种固定顺序(纯前端)

- `src/utils/lottery.js`:新增 `LOTTERY_ORDER = ['ssq','dlt','3d','kl8','pl3']` 与 `sortLotteries(list)`(按 ORDER 升序,不在表内的 code 依原相对序排末尾);`HOT_CODES` 改为 `['ssq','dlt','3d','kl8','pl3']`。
- `src/api/lottery.js`:`getLotteryList()` 返回前 `sortLotteries`,所有消费方自动有序。

### 3. 机选就地改 + 再机选确认

- `src/pages/mine/picker.vue` 机选区:每注号码球可点击。点某注某球 → 记录 `editing = { i, key, j }` → 下方展示该区可选号码 → 点新号 `n` 替换 `sets[i][key][j]`:数字区(`ordered && allow_repeat`)直接替换;普通区若 `n` 已在该注该区其它位置则忽略(去重)。任一替换置 `dirty = true`。
- `doGenerate` / `reroll`:若 `dirty` 为 `true`,先 `uni.showModal({ content: '已手动修改过未保存,是否继续机选' })`,确认才重新生成并 `dirty = false`;新机选生成后 `dirty = false`。

### 4. 统计自定义期数

- `src/pages/draw/stats.vue`:快捷档(10/30/50/100)旁加 `input`(type=number),输入 1–100(越界纠正到边界、非法回落当前值)后 `load`。沿用后端 `periods` 参数(后端已 cap 1–100)。

### 5. 走势图尺寸 + 双指缩放

- `src/pages/chart/index.vue`:折线 canvas 高度由 `460` 提升到 `560`(`.chart` 样式同步),与矩阵视觉协调。
- 去掉 `.zoom` 里两个 `±` 按钮,提示语改为「双指缩放、单指左右拖动看更多期」。
- 触摸:`onTouchStart`/`onTouchMove` 支持两指——两指时按双指间距变化调整 `windowSize`(捏合→放大→窗口变小;张开→缩小→窗口变大),范围 `[WINDOW_MIN, total]`;单指时维持现有平移逻辑。`zoom(dir)` 函数移除。

## 测试 / 验收

- `tests/lottery_util.test.js`:新增 `sortLotteries` 用例(乱序输入 → ssq,dlt,3d,kl8,pl3;未知 code 排末尾);`HOT_CODES` 顺序断言(若有)。
- 其余为组件/页面交互,无单元测试,靠 `npm run build:h5` + `npm run build:mp-weixin` 与手测。
- 收尾:`npm run test`、两端构建全过。

## 非目标

- 不做「登录用户自定义彩种」(后端,下一里程碑)。
- 不改后端、API、数据库。
- 不删除 `latest.vue` 页面。
