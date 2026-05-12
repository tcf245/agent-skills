---
name: obsidian-llm-wiki-capture
description: Use when the current conversation produces a valuable, durable insight that should be archived to the wiki. Captures the insight as a new concept page (or extends an existing one). Distinct from INGEST, which processes external sources.
type: workflow
triggers:
  - "CAPTURE"
  - "save this insight"
  - "archive this to wiki"
  - "this should be in the knowledge base"
platforms: [cc, codex, gemini]
---

# CAPTURE Operation

Archive a conversation-generated insight to the wiki.

## When to use this vs INGEST

- **INGEST**: external raw article / video / chat log already saved to `raw/`.
- **CAPTURE**: insight that emerged *within* this conversation — no external source file.

## Procedure

### 1. Confirm the insight is durable
Ask yourself (not the user — they already decided):
- Will this be useful in a different conversation a month from now?
- Is it specific enough to act on, or just a vague observation?
- Could it be derived trivially from existing wiki pages? (If yes, don't duplicate.)

If durable, proceed. If not, suggest the user just keep it in chat.

### 2. Decide the target page
- New concept page if the insight is a *new* abstract pattern, theory, or technique.
- Extension of an existing concept page if it sharpens or adds nuance to something already in the wiki.
- A record page if the insight is tied to a specific session or project decision (rare for CAPTURE — usually that's an INGEST of a debrief).

### 3. Distill
- Strip out the conversational scaffolding (questions, false starts, "let me think"s).
- State the insight as a standalone claim a future reader can use without the full chat history.
- Add a `Why this works` or `When this fails` section if the insight has known boundary conditions.

### 4. Write
- Follow the standard wiki page schema (frontmatter, title, body, cross-links, "See also").
- Status starts as `refined` (not `stub`) — CAPTURE only fires when the insight is already clear.
- Cross-link to the most related concepts that already exist.

### 5. Log
- Append to `log.md`:
  ```
  ## [[YYYY-MM-DD]] CAPTURE | <concept title>
  - Source: conversation (<short context>)
  - Created: [[Concept Name]]   OR   Extended: [[Concept Name]]
  ```
- Add to `index.md` if a new page was created.

## Anti-patterns

- **Capturing every interesting comment.** The wiki is a compounding asset; noise dilutes it.
- **Capturing rants or opinions as concepts.** Opinions go in records (and even then, sparingly).
- **Linking to the chat session.** Chat URLs rot; phrase the insight to be self-contained.
- **Writing the captured page in conversational prose.** It should read as documentation, not as a story.
