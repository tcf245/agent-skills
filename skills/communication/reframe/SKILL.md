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

# Reframe

Run ONLY when Eric explicitly says `reframe`, `"帮我换个说法"`, or `"找术语"` (never auto-trigger). Commonly used before an admin new-role interview or when Eric gives a vague voice-dictated requirement.

Starting point: **read the files, code repo, or wiki pages Eric provides first; work from his own description and materials rather than guessing.** Reply in the language the user wrote in.

## Steps

1. **Identify the problem type**: list 2–3 kinds of problem this could be, with one distinguishing signal for each; pick the most likely one and explain why.
2. **Give 8–12 expert terms** (ordered by how much they affect implementation):
   - Term + a one-sentence plain-language meaning + which part of the original description it maps to.
   - What using this term lets you ask an agent for.
   - One real project, paper, or system documentation link. **Open every link with WebFetch or an equivalent tool and confirm it actually uses the term in that sense; if it does not load or does not match, drop the item rather than keeping an unverified link.**
3. **Borrow terms from 2–3 adjacent fields**: state which practices and terms transfer, and **where the analogy breaks down**; also flag anything Eric did not mention that he should care about.
4. **Rewrite the description**: rewrite Eric's original description using the new terminology.

## Output format

- For reading on a phone: **short, no Markdown tables**, no filler or pleasantries.

## Source

Adapted from the [Cursor pstack `reframe` skill](https://github.com/cursor/plugins/tree/main/pstack/skills/reframe) by Lauren Tan (@poteto), MIT License.
