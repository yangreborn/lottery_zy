# B · 选号器改造（机选预览筛选）· 设计文档

- 日期：2026-06-24
- 定位：选号器支持"机选先预览不保存→勾选要的→保存选中"，机选 5 注/10 注，暂时隐藏定胆。对应 note.txt 第 6、8 项。
- 前置：M1–M4b + E 改版已合并 master；记录号码后端（create/generator）与前端 picker 页已就绪。

---

## 0. 范围

**本期做**：① 后端预览生成接口（不写库）；② create 接受机选选中的具体号码（gen_type=random + numbers）；③ 前端 picker 改造：手动/机选模式切换、机选 5/10 注预览、勾选筛选、保存选中、换一批、隐藏定胆。
**不做**：定胆功能移除（仅前端隐藏，后端 dan_random 代码保留）；记录分组/时间（C）；统计筛选（D）；新彩种（A）。

## 1. 后端改动

### 1.1 预览生成接口（新）

`POST /api/user/number/generate`（需登录，authentication_classes=[]，用 X-User-Id 头或 session）：
- body `{code, count}`；count 钳制到 `[1, 10]`，缺省/非整数按 5。
- 取上架彩种 rule_config，调 `random_numbers(rule_config)` 生成 count 注，每注校验 `validate_numbers` 通过（合法重试极少，直接用）。
- **不写库**，返回 `make_response(data={"sets": [{"red":[...],"blue":[...]}, ...]})`。
- 未知彩种 → code=1。

### 1.2 create 接受机选选中号码

`NumberCreateView` 当前：gen_type=random 时忽略客户端 numbers、自己生成。改为：
- gen_type=random 且 **请求带非空 numbers** → 用传入 numbers，走 `validate_numbers` 校验，非法 code=1；校验过则入库（gen_type 仍记 random）。
- gen_type=random 且 **不带 numbers** → 仍服务端 `random_numbers` 生成（兼容旧行为）。
- manual / dan_random 分支不变。

> 这样"保存机选选中的那几注"以 gen_type=random（机选）正确入库，且号码是预览时用户看到的那几注。

## 2. 前端 api

`src/api/user.js` 新增：
- `generateNumbers(code, count)` → POST `/api/user/number/generate` `{code, count}`，返回 `data.sets`。

## 3. 前端 picker 改造（pages/mine/picker.vue）

顶部加**模式切换**两段：`手动` / `机选`（默认机选，呼应"先机选"）。

### 3.1 手动模式（保留现有）
- 红/蓝区可点球（BallSelectable）、选满才可"保存手选"（gen_type=manual）。逻辑基本不变。

### 3.2 机选模式（新）
- 按钮：「机选 5 注」「机选 10 注」「换一批」。
- 点 5/10 注 → `generateNumbers(code, n)` → 得 `sets`（N 注）→ 屏上每注一排号码球（Ball 展示）+ 每注一个勾选标记；默认全不选或全选（默认全选，方便"全要"）。
- 「换一批」→ 用当前注数重新 generate，替换列表，清空/重置勾选。
- 勾选交互：点某注切换其选中态（用纯函数 `toggleIndex(selectedSet, i)` 维护选中下标集合，可单测）。
- 底部「保存选中(N)」→ 对每个选中的注调 `createNumber({code, gen_type:'random', numbers, note, target_issue})`（循环，N≤10）；全部成功 toast + switchTab 回我的。

### 3.3 隐藏定胆
- 删除「定胆随机」按钮及其相关 UI/handler（saveDan）。后端 dan_random 不动。

### 3.4 备注/目标期号
- 输入框对两种模式的保存都生效（机选保存时同 note/target_issue 应用到每注）。

## 4. 纯函数（utils/picker.js 扩充，可单测）

- `toggleIndex(set, i) -> Array`：i 在集合则移除、否则加入，返回新数组（升序）。

## 5. 错误处理

- generate 失败 / create 失败：toast 提示，不崩页。
- 机选未勾任何注就点保存：toast「请先勾选」，不发请求。
- create 多注循环中个别失败：记失败数，toast 告知"成功 X 注、失败 Y 注"，成功的已入库。

## 6. 测试

- **后端 pytest**：
  - generate：返回 count 注、每注 validate_numbers 合法、不写库（AccessLog 无关；UserNumber.count 不变）；count 钳制（传 99→≤10、传 0/非法→5）；未知彩种 code=1；未登录 code=1。
  - create：gen_type=random 带合法 numbers → 入库且 numbers 等于传入、gen_type=random；带非法 numbers → code=1 不入库；不带 numbers → 仍生成入库（回归）。
- **前端 vitest**：`generateNumbers` 调用参数；`toggleIndex` 增删/升序。
- **人工**：picker 机选 5 注 → 勾选 → 保存 → 我的出现选中注；换一批；手动模式仍可用；无定胆按钮。

## 7. 怎么看效果

后端 8123、前端 dev:h5 / dev:mp-weixin：进选号 → 机选 → 机选5注 → 屏出 5 注带勾选 → 勾 2 注 → 保存选中 → 我的号码新增 2 注（机选标签）；换一批重生成；手动模式照常；定胆已隐藏。

## 8. 里程碑定位

note.txt 第二批（B 选号器改造，6/8）。后续：D 统计筛选 → C 记录分组 → A 新彩种 → F 中奖信息 → G 体验版。
