# agent-skills

A cross-platform skill collection for AI coding agents — write your working habits once, run them on **Claude Code**, **Codex CLI**, and **Gemini CLI**.

If you switch between agents, each one forgets your conventions: how you plan, when you do TDD, which diagram tool to use, how you organize your notes. This repo packages those **process methodologies** as portable skill files that every agent can load.

## Design philosophy

- **Methodology only, no data.** Code, notes, and secrets stay where they are. Skills only describe *how* to work.
- **One source of truth, three platforms.** Skills are written once in Anthropic's markdown-with-frontmatter format; a build script generates `dist/AGENTS.md` (for Codex) and `dist/GEMINI.md` (for Gemini CLI). Claude Code consumes the files directly.
- **Lazy load by default.** On every platform, the agent reads only the skill it needs for the current task, not the entire ruleset upfront. The generated index tells the agent *when* to read each file.

## What's included

| Category | Skills | Trigger examples |
|----------|--------|------------------|
| **Coding** | `plan-mode`, `tdd-workflow`, `verification-before-completion`, `systematic-debugging` | `/plan`, "implement X", "bug" |
| **Collaboration** | `diagram-tier-selection`, `parallel-tasks`, `brainstorm-spec-plan-implement` | "draw a diagram", "in parallel", "let's build" |
| **Communication** | `language-mirroring`, `multilingual-coaching` | always-on |
| **Obsidian LLM Wiki** | `methodology`, `ingest`, `lint`, `graph`, `capture` | `INGEST`, `LINT`, `GRAPH`, `CAPTURE` |
| **Media** | `quark-resource-search` | "find resource", "organize this folder" |
| **Vendored (3rd party)** | `superpowers-*` (×7), `karpathy-guidelines` | various — see `dist/AGENTS.md` |

See `dist/AGENTS.md` or `dist/GEMINI.md` for the full machine-readable index.

## Install

```bash
git clone https://github.com/tcf245/agent-skills.git ~/workspace/agent-skills
cd ~/workspace/agent-skills
./scripts/install.sh <cc|codex|gemini|all>
```

Per-platform behavior:

### Claude Code
- Symlinks `skills/` into `~/.claude/skills/agent-skills/` (lazy-load via the `Skill` tool)
- Splices `dist/CLAUDE.md` into `~/.claude/CLAUDE.md` (eager-load index — works on a new machine before the symlink, and survives multi-device setups via Anthropic account sync)
- Restart Claude Code to pick up the new skills
- For vendored content, prefer installing the original plugins (`claude plugins install superpowers` etc.) — they're always fresher than this repo's snapshot

### Codex CLI
- Splices `dist/AGENTS.md` into `~/.codex/AGENTS.md` (or `$CODEX_AGENTS_FILE`)
- Publishes `skills/` and `vendored/` as symlinks under `~/.config/agent-skills/` (or `$AGENT_SKILLS_HOME`)
- The agent reads skill files on demand using its Read tool

### Gemini CLI
- Splices `dist/GEMINI.md` into `~/.gemini/GEMINI.md` (or `$GEMINI_AGENTS_FILE`)
- Same publish behavior as Codex

Install is **idempotent** — re-running replaces the agent-skills block (delimited by `# === agent-skills BEGIN / END ===`) without touching the rest of your config.

## Layout

```
skills/             ← Self-authored skills (source of truth)
  _schema.md        ← Skill file format documentation
  coding/           ← TDD, plan-mode, debugging, verification
  collaboration/    ← Diagram tiers, parallel tasks, pipeline
  communication/    ← Language mirroring, error coaching
  obsidian-llm-wiki/ ← Karpathy-style knowledge base ops
  media/quark-resource-search/ ← Movie/TV resource search + Alist organize
vendored/           ← Verbatim snapshots of third-party skills (MIT) with attribution
dist/               ← Generated AGENTS.md / GEMINI.md (committed; CI verifies in-sync)
scripts/            ← build / install / lint
.claude-plugin/     ← Plugin manifest for Claude Code marketplace
```

## Fork & customize

Skills are short — most are under 200 lines. To make this repo yours:

1. **Fork** on GitHub.
2. **Edit `skills/*.md`** — change wording, add your own rules, remove what doesn't fit. Each skill is independently editable; don't be afraid to make it personal.
3. **Add platform-specific values** under `config.example.yml`-style files for each skill that needs configuration. Copy `*.example.*` to `*.local.*` (gitignored) and fill in your own paths/credentials.
4. **Re-run `./scripts/build.sh`** so `dist/` matches your edits, then commit.
5. **Run `./scripts/lint.sh`** before pushing — it catches accidental personal data leaks.

If you write a new skill, follow the schema documented in `skills/_schema.md`. The build script picks it up automatically.

## CI

CI runs on every push/PR to `main`:

1. `./scripts/lint.sh` — sensitive-data scan + frontmatter completeness
2. `./scripts/build.sh` — regenerates `dist/`
3. `git diff --exit-code dist/` — ensures the committed `dist/` is in sync with `skills/`

If you edit a skill and forget to rebuild, CI catches it.

## Sensitive data — what's NOT in this repo

By design:

- No personal emails, credentials, API keys, or tokens
- No real paths beyond `${VAULT_PATH}`-style placeholders
- No personal data (watch lists, wiki content, interview notes)

The lint script enforces these via blacklist patterns. See `scripts/lint.sh`.

If you fork and your edits introduce personal data, keep it in:
- `*.local.json` / `*.local.yml` (gitignored)
- A separate private repo

## License

MIT. See [LICENSE](LICENSE).

Vendored third-party skills retain their own licenses (also MIT) — see [`vendored/README.md`](vendored/README.md) for attribution.
