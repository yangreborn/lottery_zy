# 协议/数据来源 样式 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** 首页协议链接调淡、数据来源只显网址。

**Architecture:** 单文件展示调整。

**Tech Stack:** uni-app Vue3。

## Global Constraints

- 只改 `home/index.vue`；不动 `legal.js`。
- 协议链接颜色 `#bbb`；数据来源文案「cwl.gov.cn · sporttery.cn」。

---

### Task 1: 首页底部样式与文案

**Files:**
- Modify: `lottery_frontend/src/pages/home/index.vue`

- [ ] **Step 1: 数据来源文案改为纯网址**

把 `<text class="src">数据来源：中国福彩网 cwl.gov.cn · 中国体彩网 sporttery.cn</text>` 改为：

```html
      <text class="src">cwl.gov.cn · sporttery.cn</text>
```

- [ ] **Step 2: 协议链接颜色调淡**

把样式 `.lk { color: #e53935; font-size: 26rpx; }` 改为：

```css
.lk { color: #bbb; font-size: 26rpx; }
```

- [ ] **Step 3: 全量前端测试**

Run: `cd lottery_frontend && npm test`
Expected: PASS（无回归）。

- [ ] **Step 4: 提交**

```bash
git add lottery_frontend/src/pages/home/index.vue
git commit -m "style(home): 协议链接调淡，数据来源只显网址(note31)"
```

---

## Self-Review

- note 31 协议淡化 → Step 2 ✓；数据来源只显网址 → Step 1 ✓。
- 无 placeholder；不动 legal.js（协议正文保留）。
