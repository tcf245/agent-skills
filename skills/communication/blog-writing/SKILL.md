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
   - Titles state the subject plainly and read like a person named the post: short, no stacked clauses. `你好：这个博客为什么建，以及怎么搭起来的` read as machine-made to Eric (2026-11-22: 怎么看都不像人类写出来的，读起来也别扭); avoid the `X：A，以及 B` pattern. Shorter is fine: for that post Eric chose plain `Hello` over the agent's `博客搭好了，先打个招呼`. Give Eric two alternatives in the report.
   - Describe what the thing does and why, in plain declarative sentences. Let facts carry weight; do not add adjectives to sell them.
   - **Colloquial, not formal (Eric, 2026-11-24):** 中英文最好都要口语化一点，去除 AI 味。Write the way Eric would tell a friend about it: short sentences, first person, everyday words. Calm is not stiff: drop 书面套话 ("值得注意的是", "综上所述", "in conclusion", "it is worth noting") as firmly as slang.
2. **Privacy masking.** No real names of Eric, family members, or other people in the body or diagrams; write 我, 家人, 一位家庭成员, 家里人. Also leave out personal domains, Discord/Notion IDs, emails, account numbers, children's details, and anything from health or finance records. When unsure, mask it and mention it in your report.
3. **Diagrams and code blocks contain no Chinese.** Diagram text, code, commands and config in code blocks are English in both language versions, so one set of images and code serves both. Inline prose quotes in Chinese belong in the text, not in a code block.
13. **Every post ends up in Chinese and English, Chinese first (Eric, 2026-11-22; order changed 2026-11-24).** Write only the Chinese version first and go through Eric's feedback rounds on it. When he says the Chinese is final (定稿), write the English version from that final text (Eric, 2026-11-24: 默认先写中文，我反馈几个回合，最后定稿了以后再去输出英文). A page never mixes languages: `/zh` lists only `zh` pages and `/en` only `en` pages, so the English page follows soon after the final Chinese one: same `Slug`, `Date` and `Tags`, `Lang` `en`, images reused, captions translated; natural English, not word for word. Eric publishes them, ideally together. A revision after both exist is applied to both. Before telling Eric the pair is ready, run `keychain-secret run .env.keychain -- npm run check:content` in `~/workspace/blog` (lists slugs not yet in the other language; fails on broken rows or CJK in a code block). Product names that exist only in Chinese (a Discord role name, a UI label) are described in English, not left in Chinese; list them in the report.
4. **Publish only on an explicit instruction.** Create or update the page with `Published = __NO__` by default. Tick it when Eric clearly says to publish (from the phone counts too), then confirm the live URL returns 200 (see `references/notion-blog.md`).
5. **Every key choice gets its reason.** Write the decision, then 原因/为什么 in one or two sentences, grounded in the source (a design doc, a feedback entry, a real incident). No invented reasons.
6. **Facts come from sources.** Numbers (commits, dates, counts, limits) are looked up, not remembered. Separate shipped from not-yet-built from not-yet-verified; say so plainly. A repo's first commit is not when the project began: ask Eric or write "first commit" (the blog began in November 2025; its first commit is 2025-12-06).
7. **Reasonable abstraction (保持一点合理的抽象，不必要的细节避免太具体).** Describe capabilities and roles, not the current instance. Write "调度 agy 以及其他 agent（如 Codex）", not only "agy"; write "轻量 / 标准 / 高 档位", not specific model names; write "用量分档", not exact percentages. Keep a concrete detail only when it explains a decision (one real incident is enough). Details that are likely to change (model versions, thresholds, file names) stay out of the post.
8. **Logical closure (请考虑逻辑闭环).** Every component in a diagram must have a reason to exist in the flow: something goes in and something comes back. Before drawing, trace each node: who produces its input, where its output goes, and how the user gets the result. A node with no way back (e.g. a web page that is only an endpoint) means the diagram is missing an edge or the text is missing a loop. Use two-way arrows where the user both sends and receives.
9. **Real screenshots help understanding (有真实 case 贴图帮助理解).** For each capability that has a UI (cards, pushes, pages), add one real screenshot next to its explanation, with a one-paragraph caption saying what the reader is looking at. Before uploading, review every pixel and pixelate private data: personal domains and URLs, addresses and cities, health, finance, account or ID numbers, other people's details. Names follow Eric's instruction for that post (in the 2026-11-21 post he said names in screenshots may stay). Mention in the caption that parts are masked, and list what you masked in your report. Keep the screenshot's full resolution; it is the page, not the file, that shows it small (Eric, 2026-11-24: 保持分辨率，插入 blog 之后调整显示小一点，放大还能看清楚；the 2026-11-21 frames shrank the phone to about 450 px wide inside a 1600×1240 canvas and were too blurry). Optionally put it in a phone frame: `scripts/phone-frame.py shot.png out.png` keeps the screen at native pixels and hugs the phone with a small margin. The blog (PR #11, `phoneSizedFormat` in `lib/post-utils.ts`) shows any image taller than 1.2× its width at 360 px, centred, and a tap opens the full image. Check the frame on light and dark backgrounds (`magick out.png -background white -flatten preview.png`).
10. **Keep the facts current.** Check the latest state in the repo and with Eric before describing who does what (e.g. ops moved from `#admin` to `#projects` with an Engineer agent on 2026-11-21).
12. **详略得当: weight by importance (Eric, 2026-11-22, verbatim):** 注意一些写作上的技巧，在一个章节内，优先重点讲最重要的部分，着墨最多的应该是最重要的点。按照重要程度依次递减，详略得当。
   - Before writing a section, rank its points by how much they matter to the reader. The first point gets the most words; each later one gets less; the least important get one clause or are dropped.
   - Do not turn the chat history into the post (流水账). A decision log lists every choice at the same length; a post explains the few that shaped the result. Example from the hello post: the front-end section should spend most of its words on the starting point and the effect wanted, less on the logo, a sentence on fonts, and nothing on keeping Notion's coral inline-code colour.
   - Put this ranking in the writer's brief as an explicit order for each section.
