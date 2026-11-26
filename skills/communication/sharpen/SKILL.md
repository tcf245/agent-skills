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

# Sharpen

Run ONLY when Eric explicitly says `sharpen` or `"磨一下这个需求"` (never auto-trigger). Commonly used before an admin new-role interview or when Eric gives a vague voice-dictated requirement.

Core rule: **do not execute the task itself** — deepen the requirement without expanding its scope. Reply in the language the user wrote in.

## Steps

1. **Answer four questions first** (directly, for the current task):
   - What would a top practitioner in this field do that the original prompt did not ask for?
   - What raw primary source would they start from instead of a pre-digested summary?
   - What concrete methods and tools would they use?
   - Besides you and Eric, what external signal would prove the result is right?
2. **Output the rewritten full prompt**:
   - Turn the four answers into actionable requirements.
   - **Keep every specific requirement from the original prompt that changes how the work is done, and cut anything invented that was not in the original.**
   - For any choice **that an experiment can settle**, instruct the agent to prototype first and recommend an option based on what it observes.
   - For any **pure preference choice that an experiment cannot settle** (taste, trade-offs), list it separately for Eric to decide — do not pick for him.

## Do not

- Execute the original task directly.
- Expand scope or add inventions not present in the original prompt.
- Make pure preference decisions for Eric.

## Source

Adapted from the [Cursor pstack `sharpen` skill](https://github.com/cursor/plugins/tree/main/pstack/skills/sharpen) by Lauren Tan (@poteto), MIT License.
