---
name: sharpen
description: >-
  Deepen a vague task prompt by answering four expert-framing questions and
  rewriting it without executing the task. Use ONLY when Eric explicitly says
  "sharpen" or "磨一下这个需求" (never auto-trigger), such as before an admin
  new-role interview or when Eric gives a vague voice-dictated requirement.
type: workflow
triggers:
  - "sharpen"
  - "磨一下这个需求"
platforms: [cc, codex, gemini]
---

# Sharpen — 深化需求

只在 Eric 明确说 `sharpen` 或「磨一下这个需求」时执行，不自动触发。常用于 admin 新增角色访谈前，或 Eric 用语音给出模糊需求时。

核心原则：**不做任务本身**，只把需求磨深，不把它放大。

## 步骤

1. **先回答四问**（针对当前任务，直接给出答案）：
   - 这个领域的顶级专业人士会做什么，而原需求里没要求？
   - 他们会从什么最原始的材料开始，而不是已经消化过的摘要？
   - 他们会用什么具体方法和工具？
   - 除了你和 Eric 之外，还有什么外部信号能证明结果是对的？
2. **输出改写后的完整 prompt**：
   - 把四问的答案写进可执行要求。
   - **保留原需求里能改变做法的具体要求，删掉原文没有的发挥**。
   - 凡是**能靠实验决定的选择**，要求 agent 先做原型，再按观察结果推荐方案。
   - 凡是**实验定不了的纯偏好类选择**（口味、取舍），单独列出来留给 Eric 拍板，不要替他选。

## 禁止事项

- 直接动手执行原任务。
- 擅自扩充范围或塞入原文没有的发挥。
- 替 Eric 做纯偏好类决定。

## 出处

改编自 pstack 的 `sharpen`，作者 Lauren Tan（@poteto），MIT License，原链接：https://github.com/cursor/plugins/tree/main/pstack/skills/sharpen