11. **Run the de-AI-tone pass** (`lieflat-less-ai-tone` skill) on every draft, following its own workflow: detect, give the report, wait for Eric's reply, then rewrite and re-test.

## Who uses this skill (2026-11-24)

Blog writing belongs to the **博客编辑 persona in agent-crew's `#blog` channel** (`personas/blog.yaml`). Eric posts ideas there, and the reading partner forwards distilled `#reading` discussions with `archive_and_handoff(to="blog")`. The persona runs in the crew Pod with no Bash, Notion MCP or agy, so it differs from the workflow below in four places:

- Drafts live in the wiki at `wiki/records/blog/<slug>/zh.md` and `en.md` (frontmatter `title`, `slug`, `lang`, `date`, `tags`). The `blog_draft` board tool writes a file to Notion as an unpublished draft, replacing the page's content. It never publishes, refuses published posts, and refuses pages edited in Notion since its last save unless Eric says which version wins.
- It cannot run scripts: diagrams, masking and framing screenshots, `check:content`, and reading code repos go to admin through `admin_request`.
- The de-AI-tone pass is done by reading the rules, without the detector script.
- Eric's feedback goes into `wiki/records/Blog Writing Feedback.md`. Feedback that recurs is brought to admin to fold into this skill: the persona cannot write the skill (the skills mount is read-only), so admin maintains it.

Terminal sessions (admin, `#projects`) follow the full workflow below when Eric asks there.

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
7. **Use Gemini as a second writer or reviewer** (Eric, 2026-11-21: Gemini is good at text; use it). **Who writes long-term is not decided yet.** The agent-crew post came out about even between Claude (after 2–3 feedback rounds) and Gemini (first draft, but with that feedback in its brief), so Eric is running more trials. Next post is an agy-led trial: agy writes the first draft and takes Eric's feedback rounds; you build the brief, the diagrams, the screenshots, verify facts, and handle Notion. After each trial, add a case file under `references/` with the number of feedback rounds and the kinds of mistakes each writer made. Through the `agy-delegation` skill, hand agy a no-repo task with the sources, a brief that carries Eric's requests and feedback in his words, this skill and the de-AI-tone rules, plus a `check.py` acceptance script (placeholders present, banned words absent, length). For a comparison, do not give agy your own draft. agy cannot reach Notion; you upload its Markdown as a separate draft page (`<slug>-gemini`). For a review instead, give it your draft and ask for a list of concrete edits.
8. **De-AI-tone pass** (hard rule 11). Deliver its report and stop until Eric replies. After the rewrite, update the Notion page and keep the re-test report.
9. **Translate after 定稿, through agy** (hard rule 13; FB-056: text processing goes to agy). Only once Eric calls the Chinese final: fetch the final Chinese page, save its Notion Markdown to a file, and hand agy a no-repo task (`agy-delegation`): natural, colloquial English, not word for word, same section order, keep every `<image source=...>` line and translate only its caption, describe Chinese-only names in English, output one Markdown file; `verify` checks that the image lines match the source and that no CJK is left (`grep -P '[\x{4e00}-\x{9fff}]'` empty). Skim the result for meaning, then create the `en` page with the same Slug.
10. **Report back** with both Notion links, what changed, what was masked, and anything Eric should decide before publishing (e.g. sensitive statements such as terms-of-service grey areas).

## Anti-patterns

- Sales tone: "最看重", "花时间最多" are fine as facts; "重磅", "颠覆", "强大" are not.
- Colloquial shortcuts that read as hype even when accurate (它很脆 → CLI 升级或重启后权限会失效).
- Listing features without the loop that shows them working.
- Mixing Chinese into diagrams or code blocks, or drawing diagrams that only work for one language.
- Writing the English version before Eric calls the Chinese final, or leaving it undone after he does.
- Publishing without an explicit instruction, or writing real names, because "it is just a draft".
- Dangling diagram nodes with no path back to the user.
- Hard-coding current model names, vendors, or thresholds that will change next month.
- Answering from memory about the project instead of reading its docs.
