# 合规小批（协议/数据来源/纯随机/删除确认）· 设计文档

- 日期：2026-06-25
- 定位：小程序过审与合规相关的 4 个小改，纯前端。对应 note.txt 第 13、20、21、24 项。

---

## 0. 范围

**本期做**：① 删除前确认框；② 机选纯随机声明；③ 数据来源标注；④ 用户协议 + 隐私协议页 + 入口。
**不做**：不动后端；协议文本为模板（用户后续可替换正式法务文本）；其他 note 项（15/16/17… 另起里程碑）。

## 1. 删除确认（24）

`pages/mine/index.vue` 的 `doDelete(id)`：删除前 `uni.showModal({ title:'确认删除', content:'删除后不可恢复，确定删除这条号码？' })`，仅 `res.confirm` 时才 `deleteNumber(id)` + `load()`；取消不动。

## 2. 机选纯随机声明（21）

`pages/mine/picker.vue` 机选模式（`mode==='jixuan'`）的机选按钮行下方加一行小字：「机选号码为系统纯随机生成，不含任何预测或分析成分」。

## 3. 数据来源标注（20）

`pages/home/index.vue` 底部加 footer 一行：「数据来源：中国福彩网 cwl.gov.cn · 中国体彩网 sporttery.cn」，灰色小字居中。

## 4. 用户协议 + 隐私协议（13）

- 新增页面 `pages/legal/doc`（pages.json 注册），通过 `?type=agreement|privacy` 区分展示两份文本。
- 文本放 `src/utils/legal.js` 的 `LEGAL_DOCS = { agreement: {...}, privacy: {...} }`（title + 段落数组），doc 页按 type 渲染标题 + 段落。
- 文本模板要点：定位为免费彩票**查询/工具**类应用；匿名使用，不强制注册；开奖/统计**数据来自中国福彩网、中国体彩网官方网站**，仅供参考、以官方为准；**不提供购彩、不代购、不涉及任何投注交易**；机选号码纯随机、不构成任何中奖预测或投注建议；未成年人勿沉迷。
- 入口：home footer 加「用户协议 · 隐私协议」两个可点链接，`navigateTo` 到 `/pages/legal/doc?type=agreement` / `?type=privacy`。

## 5. 错误处理

- showModal 取消 → 不删除、无副作用。
- legal doc 页未知 type → 默认显示用户协议（兜底）。

## 6. 测试

- 前端 vitest：`LEGAL_DOCS` 含 agreement/privacy 两份且各有 title + 非空段落；按 type 取文档的纯函数（getLegalDoc(type) 兜底 agreement）。
- 人工：删除弹确认；机选页有纯随机声明；首页底部有数据来源 + 两个协议链接，点开能看协议正文。

## 7. 里程碑定位

note.txt 第 13、20、21、24 项（合规小批）。后续：历史页修正(16) → 记录区重构(15/25/23) → 通知体系(19/17/18) → 微信登录(14) → 开奖海报(22)。
