---
name: obsidian-llm-wiki-ingest
description: Use when the user drops a new raw article or asks to add content to the wiki. Extracts knowledge from a raw source, creates or updates concept / entity / record pages, and logs the operation. Requires obsidian-llm-wiki-methodology to be read first.
type: workflow
triggers:
  - "INGEST"
  - "add to wiki"
  - "save to knowledge base"
  - "process this article"
  - "add this raw file"
platforms: [cc, codex, gemini]
---

# INGEST Operation

Process a raw source into structured wiki pages.

## Preconditions

1. The methodology skill (`obsidian-llm-wiki-methodology`) has been read this session. If not, read it now.
2. The source file lives under `${VAULT_PATH}/raw/`. If the user pasted content inline, save it as a raw file first with a descriptive name (`raw/<topic-slug>.md`).

## Procedure

### 1. Locate or stage the raw source
- Confirm the raw file path. If the user gave a URL or pasted text, save it to `raw/` and note the source URL in the file's frontmatter.
- Read the raw file end to end. Do not skim.

### 2. Identify candidate wiki pages
- Extract the key ideas, named things, and dated events.
- Apply the three-layer decision tree for each:
  - Time-bound → `records/YYYY-MM[-DD] <topic>.md`
  - Named thing → `entities/<Proper Name>.md`
  - Abstract idea → `concepts/<Title Case>.md`
- Check `index.md` to see whether each candidate page already exists. **Reuse before creating.**

### 3. Update or create pages
- For existing pages: append new material, deduplicate with what's there, add cross-links to the raw source.
- For new pages: scaffold with the required frontmatter (status: `stub`), one-sentence summary, a "See also" section with backlinks.
- Concept and entity pages should remain *timeless* — phrase facts so they don't go stale.

### 4. Cross-link
- Every new wiki page links to at least one other wiki page (a related concept or entity) plus the raw source.
- Every record references the concepts it consumes.

### 5. Update vault metadata
- Add one-line entries to `index.md` for any new pages.
- Append an `INGEST` line to `log.md`:
  ```
  ## [[YYYY-MM-DD]] INGEST | <raw source title>
  - Created: [[New Concept]], [[New Entity]]
  - Updated: [[Existing Page]]
  ```

### 6. Report
- Tell the user: how many pages created, how many updated, which raw source was consumed.
- Do NOT run `snapshot.sh` — the daily cron handles snapshots.

## Quality bar

- **No phantom links.** Every `[[wikilink]]` you create must resolve. If you reference a page that doesn't exist yet, create at least a stub for it.
- **No duplicated knowledge.** If a concept already has a page, extend it instead of creating a near-duplicate.
- **Verifiable claims.** Concept pages cite the raw source for non-obvious facts.

## Anti-patterns

- **Treating INGEST as transcription.** The job is *extraction and organization*, not paraphrasing.
- **Creating one page per paragraph.** Aggregate; one page should cover one coherent idea.
- **Skipping the index.md and log.md updates.** Future-you will be unable to find what was ingested when.
