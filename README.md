# agent-skills

Eric's personal AI agent skill collection in native Agent Skills format (`skills/<category>/<name>/SKILL.md`), discovered natively by **Claude Code**, **Codex CLI**, **pi**, and **Gemini / Antigravity (`agy`)**.

> **Target environment:** These skills target Eric's Mac and resolve concrete local paths (such as `/Users/eric/Library/Mobile Documents/iCloud~md~obsidian/Documents/LLM-Wiki` for the Obsidian vault). Secrets never live in this repo — they live in macOS Keychain via `keychain-secrets`.

## Design philosophy

- **Native discovery first.** Every skill is a directory (`skills/<category>/<name>/SKILL.md`) with a `name` matching the directory and a specific `description` telling the model when to load it.
- **Minimal always-on prompt.** `scripts/build.py` emits a tiny 3-line block in `dist/{CLAUDE,AGENTS,GEMINI}.md` containing only the always-on `multilingual-coaching` rule plus a one-line pointer to `~/.agents/skills` — no bloated triggered-skill index.
- **Keep prompts minimal.** Unused process skills and community duplicates are omitted in favor of built-in agent capabilities and Eric's own workflows.

## What's included

| Category | Skills | When to use |
|----------|--------|-------------|
| **Career** | `resume-coach`, `system-design-interview` | Resume review/rewrites and Google Docs updates; interview-grade system design with diagrams and wiki records |
| **Coding** | `agy-delegation`, `jev-prefilter`, `working-rules` | Delegate large well-scoped execution tasks to `agy`; pre-filter bulk logs/candidates with `jev`; always-on standing rules (fix mistakes with checks before prose, obey hooks, secrets in Keychain, push yourself, evidence before done) |
| **Communication** | `multilingual-coaching`, `blog-writing` | Always-on passive one-line corrections (`😇` English, `🌸` Japanese) at the end of replies; calm, masked, diagram-backed blog posts drafted into the Notion blog database |
| **Design** | `frontend-design`, `web-artifacts-builder`, `theme-factory`, `canvas-design`, `algorithmic-art` | Vendored unchanged from [anthropics/skills](https://github.com/anthropics/skills) @ `e4bb5d9` (each keeps its own `LICENSE.txt`): distinctive UI direction, multi-component React/Tailwind/shadcn pages, preset themes for pages and decks, posters and static art as PNG/PDF, p5.js generative art |
| **Context** | `personal-context-sync` | Read and maintain Eric's durable personal profile in the LLM Wiki |
| **Language** | `jlpt-n2-coach` | JLPT N2 mock-test OCR, error bank tracking, knowledge summaries, and targeted drills |
| **Media** | `quark-resource-search` | Search, filter, save, and organize Quark Cloud movie/TV resources with Alist |
| **Ops** | `keychain-secrets` | Manage secrets in macOS Keychain paired with the LLM Wiki pointer registry |
| **Wiki** | `llm-wiki` | `INGEST`, `LINT`, `GRAPH`, `CAPTURE`, and exam error-bank workflows for Eric's Obsidian vault |

## Install

```bash
git clone https://github.com/tcf245/agent-skills.git ~/workspace/agent-skills
cd ~/workspace/agent-skills
./scripts/install.sh all
```

Preview without modifying the filesystem:

```bash
./scripts/install.sh --dry-run all
```

What `scripts/install.sh` does:

1. **Canonical skill symlinks (`~/.agents/skills/<name>`):** For every skill directory under `skills/` containing `SKILL.md`, creates `~/.agents/skills/<name> -> ~/workspace/agent-skills/skills/<category>/<name>`. Any existing real directory of the same name is moved to `~/.agents/skills/.replaced-YYYYmmdd/<name>` first.
2. **Per-agent skill symlinks:** Creates `~/.claude/skills/<name> -> ~/.agents/skills/<name>` and `~/.gemini/skills/<name> -> ~/.agents/skills/<name>`.
3. **Legacy cleanup:** Removes the old `~/.claude/skills/agent-skills` symlink and `~/.config/agent-skills` directory if present.
4. **Minimal config block:** Splices `dist/CLAUDE.md`, `dist/AGENTS.md`, and `dist/GEMINI.md` into `~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, and `~/.gemini/GEMINI.md` between `# === agent-skills BEGIN ===` and `# === agent-skills END ===` markers, replacing any previous block idempotently.

## Layout

```
skills/             ← Native skill directories (skills/<category>/<name>/SKILL.md)
  _schema.md        ← Skill directory & frontmatter format documentation
  career/           ← resume-coach, system-design-interview
  coding/           ← agy-delegation, jev-prefilter
  communication/    ← multilingual-coaching, blog-writing
  design/           ← frontend-design, web-artifacts-builder, theme-factory, canvas-design, algorithmic-art (from anthropics/skills)
  context/          ← personal-context-sync
  language/         ← jlpt-n2-coach
  media/            ← quark-resource-search
  ops/              ← keychain-secrets
  wiki/             ← llm-wiki
tools/              ← CLI tools (agy-delegate, jev, keychain-secret)
dist/               ← Generated minimal CLAUDE.md / AGENTS.md / GEMINI.md blocks
scripts/            ← build.py / build.sh / install.sh / lint.sh
.claude-plugin/     ← Plugin manifest
```

## CI & Verification

CI runs on every push/PR to `main`:

1. `./scripts/lint.sh` — sensitive-data scan + native directory and frontmatter validation
2. `python3 ./scripts/build.py --check` — verifies committed `dist/` matches `skills/`
3. `HOME=/tmp/agy-home ./scripts/install.sh --dry-run all` — verifies the installer in dry-run mode

## License

MIT. See [LICENSE](LICENSE).
