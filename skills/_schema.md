# Skill File Schema

Every skill file under `skills/` must follow this format.

## Frontmatter (required)

```yaml
---
name: <kebab-case-id>                     # Must match the file name without .md
description: <one-line trigger sentence>  # Used by index generators; should start with "Use when..." or similar
type: workflow | behavior | domain        # See definitions below
triggers:                                 # List of conditions that invoke this skill
  - "/plan"                               # Slash command (Claude Code style)
  - "make a plan"                         # Natural language phrase
  - "<task type>"                         # Or a category like "implementing feature"
platforms: [cc, codex, gemini]            # Subset; omit a platform to skip it in build
---
```

### Type definitions

- **workflow** — A multi-step procedure the agent follows for a specific task (e.g., `plan-mode`, `tdd-workflow`, `ingest`).
- **behavior** — A persistent rule the agent applies across many tasks (e.g., `language-mirroring`, `verification-before-completion`).
- **domain** — Subject-matter knowledge for a specific area (e.g., `obsidian-llm-wiki/methodology`).

## Body

After the frontmatter, the skill body is plain Markdown. Recommended structure:

1. **`# Title`** — Human-readable name
2. **One-paragraph summary** — What this skill does and when it kicks in
3. **The actual rules / steps / procedure**
4. **Examples** (optional) — concrete cases
5. **Anti-patterns** (optional) — what NOT to do

## Cross-platform notes

- Write the body so it makes sense **without** Claude Code's `Skill` tool. The Codex and Gemini index generators include the skill body as-is.
- Refer to "the agent" or "you" rather than "Claude" — keeps the skill platform-agnostic.
- If a rule is Claude-Code-only (e.g., references the `Skill` tool, `Agent` tool, or hooks), put it under a section labeled `## Claude Code specifics` so other platforms can ignore it.

## Naming rules

- File path: `skills/<category>/<name>.md` for single-file skills.
- Multi-file skills: `skills/<category>/<name>/SKILL.md` plus supporting files in the same directory.
- `name` in frontmatter equals the file basename (or the directory name for multi-file skills).
