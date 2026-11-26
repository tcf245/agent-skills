# Skill File Schema

Every skill under `skills/` follows the native Agent Skills directory format (`skills/<category>/<name>/SKILL.md`) so Claude Code, Codex, pi, and Gemini/agy discover it natively.

## Frontmatter (required)

```yaml
---
name: <kebab-case-id>                     # Must match the skill directory name
description: <when-to-use sentence>       # Shown to the model by native discovery; state clearly when to invoke
type: workflow | behavior | domain        # Optional classification (see below)
triggers:                                 # Optional trigger phrases ("always-on" for persistent behaviors)
  - "<phrase or command>"
platforms: [cc, codex, gemini]            # Optional subset
---
```

### Type definitions

- **workflow** — A multi-step procedure the agent follows for a specific task (e.g., `agy-delegation`, `system-design-interview`).
- **behavior** — A persistent rule the agent applies across many tasks (e.g., `multilingual-coaching`).
- **domain** — Subject-matter knowledge and operating rules for a specific area (e.g., `llm-wiki`).

## Body

After the frontmatter, the skill body is plain Markdown. Keep prompts minimal:

1. **`# Title`** — Human-readable name
2. **One-paragraph summary** — What this skill does and when it kicks in
3. **The actual rules / steps / procedure**
4. **Anti-patterns** (optional) — what NOT to do

## Language

Write skill bodies (and descriptions) in English, the shared language every agent reads. Keep non-English text only for trigger phrases Eric types, verbatim quotes in quotes, and output examples in backticks or code blocks. Enforced by `scripts/lint.sh` section 7 (FB-078).

## Cross-platform notes

- Refer to "the agent" or "you" rather than a specific model name when possible.
- If a rule is Claude-Code-only, put it under a section labeled `## Claude Code specifics` so other platforms can ignore it.

## Naming rules

- Skill path: `skills/<category>/<name>/SKILL.md` (plus optional `config.example.yml`, `references/`, `scripts/` in the same directory).
- `name` in frontmatter must equal the directory name `<name>`.
