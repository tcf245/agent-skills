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
4. **Never tick `Published`.** Create or update the page with `Published = __NO__`. Eric reviews and publishes. Only tick it if he says so in the current session.
5. **Every key choice gets its reason.** Write the decision, then 原因/为什么 in one or two sentences, grounded in the source (a design doc, a feedback entry, a real incident). No invented reasons.
6. **Facts come from sources.** Numbers (commits, dates, counts, limits) are looked up, not remembered. Separate shipped from not-yet-built from not-yet-verified; say so plainly.
7. **Run the de-AI-tone pass** (`lieflat-less-ai-tone` skill) on every draft, following its own workflow: detect, give the report, wait for Eric's reply, then rewrite and re-test.

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
7. **De-AI-tone pass** (hard rule 7). Deliver its report and stop until Eric replies. After the rewrite, update the Notion page and keep the re-test report.
8. **Report back** with the Notion link, what changed, what was masked, and anything Eric should decide before publishing (e.g. sensitive statements such as terms-of-service grey areas).

## Anti-patterns

- Sales tone: "最看重", "花时间最多" are fine as facts; "重磅", "颠覆", "强大" are not.
- Colloquial shortcuts that read as hype even when accurate (它很脆 → CLI 升级或重启后权限会失效).
- Listing features without the loop that shows them working.
- Mixing Chinese into diagrams, or drawing diagrams that only work for one language.
- Publishing, or writing real names, because "it is just a draft".
- Answering from memory about the project instead of reading its docs.
