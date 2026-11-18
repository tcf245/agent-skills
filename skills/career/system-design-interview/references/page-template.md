# Wiki Page Templates

Section titles follow the language Eric used in the request. The Chinese titles below match the first page written with this skill (`AI Chat Platform System Design`), which is the reference example for depth and tone.

## Concept page

Path: `wiki/concepts/<Topic> System Design.md`

```markdown
---
title: <Topic> System Design
tags:
  - concept
  - system-design
  - <domain>
created: YYYY-MM-DD
status: refined
---

# <Topic> System Design

<One paragraph: the prompt, the scale, the two or three hard problems.>

一句话版本：

> <The key mechanism of each hard problem in one or two sentences.>

这是工程设计方案，不是对 <real product> 内部实现的描述。

## 1. 需求与容量
### 范围            <table: 功能 / 难点相关约束 / 暂不考虑 / 非功能>
### 估算（全部是设计假设）   <table: 指标 / 推导 / 结果>
<One conclusion sentence: where the bottleneck is.>

## 2. 架构与职责划分
![<alt>](../../attachments/diagrams/<slug>-architecture.png)
<table: 组件 / 职责 / 不负责>
<table of concepts that must be kept apart>
<deployment note>
### 存储           <table: 存储 / 内容 / 选择理由>

## 3. 难点一：<name>
### 3.1 先定义"<goal>"         <verifiable guarantees>
### 3.2 为什么朴素方案不行      <comparison table, same numbers>
### 3.3 <mechanism>
![<alt>](../../attachments/diagrams/<slug>-<mechanism>-flow.png)
<state layout, pseudo-code, numbered timeline>
### 3.4 回答 <N> 个难点         <one labeled paragraph per stated difficulty>
### 3.5 一致性与故障            <failure table, measurement error, defensible alternative>

## 4. 难点二：<name>
### 4.1 <disambiguation table>
### 4.2 数据模型
### 4.3 API
### 4.4 状态机                  <mermaid stateDiagram-v2>
### 4.5 <core decoupling>       <mermaid sequenceDiagram>
### 4.6 故障场景逐个过           <scenario table>

## 5. 经得住问：追问清单          <Q1..Q14, bold question + short answer>
## 6. 扩展思考
## 7. 用户翻十倍的优化方向        <table: 方面 / 现在 / 10×>
## 8. 面试中的讲述顺序

## Related
- [[<existing concept>]] — <why it is related>
```

Rules for the concept page:

- Link the first mention of any concept that has a wiki page.
- Do not link to record pages.
- Image embeds use the relative Markdown form shown above.

## Record page

Path: `wiki/records/YYYY-MM-DD <Topic> System Design.md`

```markdown
---
title: YYYY-MM-DD <Topic> System Design
tags:
  - record
  - system-design
  - interview-prep
created: YYYY-MM-DD
status: active
---

# YYYY-MM-DD <Topic> System Design

<What this session was, with links to the concept page and to any earlier attempt.>

**状态：待 Eric review。** 下面的判断由 agent 提出，尚未经 Eric 确认或质疑。

## Eric 提出的约束           <numbered, in his words>
## 本次形成的设计判断         <one line each>
## 关键结论（可直接复述的数字和界）
<example parameters, marked as assumptions>
<table: 结论 / 内容 — invariant, each bound with its number, sizing rule, capacity estimate,
 bottleneck judgment, what changes at 10×>
## 继续讨论的入口
<how to resume in a new session: which pages and sections to read, in order;
 what to update once a point is settled; what is left undone or unverified>
## Review 记录
| 日期 | 质疑 / 问题 | 结论 | 改动 |
|---|---|---|---|
| — | 尚未 review | — | — |
## 相对上次回答的变化         <table: 上次 / 这次 — only if an earlier attempt exists>
## Review 时值得质疑的点      <the trade-offs he may reject, as questions>
## 图                        <paths>
## Related
```

The record page is the handoff document. Write "关键结论" and "继续讨论的入口" so that an agent with no memory of the session can resume from this page alone.

## index.md

Add one line in the concept list near the other system design concepts, and one line under `### System Design 学习记录`:

```markdown
- [[<Topic> System Design]] 🆕 — <scale, hard problems, key mechanisms>
- [[YYYY-MM-DD <Topic> System Design]] 🆕 — <what the session covered, what awaits review>
```

## log.md

Append:

```markdown
## [[YYYY-MM-DD]] CAPTURE | <Topic> System Design
- Source: conversation（System Design 练习：<prompt and focus>）
- Created: [[<Topic> System Design]]、[[YYYY-MM-DD <Topic> System Design]]
- Diagrams: `attachments/diagrams/<slug>-*.svg/png`
- Updated: `index.md`
- Status: 设计由 agent 提出，待 Eric review
```
