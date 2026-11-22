# Case: hello post, agy-led trial (2026-11-22)

"你好：这个博客为什么建，以及怎么搭起来的" (slug `hello-building-this-blog`). First agy-led trial (Workflow step 7): agy (Gemini, Orchestrator Neon) wrote every draft from a brief; Claude wrote the brief and `check.py`, drew the diagrams, checked facts, and handled Notion. Sources: blog `git log`, README, TODO, `lib/notion.ts`, `app/globals.css`, `app/icon.svg`.

## Round 1 → Eric's feedback

| # | Feedback | Cause | Fix |
|---|---|---|---|
| 1 | 流水账: the front-end section reads like the chat log; style starting point, logo, fonts and the coral inline-code colour got equal length, though their importance falls in that order and the last needs no mention | The brief listed facts as a flat list with no ranking, so the writer gave each one a paragraph | Hard rule 12 (详略得当); brief v2 ranks every section's points and marks some 删 |
| 2 | The blog started in November 2025; the post said December | The brief took the first commit (2025-12-06) as the start date | Hard rule 6: a first commit is not the start date; ask or say "first commit" |
| 3 | Try the `fireworks-tech-graph` skill, default theme, after upgrading it per its GitHub page; show both diagrams side by side | — | Latest 1.2.0 cloned from GitHub into `~/workspace/research/fireworks-tech-graph` (installing into `~/.claude/skills` is outside this agent's write scope); Style 1 Flat Icon diagram rendered and placed after the hand-drawn one |

agy on round 1: no tone or privacy problems; facts matched the brief. The flat structure came from the brief, not the writer.

## Round 2

Brief v2 quoted the feedback, ranked each section, merged two sections, and `check.py` rejected the removed details (commit count, coral colour, December dates) and required 4–5 headings. agy finished in about 4 minutes; front end ≈195 / 110 / 45 characters for style / logo / fonts. Eric picked the hand-drawn diagram (fireworks version removed; he upgraded the fireworks skill himself).

## Round 2 → Eric's feedback

| # | Feedback | Fix |
|---|---|---|
| 1 | Notion also solves cross-platform writing; a whole post can be done without a computer | Added to the Notion section, ranked after agent-friendliness |
| 2 | Title `你好：这个博客为什么建，以及怎么搭起来的` does not read as human-written | Hard rule 1 title guidance: no `X：A，以及 B`; offer alternatives |
| 3 | Date the post a month earlier (2026-10-22); no recent dates in the text, it was written last month and published late | Brief v3 removes absolute dates and the line about the earlier agent-crew post (published after the new date); `check.py` rejects them |

When a post is back-dated, check every relative reference ("前一篇", "最近", "今天") against the new date, not only the explicit dates.

## Round 3 and outcome

- Round 3: Notion can be managed from the phone, and the platform keeps the content safe (history, sync). Two sentences added; agy on the faster model finished in 71 s and changed only that section.
- Eric then edited by hand and published: title `Hello`, slug `hello-my-first-blog-post`, page set to full width. Body unchanged from round 3.
- After publishing, the post's image failed ("User does not have access") because the site used Notion's image proxy, which only serves pages once published to the web. Fixed in blog PR #4 (signed S3 URLs). Check images on the live page after every first publish.

Tally: 3 rounds of content feedback after the first draft, plus a title Eric chose himself. agy's mistakes were few (no tone, privacy or fact errors); most rounds traced back to the brief (flat facts, a colon-style title example in this skill, a start date taken from git) or to new requests. Compared with the agent-crew post (Claude, 2–3 rounds): about even; the brief matters more than the writer.

## Notes

- A ranked brief is what fixes 详略; tell the writer the order and what to drop, not just the facts.
- Fireworks 1.2.0: `fireworks.py render` refuses truncated text under `text_policy: "strict"` and refuses labels with no free spot; widen gaps between nodes (≥ 80 px) rather than shortening copy.
