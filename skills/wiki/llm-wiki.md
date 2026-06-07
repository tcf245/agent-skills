---
name: llm-wiki
description: >-
  LLM Wiki knowledge base management skill for Eric's personal Obsidian vault.
  Trigger when the user says INGEST / LINT / GRAPH / CAPTURE, drops a new raw
  article or file to process, asks to add something to the wiki, wants a health
  check, or when conversation produces a valuable insight worth archiving.
  Also trigger on: "add to wiki", "save to knowledge base", "update wiki",
  "run INGEST", "run LINT", "is X in the wiki", "clean up the knowledge base",
  "加到 wiki", "存到知识库", "更新 wiki", "做 INGEST", "跑 LINT".
---

# LLM Wiki — Management Skill

Operating protocol for Eric's personal Obsidian knowledge base, built on Andrej Karpathy's LLM Wiki methodology.

---

## Vault Location

```
iCloud primary:    ${LLM_WIKI_PATH}
Workspace mirror:  ${LLM_WIKI_MIRROR_PATH}    ← snapshot/mirror side, not the primary write target
Git repo:          ${LLM_WIKI_REPO_PATH}      (tracks snapshot/Notes/)
Snapshot script:   ${LLM_WIKI_SNAPSHOT_SCRIPT}  (launchd, runs daily at 23:00)
```

> **Never run snapshot.sh manually** unless the user explicitly asks.
>
> **Read/write priority:** use the iCloud primary vault first for normal wiki operations. Use the workspace path only when working with the git-tracked snapshot/mirror or repo-local scripts.

For local setup, copy `config.example.yml` to a local config file outside git or
export the variables above in the agent environment.

---

## Session Bootstrap Order

```
1. README.md    ← operating protocol overview
2. index.md     ← full vault catalog; decides which pages to load
3. on-demand    ← only the wiki pages relevant to the current task
4. schema.md    ← only when creating a new page or running LINT
5. log.md       ← only when tracing historical decisions
```

Goal: build a global view with minimum tokens. **Scan index.md first, load individual pages on demand.**

---

## Scripts (run these before calling LLM)

| Script | What it does | When to use |
|---|---|---|
| `bash bin/lint.sh` | Automated checks: broken links, missing frontmatter, index sync, orphans, `.md.md` | Before any LINT session — run first, pass report to LLM |
| `bash bin/ingest-pending.sh` | Lists raw/ files not yet ingested | Before INGEST — find what needs processing |
| `python3 attachments/diagrams/generate_canvas.py` | Regenerate architecture canvas | GRAPH only — never auto-run |
| `bash bin/snapshot.sh` | Sync iCloud vault to git | **Never run manually** — launchd runs at 23:00 |

Scripts live in `bin/`. Python 3 required.

---

## The Four Operations

| Op | Actor | Trigger | What happens |
|---|---|---|---|
| **CAPTURE** | Human | You find something worth keeping | Land a file in `raw/` — web clip, manual notes, paste, AI-generated draft |
| **INGEST** | LLM | After CAPTURE, or when insight surfaces mid-conversation | Read raw → extract entities + concepts → write/update `wiki/` pages → wire `[[wikilinks]]` → update `index.md` + `log.md` |
| **LINT** | Script + LLM | Periodic (weekly-ish) | Run `bin/lint.sh` first for mechanical checks → pass report to LLM for judgment calls (stub rot, contradictions, status honesty) |
| **GRAPH** | LLM | On-demand (presentations, exports) | Generate a curated visualization (`.canvas`, SVG, PNG); **never auto-regenerate** |

---

### CAPTURE vs INGEST terminology

Eric often uses **INGEST** as the umbrella term for adding knowledge to the
wiki. Use **CAPTURE** for insights that emerge inside the current conversation
and **INGEST** for processing saved external/raw sources. When a conversation
produces durable knowledge, treat it as a CAPTURE-style INGEST: distill the
conversation result directly into the wiki without requiring a separate raw
file.

### Automatic conversation-capture hook

At natural stopping points in a long conversation, proactively evaluate whether
the discussion produced durable knowledge worth preserving. Capture when one or
more of these are true:

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

Do not capture generic public facts, one-off answers, unresolved explorations,
or interesting but non-operational asides. If the value is obvious and enough
context is present, perform the capture. If it is borderline, briefly propose it
and ask for confirmation. Prefer fewer, higher-signal pages over noisy
accumulation.

---

## INGEST — Step by Step

1. **Check pending**: `bash bin/ingest-pending.sh` — see which raw files need processing
2. Read `raw/<source-file>` — never modify it
3. Identify entities (specific things) and concepts (patterns / theories)
4. For each item:
   - **Create new** or **update existing** page in `wiki/entities/` or `wiki/concepts/` or `wiki/records/`
   - Write YAML frontmatter (see Schema section below)
   - Cross-link to related existing pages using `[[wikilinks]]`
5. Append entries to `index.md` under the correct section
6. Append a line to `log.md`:
   ```
   ## [[YYYY-MM-DD]] INGEST | Short Title
   - Created: Page A, Page B
   - Updated: Page C (added section X)
   - Source: raw/filename.md
   ```

### Updating an existing page vs creating new

- **Record pages** (e.g. interview prep, ongoing projects): **update in place** — append new sections, update status table, do not create duplicates
- **Concept/entity pages**: update if new info is additive; create new if the insight is a distinct topic

---

## LINT — Validation Checklist (report findings before fixing)

