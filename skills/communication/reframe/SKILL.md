---
name: reframe
description: >-
  Teach Eric the expert terminology for what he is building from his own files
  and description, then rewrite his description in those terms. Use ONLY when
  Eric explicitly says "reframe", "帮我换个说法", or "找术语" (never
  auto-trigger), such as before an admin new-role interview or when Eric gives
  a vague voice-dictated requirement.
type: workflow
triggers:
  - "reframe"
  - "帮我换个说法"
  - "找术语"
platforms: [cc, codex, gemini]
---

# Reframe — 换专业说法与找术语

只在 Eric 明确说 `reframe`、「帮我换个说法」或「找术语」时执行，不自动触发。常用于 admin 新增角色访谈前，或 Eric 用语音给出模糊需求时。

起点：**先读 Eric 给的文件、代码仓库或 wiki 页面，从他自己的描述和材料出发，不凭空想。**

## 步骤

1. **辨别问题类型**：列出 2–3 种这可能是什么问题，每种写一条能区分它与其他问题的信号；选出最可能的一种并说明原因。
2. **给 8–12 个专家术语**（按对实现方式的影响排序）：
   - 术语名 + 一句大白话意思 + 它对应原描述的哪部分。
   - 用这个词能让你向 agent 要什么。
   - 一个真实项目、论文或系统文档链接。**每个链接必须用 WebFetch 或同类工具实际打开，确认内容确实按该含义使用此术语；打不开或内容对不上就删掉这条，不要保留未确认的链接。**
3. **从 2–3 个邻近领域借术语**：写清哪些做法和术语可以带过来，以及**类比在哪里不成立**；顺带指出他没提到但该关心的事。
4. **重写描述**：用新术语重写 Eric 的原始描述。

## 输出格式

- 给手机看：**短、不要 Markdown 表格**，不写客套和废话。

## 出处

改编自 pstack 的 `reframe`，作者 Lauren Tan（@poteto），MIT License，原链接：https://github.com/cursor/plugins/tree/main/pstack/skills/reframe
