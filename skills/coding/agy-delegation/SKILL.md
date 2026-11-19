---
name: agy-delegation
description: Use when a task has a big, well-scoped execution part (batch edits across many files, i18n/translation, bulk text, writing tests, collecting and drafting from the wiki) or when Claude's quota is past 50%. Hand that part to agy (Gemini through Google's official Antigravity CLI) with the `agy-delegate` tool; you judge, write the task, and verify.
type: workflow
triggers:
  - "交给 agy"
  - "委托给 agy"
  - "用 agy"
  - "delegate to agy"
  - "batch task"
  - "批量"
  - "大量文件"
  - "quota is running low"
  - "额度不够"
platforms: [cc]
---

# Delegate execution to agy

Eric has spare Google AI quota and a limited Claude quota. The split: **you (Claude) decide, write the task package and verify; agy executes.** Google forbids proxying its models, so the only allowed route is you calling the official `agy` CLI on this Mac through `agy-delegate` (code: `tools/agy-delegate/agy_delegate.py`). It enforces the limits: fresh git worktree, `--sandbox`, JSON result, time limit, model allow-list, no secret files.

Works the same in a terminal session, a Remote Control session and agent-crew's admin.

## Keep Claude quota in reserve

You stay the gateway even when agy does all the work, so Claude's 5-hour window must never reach 100%. Check it before a big task and when a task drags on:

```sh
agy-delegate quota
```

`five_hour` is the share used, `age_minutes` how old the number is (the status line and agent-crew's admin keep it fresh).

| Used | Mode | What you do |
|---|---|---|
| < 50% | normal | Delegate what fits (below); do the rest yourself |
| 50–80% | conserve | Delegate every execution part agy can do; you only split, write packages, verify |
| 80–95% | reserve | No substantive work yourself. Delegate, or stop and tell Eric when the quota resets |
| ≥ 95% | stop | Only tell Eric where things stand and when it resets |

## What to hand over

**Hand over:** clear scope, a lot of work or a long run, and a way to check it — batch edits or translations, applying a convention across many files, writing tests, collecting from the wiki and drafting.

**Keep:** anything that needs accounts (mail, calendar, Discord, databases), deploys and publishing, secrets, hard-to-undo actions, trade-off decisions, and small jobs that take a few minutes.

Don't sync other skills or MCP servers to agy. Put only the rules this task needs into `rules`.

## How

1. **Write the task package** (JSON) with the Write tool, e.g. in `$TMPDIR`:

   | Field | Meaning |
   |---|---|
   | `goal` | What to do and how far. agy has no context; be complete |
   | `repo` | A git repo under `~/workspace` (runs in a new worktree, branch `agy/<run-id>`; the original tree is untouched). Or omit it and list input files in `files` |
   | `rules` | The few rules from the relevant skills and the repo's CLAUDE.md/AGENTS.md for this task |
   | `verify` | A command that proves it worked. agy runs it; **you run it again** |
   | `wiki` | `read` or `write` to give agy the LLM Wiki and the llm-wiki skill. For a handover, write it into the wiki or the run folder first and say where in `goal` |
   | `model` | Default `gemini-pro-orchestrator-neon` = Orchestrator (Neon) (Eric 2026-11-19: Neon replaced Argon; Neon plans and reviews, Hydrogen executes). Small, fully specified edits: `gemini-4-hydrogen-high`. Hardest single-thread work: `gemini-4-neon-high`/`-xhigh`. `gemini-3.8-flash-*` only for bulk text where speed matters. Argon (`gemini-4-argon-*`, `gemini-pro-orchestrator-g1-pro`) is only the fallback bucket. **Quota protection:** agy has two buckets, as its quota page shows: `gemini` (Neon, Orchestrator Neon, Hydrogen and 3.8 Flash share it) and `argon` (Argon + Orchestrator Argon), each with a weekly and a 5-hour limit. agy's CLI cannot report them, so when Eric pastes the page, record each bucket: `agy-delegate agy-quota <gemini|argon> <left%> <refresh-hours>` (no arguments shows it; a reading expires at the refresh time, default 7 days). Below 50% left, the tool swaps the model for the other bucket (`model_swapped_from`). On a quota error mid-task it continues on the other bucket in the same folder (`fallback_from`) and skips the empty one for 5 hours. Claude models inside agy are not allowed |
   | `timeout_min` | Default 30, max 60 |
   | `requester` | `eric` or `baobao` |

2. **Run it as a lone command** — no `cd`, `&&`, pipes or heredoc in the same call, or the sandbox exclusion does not apply:

   ```sh
   agy-delegate run /path/to/task.json
   ```

   Inside Rex a pane opens on the right showing agy's steps live (`--no-panel` to skip). The run can take longer than one shell call allows: for anything over a few minutes, run it in the background and wait for the completion notice.

3. **Verify.** Read `status`, `summary`, `questions`, `files_changed` (from git, not from agy), `wiki_changed`, `warning`. In `workdir`, run `verify` and look at `git diff` yourself. agy saying the tests pass does not count.

4. **Land it.** Good: merge or cherry-pick branch `agy/<run-id>` (or copy the outputs). Not good: re-delegate with a sharper `goal`, or fix it yourself. Then `agy-delegate cleanup <run-id>`.

5. **Report** which part agy did and how you checked it.

## Claude Code specifics

- The sandbox lets this one command out through `sandbox.excludedCommands: ["agy-delegate *"]` in `~/.claude/settings.json` (agent-crew's admin has its own entry). Never add `dangerouslyDisableSandbox` to it. If it fails with `Operation not permitted`, the exclusion is missing; tell Eric.
- Use the Bash tool's background mode for runs over ~8 minutes.

## Anti-patterns

- Delegating a vague goal and then redoing the work yourself: costs both quotas.
- Reading every line agy changed instead of running the check: verification is the verify command plus a look at the diff.
- Using an Orchestrator or Neon/Argon for a two-minute edit (use Hydrogen).
- Passing whole skills, MCP access, or secrets to agy.
