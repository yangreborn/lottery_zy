# 里程碑E 玩法说明=奖级规则直达 设计（note 42 + 43）

**目标：** 玩法说明页只展示奖级规则，选彩种即直达，去掉多余的类型点击。纯前端。

## 背景

`guide/index.vue` 现有类型 Tab（全部=intro,rule / 玩法说明=intro / 奖级规则=rule），用户进来还要再点一次类型才看到规则。
- note 42：玩法说明只记录奖级规则（什么情况中奖、奖金大概多少）。
- note 43：点玩法说明→选彩种就直接展示奖级规则，不要额外点一次。

## 方案

`guide/index.vue`：
- 移除类型 Tab（`types`/`curType`/`chooseType` 及模板 `.types` 块）。
- `load()` 固定 `getGuideList(store.code, 'rule')`，进入即按当前彩种展示奖级规则。
- 保留 `LotteryTabs`，`onChange(code)` = `setCode` + `load()`（选彩种直达）。
- 列表项点击仍进 `guide/detail`。

后端 guide 模型/类型不变（仍可有 intro 等，只是玩法说明页只查 rule）。menu「玩法说明」名称保留。

## 文件

- 修改：`src/pages/guide/index.vue`

## 测试

- 组件接线（去 Tab + 固定 rule 查询），无新增可单测逻辑；getGuideList api 已有单测。全量前端测试通过 + 手测：进玩法说明选彩种即见奖级规则、无类型 Tab。
