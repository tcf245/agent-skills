---
name: blog-writing
description: Use when Eric asks to write, draft, revise, or publish a blog post or long-form write-up (especially into his Notion "Blog Articles" database), or to turn a project, repo, or conversation into an article with diagrams. Trigger on 写博客, 写一篇, blog, 文章, 发到博客, 草稿, write-up, post about.
type: workflow
triggers:
  - "写一篇博客"
  - "write a blog post"
  - "发到博客"
---

# Blog Writing

Eric's blog reads from a Notion database. You research the subject from primary sources, draft in a calm voice, draw reusable English diagrams, write the post into Notion as an unpublished draft, run the de-AI-tone pass, and leave publishing to Eric. The rules below come from real feedback on the first post (see `references/case-2026-11-21-agent-crew.md`); read that case before your first draft.

## Hard rules

1. **Tone (Eric, 2026-11-21, verbatim):** 除非有特定指向性，否则请尽量不要使用网络流行用语，不用考虑流量和吸引眼球，不要用震惊体，请用一个平静的视角和口吻来叙述，保持 taste。
   - No internet slang or hype words (它很脆, 拉满, 爆炸, 炸裂, 封神, 王炸, 杀疯了, 天花板, 绝绝子, 养一支…). No clickbait or 震惊体 titles. No 吸睛 hooks.
   - Titles state the subject plainly, e.g. `agent-crew：在 Discord 上搭建家庭 AI 助理团队`.
   - Describe what the thing does and why, in plain declarative sentences. Let facts carry weight; do not add adjectives to sell them.
