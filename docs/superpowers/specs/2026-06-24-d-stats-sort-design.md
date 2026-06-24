# D · 统计页"最多/最少"排序筛选 · 设计文档

- 日期：2026-06-24
- 定位：统计页加排序切换（号码顺序/出现最多/出现最少），让用户看最近 N 期出现最多/最少的号码。对应 note.txt 第 11 项。
- 前置：统计接口 draw/stats（compute_number_stats 返回每号码 count/miss）已就绪；一年真实数据已入库。

---

## 0. 范围

**本期做**：纯函数 `sortCells(cells, mode)`；统计页加排序切换行（号码顺序/出现最多/出现最少），本地重排红/蓝热力图。
**不做**：后端不动（getStats 已返回每号码 count）；Heatmap 组件不动；记录分组（C）、新彩种（A）等其他 note 项。

## 1. 数据现状

`GET /api/openapi/draw/stats?code=&periods=` 返回 `data:{red:[{number,count,miss},...], blue:[...], periods}`，已含每号码出现次数 count。"最多/最少"即按 count 排序——纯前端，无需后端改动。

## 2. 纯函数 sortCells（utils/statsort.js）

`sortCells(cells, mode) -> Array`（不可变，返回新数组）：
- `mode='number'`：按 `number` 升序（默认，号码顺序）。
- `mode='most'`：按 `count` 降序；count 相同按 `number` 升序（平手 tie-break）。
- `mode='least'`：按 `count` 升序；count 相同按 `number` 升序。
- 入参 cells 为 `[{number,count,miss}]`；非数组/空返回 `[]`。

## 3. 统计页 stats.vue

- 在期数选择行下方加**排序切换行**：三个选项 `号码顺序 / 出现最多 / 出现最少`，与期数选项同款 chip 样式（选中红底）。
- 新增 `sortMode` ref（默认 `'number'`）；点切换只改 sortMode（**不重新请求**）。
- 用 computed `redSorted = sortCells(redCells.value, sortMode.value)`、`blueSorted = ...`，传给 `<Heatmap :cells="redSorted" />`。
- Heatmap 配色按 count 占比（其内部用 cells 最大 count），重排不影响 max，照常着色。
- 期数切换仍重新请求（load）；排序切换只本地重排。

## 4. 错误处理

- 接口失败：沿用现有 toast + 空态。
- sortCells 对空/非数组返回 `[]`，不崩。

## 5. 测试

- **vitest**：`sortCells` 三 mode（number 升序、most 降序+平手号码升序、least 升序+平手），不可变（不改入参），空/非数组返回 `[]`。
- **人工**：`dev:h5`/开发者工具看统计页：切"出现最多"红球按次数降序、最热排前；"最少"升序；"号码顺序"复原；切换不重新请求。

## 6. 怎么看效果

统计页选近 100 期 → 切"出现最多" → 红球按出现次数从高到低重排（如最热的 02/03/13 排最前）；切"最少"→ 最冷的排前；切"号码顺序"→ 回到 01..33 顺序。

## 7. 里程碑定位

note.txt 第 11 项（统计筛选）。后续：C 记录分组（7）→ A 新彩种（3/4）→ F 中奖信息（1）→ G 体验版（10）→ dlt 翻页抓满一年（可选）。
