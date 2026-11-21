# Case: agent-crew post (2026-11-21)

First post written by an agent into the blog database: "agent-crew：在 Discord 上搭建家庭 AI 助理团队" (Notion page `41f16a46b81381f982a0d12a19575175`, slug `agent-crew`). Sources: `~/workspace/agent-crew` README, CLAUDE.md, `docs/ARCHITECTURE.md`, `docs/STATUS.md`, `docs/specs/`, `docs/handover/2026-10-31-magpie.md`, `crew/workout.py`, `personas/coach.yaml`, `git log`.

## v1 → Eric's feedback

| # | Feedback | What changed | Where it now lives |
|---|---|---|---|
| 1 | Mask names, including Eric and family | 我 / 家人 / 一位家庭成员; diagram "Eric / 宝宝" → "Family" | Hard rule 2 |
| 2.1 | Missed benefit: sharing with family or invited people through Discord server roles; similar platforms (Telegram, Slack) could work | New section 多人使用: identity by ID, per-person data and tokens, role-based access, frontend isolated in one adapter | Default structure: capabilities |
| 2.2 | Missed benefit: interactive cards (artifacts), explained through the workout card loop: request card, tick sets, submit, coach feedback, record in wiki, adjust next plan | New section and diagram `4-workout-loop` | Capabilities need an end-to-end walk-through |
| 3 | Backend can use Claude to drive agy so both quotas are used | Section "Claude 调度 agy，把手上的额度都用起来" | Reasons must come from real incidents |
| 4 | No trendy colloquial phrasing (它很脆, 拉满, 爆炸); calm narration; no clickbait; run the de-AI-tone skill | Title and body rewritten; `lieflat-less-ai-tone` pass | Hard rules 1 and 7 |
| 5 | No Chinese in workflow diagrams, so they can be reused for a bilingual version | All four SVGs in English | Hard rule 3 |
| 6 | Discord makes voice easy | Added to the Discord reasons | — |
| 7 | One-off sharing: turn a page or conversation into HTML on the tunnel, with auth and expiry | Section 一次性分享 (`publish_page`, `share_page`, 1/7/30-day signed links, revocation, control panel) | — |
| 8 | Unbuilt items such as the LLM gateway that removes single-vendor dependence | Section 还没有做的 (magpie, paused, and why) | Default structure: 还没有做的 |
| 9 | Turn this case into a reusable writing skill | This skill | — |
| later | Hard rule on tone, verbatim | Hard rule 1 | — |

## v1 phrases that were removed

- Title "在 Discord 里养一支 AI 助理团队：agent-crew 搭建记" (养一支 is cute marketing) → plain title.
- "它很脆" → "CLI 升级或 Mac 重启之后，wiki 的读写权限经常失效".
- "这是我最看重、也花时间最多的部分" kept only as "主动提醒是投入时间最多的部分".
- Rhetorical "不是一个只会转发通知的闹钟" style contrasts (翻案腔) removed.

## Process notes

- Notion OAuth from the Dia browser did not return to the localhost callback; `/mcp` in Claude Code worked.
- `fireworks-tech-graph` was not installed; hand-written SVG in the same Claude-style palette, rendered with `rsvg-convert`, was good enough. Always view the PNGs: the first render had a label crossing a group title and text overflowing boxes.
- De-AI-tone detection on v2 flagged dense 顿号 enumerations (4.7/千字 vs human ≈1.78) and semicolons (3.0/千字) as the main items; semantic checks (renaming, cohesion chains, conclusion colons, isomorphic triples) were below thresholds.