2. **Privacy masking.** No real names of Eric, family members, or other people in the body or diagrams; write 我, 家人, 一位家庭成员, 家里人. Also leave out personal domains, Discord/Notion IDs, emails, account numbers, children's details, and anything from health or finance records. When unsure, mask it and mention it in your report.
3. **Diagrams contain no Chinese.** All diagram text is English so the same images work for a future bilingual (zh/en) version.
4. **Publish only on an explicit instruction.** Create or update the page with `Published = __NO__` by default. Tick it when Eric clearly says to publish (from the phone counts too). The page must also be published to the web in Notion, which only Eric can do (see `references/notion-blog.md`); ask for it in the same message, then confirm the live URL returns 200.
5. **Every key choice gets its reason.** Write the decision, then 原因/为什么 in one or two sentences, grounded in the source (a design doc, a feedback entry, a real incident). No invented reasons.
6. **Facts come from sources.** Numbers (commits, dates, counts, limits) are looked up, not remembered. Separate shipped from not-yet-built from not-yet-verified; say so plainly.
7. **Reasonable abstraction (保持一点合理的抽象，不必要的细节避免太具体).** Describe capabilities and roles, not the current instance. Write "调度 agy 以及其他 agent（如 Codex）", not only "agy"; write "轻量 / 标准 / 高 档位", not specific model names; write "用量分档", not exact percentages. Keep a concrete detail only when it explains a decision (one real incident is enough). Details that are likely to change (model versions, thresholds, file names) stay out of the post.
8. **Logical closure (请考虑逻辑闭环).** Every component in a diagram must have a reason to exist in the flow: something goes in and something comes back. Before drawing, trace each node: who produces its input, where its output goes, and how the user gets the result. A node with no way back (e.g. a web page that is only an endpoint) means the diagram is missing an edge or the text is missing a loop. Use two-way arrows where the user both sends and receives.
9. **Real screenshots help understanding (有真实 case 贴图帮助理解).** For each capability that has a UI (cards, pushes, pages), add one real screenshot next to its explanation, with a one-paragraph caption saying what the reader is looking at. Before uploading, review every pixel and pixelate private data: personal domains and URLs, addresses and cities, health, finance, account or ID numbers, other people's details. Names follow Eric's instruction for that post (in the 2026-11-21 post he said names in screenshots may stay). Mention in the caption that parts are masked, and list what you masked in your report. Then put each phone screenshot in a phone frame at phone size (Eric, 2026-11-21: like Apple's site, not a full-width screenshot): `scripts/phone-frame.py shot.png out.png` draws an iPhone-style bezel on a transparent 1600×1240 canvas so the phone shows at about a third of the column width; check it on light and dark backgrounds (`magick out.png -background white -flatten preview.png`).
10. **Keep the facts current.** Check the latest state in the repo and with Eric before describing who does what (e.g. ops moved from `#admin` to `#projects` with an Engineer agent on 2026-11-21).
11. **Run the de-AI-tone pass** (`lieflat-less-ai-tone` skill) on every draft, following its own workflow: detect, give the report, wait for Eric's reply, then rewrite and re-test.

## Workflow

1. **Gather sources.** For a project, read its README/CLAUDE.md, architecture and status docs, design specs, feedback log, and `git log`. Note what is shipped, paused, and planned. For Eric's background, use the LLM Wiki (personal-context-sync).
2. **Ask only if the angle is unclear.** Default structure for a project post:
   - 开头：what it is, timeline (dates, commit count).
   - 想解决的问题 + design goals.
   - 整体架构 (diagram) + 关键选择, each with its reason.
   - Capabilities worth calling out, each with a concrete walk-through (e.g. one real loop end to end, with a diagram).
   - Workflows (diagrams).
   - 适合 / 不适合.
   - How it evolved (feedback, incidents).
   - 还没有做的 (planned or paused features and why they matter).
   - 当前状态 (honest: what is verified, what is not, known risks).
3. **Draft locally** as Markdown in the scratchpad, using `![alt](file.png)` placeholders for images.
4. **Diagrams.** Hand-write SVG in the house style (`assets/diagram-template.svg`: cream `#f8f6f3` background, white boxes, coral `#d97757` for model steps, green `#eef3ec` for deterministic code, dashed groups). Render with `rsvg-convert -z 2 in.svg -o out.png`, then **open every PNG and check** for overflowing text, labels crossing lines, and leftover CJK (`grep -P '[\x{4e00}-\x{9fff}]'` on the SVG must be empty). Fix and re-render before uploading. Keep the SVG sources next to the draft.
5. **Upload images** to Notion: call `notion-create-file-upload` per file, then `NOTION_UPLOAD_TOKEN=<bearer> scripts/notion-upload.sh <upload_url> <file>` (needs `api.notion.com` in the sandbox allowlist). Replace each placeholder with `<image source="file-upload://<id>">caption</image>`.
6. **Write to Notion** (see `references/notion-blog.md` for the data source, fields, and Markdown rules). New post: `notion-create-pages` with the data source as parent. Revision: `notion-update-page` `replace_content`, and `update_properties` for the title.
7. **Use Gemini as a second writer or reviewer** (Eric, 2026-11-21: Gemini is good at text; use it). **Next post: let agy write the first draft**, and route Eric's feedback rounds to agy (Eric wants to see how Gemini responds to feedback); you build the brief, the diagrams, the screenshots, verify facts, and handle Notion. Through the `agy-delegation` skill, hand agy a no-repo task with the sources, a brief that carries Eric's requests and feedback in his words, this skill and the de-AI-tone rules, plus a `check.py` acceptance script (placeholders present, banned words absent, length). For a comparison, do not give agy your own draft. agy cannot reach Notion; you upload its Markdown as a separate draft page (`<slug>-gemini`). For a review instead, give it your draft and ask for a list of concrete edits.
8. **De-AI-tone pass** (hard rule 11). Deliver its report and stop until Eric replies. After the rewrite, update the Notion page and keep the re-test report.
9. **Report back** with the Notion link, what changed, what was masked, and anything Eric should decide before publishing (e.g. sensitive statements such as terms-of-service grey areas).

## Anti-patterns

- Sales tone: "最看重", "花时间最多" are fine as facts; "重磅", "颠覆", "强大" are not.
- Colloquial shortcuts that read as hype even when accurate (它很脆 → CLI 升级或重启后权限会失效).
- Listing features without the loop that shows them working.
- Mixing Chinese into diagrams, or drawing diagrams that only work for one language.
- Publishing without an explicit instruction, or writing real names, because "it is just a draft".
- Dangling diagram nodes with no path back to the user.
- Hard-coding current model names, vendors, or thresholds that will change next month.
- Answering from memory about the project instead of reading its docs.
