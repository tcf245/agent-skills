---
name: obsidian-llm-wiki-capture
description: Use when the current conversation produces a valuable, durable insight that should be archived to the wiki, including proactively at natural stopping points after multi-turn conversations. Captures the insight as a new concept page, extends an existing one, or records a session-specific conclusion. This is the conversation-native form of INGEST.
type: workflow
triggers:
  - "CAPTURE"
  - "save this insight"
  - "archive this to wiki"
  - "this should be in the knowledge base"
  - "valuable insight"
  - "durable knowledge"
  - "conversation produces reusable knowledge"
  - "conversation-native INGEST"
platforms: [cc, codex, gemini]
---

# CAPTURE Operation

Archive a conversation-generated insight to the wiki.

## When to use this vs INGEST

- **INGEST**: external raw article / video / chat log already saved to `raw/`.
- **CAPTURE**: insight that emerged *within* this conversation — no external source file.

Eric often uses "INGEST" as the umbrella term for both operations. Treat
conversation-derived knowledge capture as a CAPTURE-style INGEST: distill the
conversation result directly into the wiki without requiring a separate raw
source file.

## Automatic Capture Hook

At natural stopping points in a long conversation, evaluate whether the
discussion produced durable knowledge worth preserving. Do this proactively; do
not wait for the user to say `CAPTURE` or `INGEST`.

Capture when one or more of these are true:

- **Private or hard-to-reconstruct context**: company/internal knowledge, work
  setting details, team conventions, repo-specific practices, local workflows,
  personal operating preferences, or process knowledge that a public LLM would
  not know.
- **Public knowledge transformed by Eric's thinking**: the topic is public, but
  the conversation resolved Eric's specific doubts, compared alternatives,
  captured boundary conditions, or produced a reusable personal framing rather
  than a generic explanation.
- **Future work leverage**: the conclusion is likely to be reused in coding,
  architecture, decision-making, communication, research, or future agent
  behavior.
- **Stable rule or heuristic**: the conversation produced a decision rule,
  threshold, checklist, taxonomy, or workflow that should guide later sessions.

Do not capture when the result is only:

- A generic public fact that can be fetched or regenerated on demand.
- A one-off answer for the current moment with no likely reuse.
- An unresolved exploration where no stable conclusion has emerged.
- A vague opinion, rant, or interesting aside without operational value.

If the value is obvious and enough context is present, perform the capture. If
the value is plausible but borderline, briefly propose the capture and ask for
confirmation. Prefer fewer, higher-signal pages over noisy accumulation.

## Procedure

### 1. Confirm the insight is durable
Ask yourself (not the user — they already decided):
- Will this be useful in a different conversation a month from now?
- Is it specific enough to act on, or just a vague observation?
- Could it be derived trivially from existing wiki pages? (If yes, don't duplicate.)
- Does it encode Eric-specific context, judgment, or workflow that future agents
  should reuse?

If durable, proceed. If not, suggest the user just keep it in chat.

### 2. Decide the target page
- New concept page if the insight is a *new* abstract pattern, theory, or technique.
- Extension of an existing concept page if it sharpens or adds nuance to something already in the wiki.
- A record page if the insight is tied to a specific session, project decision,
  repo, team, or personal workflow.

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
