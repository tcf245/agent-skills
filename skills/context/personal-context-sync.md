---
name: personal-context-sync
description: Use when a task depends on Eric's personal background or when new personal facts appear in chat.
---

# Personal Context Sync

Use this skill whenever the conversation depends on Eric-specific personal context such as family structure, child details, home address, residence status, visa situation, employer, compensation band, or similar background facts.

## Source of truth

Read this page first:

`${LLM_WIKI_PATH}/wiki/records/Eric Personal Profile.md`

For local setup, copy the relevant example config or export `LLM_WIKI_PATH` in
the agent environment.

## Rules

1. Before answering a question that depends on Eric's personal background, read the profile page first.
2. If Eric provides new durable personal information or corrects an existing fact, update the profile page.
3. When you update the profile page, also update:
   - `index.md`
   - `log.md`
4. Keep personal facts in the profile page as documentation, not as scattered ad hoc notes.
5. If a conclusion is time-sensitive, record the assessment date in the destination page.

## Scope

This skill is for durable personal context, including:

- family members and child information
- residence and address
- country of residence and nationality
- visa / residence status
- employer, role, income band, and major career changes
- school / kindergarten information

## Do not do this

- Do not invent missing details.
- Do not overwrite a fact unless Eric explicitly corrects it or provides newer information.
- Do not store transient one-off facts here unless they are likely to matter in future sessions.
