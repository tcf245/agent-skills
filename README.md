# agent-skills

A cross-platform skill collection for AI coding agents — write your working habits once, run them on Claude Code, Codex CLI, and Gemini CLI.

## What's this for?

If you switch between coding agents (Claude Code → Codex → Gemini CLI), each one forgets your conventions: how you write plans, when you do TDD, which diagram tool to use, how you organize your Obsidian wiki. This repo packages those **process methodologies** as portable skill files that any agent can load.

**Design philosophy**:
- **Methodology only, no data.** Your actual code, notes, and secrets stay where they are. Skills only describe *how* to work.
- **One source of truth, three platforms.** Skills written in Anthropic's markdown-with-frontmatter format are consumed natively by Claude Code, and a build script generates index files (`AGENTS.md` / `GEMINI.md`) for Codex and Gemini CLI.
- **Lazy load by default.** On every platform, the agent reads only the skill it needs for the current task, not the entire ruleset upfront.

## Status

🚧 v0.1.0 in progress. See `docs/superpowers/specs/` once we cut the first release.

## Install

> _Coming after v0.1.0 lands. For now, this is an active build._

```bash
git clone https://github.com/tcf245/agent-skills.git
cd agent-skills
./scripts/install.sh <cc|codex|gemini|all>
```

## Layout

```
skills/         ← Self-authored skills (source of truth)
vendored/       ← Snapshots of third-party skills, attributed (for non-CC platforms)
dist/           ← Generated AGENTS.md / GEMINI.md (committed; CI verifies in-sync)
scripts/        ← build / install / lint
```

## License

MIT. See [LICENSE](LICENSE).

Vendored third-party skills retain their own licenses — see `vendored/README.md`.
