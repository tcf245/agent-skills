---
name: obsidian-llm-wiki-lint
description: Use when the user requests a wiki health check, asks to "clean up the knowledge base", or as a periodic sweep. Finds broken links, naming issues, missing stub pages, and stale content. Requires obsidian-llm-wiki-methodology.
type: workflow
triggers:
  - "LINT"
  - "wiki health check"
  - "clean up the knowledge base"
  - "wiki maintenance"
platforms: [cc, codex, gemini]
---

# LINT Operation

Sweep the vault for inconsistencies and rot. Fix or report.

## Procedure

### 1. Scope decision
- Default scope: the entire vault.
- If the user names a subdir (`wiki/concepts/`), scope to that.

### 2. Run the checks (in order)

#### A. Broken wikilinks
- Grep for `[[<text>]]` patterns. For each, confirm the target page exists.
- For each broken link, decide:
  - **Rename mismatch** → fix the link.
  - **Genuine missing page** → create a stub with frontmatter and a one-line "TODO: expand" body.
  - **Stale link** (target deleted intentionally) → remove the link.

#### B. Naming convention violations
- All filenames in `wiki/` are Title Case (concepts) or Proper Name (entities).
- No double-extension files (e.g., `CLAUDE.md.md`).
- Records are date-prefixed (`YYYY-MM[-DD] <topic>.md`).

#### C. Frontmatter completeness
- Every wiki page has `title`, `tags`, `created`, `status`.
- `status: stub` pages older than 60 days are reported for follow-up — they may have been forgotten.

#### D. Orphans
- Wiki pages with zero backlinks may be candidates for merge or deletion. List them; do not auto-delete.

#### E. index.md / log.md drift
- `index.md` should list every wiki page. Find pages missing from the index and add them.
- `log.md` should chronologically cover every INGEST / LINT / GRAPH run. If a recent INGEST is missing, add a back-dated entry from git/file timestamps.

#### F. Stale concept pages
- Look for concept pages whose claims reference dated events (e.g., "the latest version is X"). Flag for rewording to remove time-bound phrasing.

### 3. Report and act
- For each finding, apply automatic fixes where unambiguous (rename mismatches, missing index entries, naming-convention fixes).
- For judgment calls (orphan deletion, stub expansion, stale concept rewording), present a list to the user and wait for direction.
- Append a `LINT` entry to `log.md` summarizing what was fixed and what's outstanding.

## Anti-patterns

- **Auto-deleting orphans.** A page with no backlinks today may be load-bearing tomorrow once the relevant concept is ingested. Always confirm.
- **Reformatting stylistic choices.** LINT fixes broken/wrong things, not different things.
- **Running LINT after every edit.** Once a week is plenty for a vault that's actively maintained.