1. **Broken links** — any `[[Page]]` where the file doesn't exist?
2. **Naming drift** — same concept referenced as both `[[DGS]]` and `[[Domain Graph Service (DGS)]]`?
3. **Orphan pages** — pages with no inbound `[[wikilinks]]` from any other page?
4. **Stub rot** — any `status: stub` page untouched for 30+ days?
5. **Index sync** — every file under `wiki/` listed in `index.md`? Every `index.md` entry actually exists?
6. **Frontmatter completeness** — missing `title`, `tags`, `created`, or `status` on any page?
7. **Status honesty** — pages marked `refined` that are visibly skeletal → demote to `stub`
8. **Double-extension bug** — any file with a `.md.md` suffix?
9. **Contradictions** — same claim stated differently in two pages → flag for human review
10. **Raw-source integrity** — no files under `raw/` have been modified (LLM is forbidden from touching them)

---

## Page Schema

### Concept page
```yaml
---
title: Page Name          # REQUIRED; should match H1
tags:
  - concept
  - <domain-tag>          # e.g. knowledge-management, ai-agents, infra
created: YYYY-MM-DD       # REQUIRED
status: stub | refined | active
source: "[[raw-source]]"  # OPTIONAL
---
```

### Entity page
```yaml
---
title: Netflix Engineering
tags:
  - entity
  - company               # or: person, tool, project, place
  - engineering-blog
created: YYYY-MM-DD
status: active
---
```

### Status semantics

| Status | Meaning |
|---|---|
| `stub` | Skeleton page — title, one-line summary, TODO markers. Acceptable as a cross-link target before full content lands. |
| `refined` | Complete enough to read standalone. Canonical sections filled. Safe to cite. |
| `active` | Live, regularly updated page tied to ongoing work (e.g., interview prep). |

When in doubt, prefer `stub` over `refined`. Overstating maturity makes LINT less useful.

---

## Naming Rules

- **Title Case with spaces** (not dashes): `AI Agent.md`, `LLM Wiki.md`
- **Disambiguation suffix in parentheses** for collisions: `Agent-Computer Interface (ACI).md`
- **Escape the `.md.md` bug**: if a concept name contains a dot (e.g. `AGENTS.md`), use a dash in the filename: `Codex-md.md`
- **Forbidden in filenames**: `:` (macOS path issues) — use ` — ` or parentheses instead

---

## Cross-Linking Rules

| Form | When to use |
|---|---|
| `[[Page Name]]` | Default. Obsidian resolves it; Graph View tracks the edge. |
| `[[Page Name\|alias]]` | When surrounding prose reads better with a different noun. |
| `[Text](./relative/path.md)` | Rare — only for links outside `wiki/` (e.g., to `README.md`). Graph View ignores these. |

- **First mention** of any wiki-covered concept/entity in a page → add a link
- Subsequent mentions in the same page → plain text is fine
- **"Related" section** at the bottom → 3–6 closest neighbors, not exhaustive

---

## Visualization — Three Layers

1. **Obsidian Graph View** (`Cmd+G`) — zero maintenance, auto-rendered from every `[[wikilink]]`. Do not duplicate it with custom diagrams.
2. **Architecture canvas** — `attachments/diagrams/knowledge-network.canvas`. High-level domain map: 1 META block + 5 domain cards with entry-point wikilinks. **Regenerate only when a new top-level knowledge domain is added** — not on every INGEST.
3. **Graphviz snapshot** — `attachments/diagrams/knowledge-network.png`. For slides/PDFs only; on-demand.

Regenerate the architecture canvas:
```bash
python3 attachments/diagrams/generate_canvas.py
```

---

## Knowledge Domains (index.md sections)

When creating pages, classify them into the correct `index.md` section:

| Domain | Examples |
|---|---|
| AI & Agents | Agent Loop, Context Engineering, Subagents, Plan Mode |
| Distributed Systems | Saga Pattern, Kafka, State Machine, Kubernetes |
| Recommendation Systems | Dual Encoder, Sequential Recommendation |
| Interview & Career | System Design Framework, Payment System Design |
| Japan & Career | Japan IT Company Comparison, Japan PR Application (HSP), Japan Relocation |
| Entities | Companies, people, tools |
| Records | Interview prep, ongoing projects (time-bound, personal) |

**Japan & Career** is a growing domain (2026): job research, immigration strategy, relocation logistics. Classify new pages here when they relate to working or living in Japan.

---

## LLM Behavior Rules

1. **At the start of every session** — scan `index.md` to check whether the task touches existing knowledge.
2. **When a valuable insight surfaces mid-conversation** — proactively propose an INGEST.
3. **When citing wiki content** — always use `[[wikilinks]]`; Obsidian's Graph View depends on them.
4. **After any change** — keep `index.md` and `log.md` in sync.
5. **Never modify anything under `raw/`** — it is the immutable source of truth.
6. **Before running LINT** — always run `bash bin/lint.sh` first; only call LLM for judgment calls flagged in the report.

---

## Key Files at a Glance

| File | Purpose |
|---|---|
| `README.md` | Operating protocol + directory layout |
| `index.md` | Full vault catalog; LLM reads this first |
| `schema.md` | Naming and frontmatter rules |
| `log.md` | Append-only action log |
| `wiki/concepts/` | Patterns, theories, methodologies |
| `wiki/entities/` | Specific people, orgs, tools, projects |
| `wiki/records/` | Time-bound personal records (interview prep, projects) |
| `attachments/diagrams/` | LLM-generated diagrams |
| `raw/` | Immutable source material (read-only) |
| `bin/lint.sh` + `bin/lint.py` | Automated LINT checks |
| `bin/ingest-pending.sh` + `bin/ingest_pending.py` | Find unprocessed raw files |
| `bin/snapshot.sh` | Daily vault sync to git (launchd, do not run manually) |
