---
name: obsidian-llm-wiki-methodology
description: Use when working with an Obsidian vault organized as an LLM-collaborative knowledge base (Karpathy-style). Defines the three-layer directory decision, schema, naming, and the snapshot model. Read this first before any INGEST / LINT / GRAPH / CAPTURE operation.
type: domain
triggers:
  - "INGEST"
  - "LINT"
  - "GRAPH"
  - "CAPTURE"
  - "add to wiki"
  - "save to knowledge base"
  - "update wiki"
platforms: [cc, codex, gemini]
---

# Obsidian LLM Wiki — Methodology

An LLM-collaborative knowledge base built in Obsidian. The agent is the *programmer*, Obsidian is the *IDE*, the vault is the *codebase*. The goal is a compounding personal knowledge graph — every conversation that produces durable insight adds a node or edge.

## Conversation Capture Policy

Treat CAPTURE as the conversation-native form of INGEST. Eric may use "INGEST"
as the umbrella term for both external-source ingestion and conversation-derived
knowledge capture.

After multi-turn conversations, proactively decide whether the conversation
produced knowledge worth adding to the wiki. Preserve knowledge that is hard for
a public LLM to reconstruct later: internal/work context, company or team
knowledge, repo-specific conventions, local development workflows, personal
preferences, or reusable decisions. Also preserve public-domain topics when the
conversation fused them with Eric's own questions, clarifications, trade-offs,
and conclusions into a reusable personal understanding.

Do not preserve generic public facts, one-off answers, unresolved explorations,
or material that is easy to regenerate and contains no Eric-specific judgment.
When the value is clear, proceed with CAPTURE/INGEST. When borderline, ask for a
short confirmation before writing.

## Configuration

Read these values from `skills/obsidian-llm-wiki/config.example.yml` (or the user's local override):

- `VAULT_PATH` — absolute path to the vault root
- `PRIMARY_SYNC` — `iCloud` / `local` / `git` (affects where the canonical files live)
- `SNAPSHOT_TIME` — when the daily snapshot cron fires (default `23:00`)

Never hardcode paths in skills; always resolve them via config.

## Directory Structure

```
${VAULT_PATH}/
├── raw/                 ← Immutable source articles (read-only after INGEST)
│   └── assets/          ← Images extracted from raw sources
├── wiki/
│   ├── concepts/        ← Abstract, timeless knowledge: patterns, theories
│   ├── entities/        ← Named concrete things: people, orgs, tools, places
│   └── records/         ← Time-bound personal records: sessions, debriefs, designs
└── attachments/
    └── diagrams/        ← LLM-generated diagrams (.canvas, .png, .svg)
```

## The Three-Layer Decision Tree

When deciding where a new wiki page goes, ask these three questions in order:

1. **Is it time-bound** (a specific session, debrief, dated event)? → `records/`
2. **Is it a named concrete thing** (a company, a tool, a person, a place)? → `entities/`
3. **Otherwise** → `concepts/`

`records` may reference `concepts` and `entities`. The reverse is not allowed — concepts and entities must stay timeless and reusable.

## Key Files (vault-level metadata)

- `index.md` — Content catalog with one-line description per page. The agent reads this FIRST when starting any wiki operation. Keep entries terse.
- `log.md` — Append-only chronological operation log. Format: `## [[YYYY-MM-DD]] OPERATION | Title`
- `schema.md` — Naming conventions and rules (per-vault customization of this skill).
- `README.md` — Workflow guide; mostly points to INGEST / LINT / GRAPH skills.

## Naming Conventions

- Concept files: `Title Case.md` (e.g., `AI Agent.md`).
- Entity files: `Proper Name.md` (e.g., `Netflix Engineering.md`).
- Avoid double-extension bugs: a page about CLAUDE.md should be named `CLAUDE-md.md`, not `CLAUDE.md.md`.
- Records: prefix with `YYYY-MM-DD ` or `YYYY-MM ` for date-only granularity, then the topic.

## Frontmatter (required on every wiki page)

```yaml
---
title: <page title>
tags: [<topic>, <topic>]
created: YYYY-MM-DD
status: stub | refined
---
```

`status: stub` is the default for new pages. Promote to `refined` only after a real second pass with cross-links.

## Cross-Links

Use Obsidian wikilink syntax: `[[Page Name]]`. Prefer linking through canonical filenames; alias display text with `[[Page Name|alt text]]` when prose flow needs it.

## Sync & Snapshot Model

- The vault syncs across devices via the configured `PRIMARY_SYNC` (often iCloud for solo users).
- A daily `bin/snapshot.sh` cron (typically at `SNAPSHOT_TIME`) writes a read-only snapshot under `snapshot/Notes/` that is tracked by git. This gives version history without putting the live vault into git directly.
- **The agent does not run `snapshot.sh` manually after every edit.** The cron handles it. Only run on explicit user request.

## Visualization Conventions

Three view layers; each is maintained differently:

1. **Obsidian Graph View** (`Cmd+G` in the app) — live, exhaustive, zero maintenance. Do NOT duplicate it with custom diagrams.
2. **Architecture canvas** (`attachments/diagrams/knowledge-network.canvas`) — curated, high-level domain map: a small number of domain cards plus entry-point wikilinks. Regenerate only when top-level domains change, not on every INGEST.
3. **Static graph snapshot** (`attachments/diagrams/knowledge-network.png`) — on-demand export for slides or sharing.

A previous version of the architecture canvas enumerated every concept page; that was wrong because it duplicated Graph View for free. The curated canvas earns its keep only at the *abstraction* layer.

## Anti-patterns

- **Linking concepts back to records.** Records are downstream consumers; the reverse coupling makes concepts dated.
- **Putting personal context into a concept page.** Concept pages should be reusable by anyone with similar background; personal context belongs in records.
- **Renaming a page without updating backlinks.** Use Obsidian's "Update Backlinks on Rename" feature, then run LINT.
- **INGEST-ing the same article twice.** Check `raw/` and `log.md` before processing a new source.
