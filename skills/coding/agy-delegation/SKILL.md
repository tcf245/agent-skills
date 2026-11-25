---
name: agy-delegation
description: Use when a task has a big, well-scoped execution part (batch edits across many files, i18n/translation, bulk text, writing tests, collecting and drafting from the wiki), when a question needs fresh web facts about everyday life (restaurants, shops, opening hours, prices, local how-tos), or when Claude's quota is past 50%. Hand that part to agy (Gemini through Google's official Antigravity CLI) with the `agy-delegate` tool; you judge, write the task, and verify.
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
  - "附近好吃的"
  - "餐厅推荐"
  - "营业时间"
  - "生活百科"
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
| < 50% | normal | Still delegate by default (below); do yourself only what is on the Keep list |
| 50–80% | conserve | Delegate every execution part agy can do; you only split, write packages, verify |
| 80–95% | reserve | No substantive work yourself. Delegate, or stop and tell Eric when the quota resets |
| ≥ 95% | stop | Only tell Eric where things stand and when it resets |

## What to hand over

**Delegation is the default, at every quota level (Eric 2026-11-22, FB-056).** agy used about 10% of its 5-hour window while Claude often passed 80%, so the balance was wrong. Before doing a piece of work yourself, ask whether a task package could carry it.

**Hand over:** anything with a clear scope and a way to check it — writing code, translation and any other text processing (rewrites, summaries, bulk edits), first drafts of specs and test plans, writing tests, verification runs (test suites, builds, starting a local server and checking routes or pages, comparing a translation with its source), applying a convention across many files, collecting from the wiki and drafting.

**Keep:** anything that needs accounts (mail, calendar, Discord, Notion, databases), deploys and publishing, secrets, hard-to-undo actions, trade-off decisions, and jobs that take a few minutes. For verification, re-running the package's `verify` command and reading the diff stays with you (cheap, and agy's own report does not count); the long checks behind it go to agy.

Don't sync other skills or MCP servers to agy. Put only the rules this task needs into `rules`.

## Life and web questions (Eric 2026-11-20)

Gemini is strong on everyday knowledge and agy has Google Search, so questions that need fresh facts from the web go to agy: restaurants and shops nearby, opening hours, prices, events, local procedures, general "how do I" knowledge. This saves Claude quota for judgment.

What agy can and cannot do (probe 2026-11-20, run `20261120-162931-3d5b`): it has `search_web` (Google Search grounding, cites sources through `vertexaisearch.cloud.google.com` redirect links). It has **no** Google Maps/Places tool and no URL fetch, so ratings and review counts arrive second-hand (Tabelog, blogs, travel sites), not live from Maps. A three-restaurant query took 86 s and 32k tokens on Hydrogen.

- Package: no `repo`, `verify: "true"`, `model: gemini-4-hydrogen-high` (`gemini-3.8-flash-*` when speed matters more than care), `timeout_min: 10`. Put the person's constraints in `goal` (area, time, budget, who is coming, allergies) but no names, phone numbers or booking numbers: the question goes to Google.
- Rules to pass: every fact comes from a search result in this run with its source; give today's date; say what could not be confirmed; answer in the user's language; give a decision and one fallback, not a long list.
- Your check: read `summary`. For facts the person will act on (hours today, reservation rules, prices), open the official page yourself when you can, or mark them 未核实. Replace the redirect links with the site names; keep at most one link per place.
- Quota: these runs use the `gemini` bucket. When it is below 50% the tool swaps to `argon`; when both are low, answer yourself with WebSearch instead of waiting.
- Say in the reply that Gemini looked it up.

## How

1. **Write the task package** (JSON) with the Write tool, e.g. in `$TMPDIR`:

   | Field | Meaning |
   |---|---|
   | `goal` | What to do and how far. agy has no context; be complete. For tasks over 3 steps, remind agy in `goal` to maintain `.agy/decisions.tsv` (the tool's ground rules already cover the format, so don't repeat the details) |
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

3. **Verify.** Read `status`, `summary`, `questions`, `files_changed` (from git, not from agy), `wiki_changed`, `warning`, and `decisions`. When `decisions` is present, read that TSV first (adapted from Cursor's `pstack` `show-me-your-work`, Lauren Tan, MIT): scan each row's `evidence` pointer, spot-check key entries by opening `file:line` or re-running the cited command, and send the task back if `bad_rows` is non-empty or a `superseded` chain is unclear. Then run `verify` in `workdir` and check `git diff --stat` yourself (agy saying the tests pass does not count). Read the full `git diff` only for parts the decision log leaves unclear.

4. **Land it.** agy never commits, so its work sits uncommitted in `workdir`. Good: `git add -A && git commit` there, then cherry-pick or merge it onto your branch and check `git log` (or copy the outputs). Not good: re-delegate with a sharper `goal`, or fix it yourself. Only then, as a separate command, `agy-delegate cleanup <run-id>` — cleanup refuses while the worktree has uncommitted changes; add `--discard` only when you really want them gone. Cleanup also closes the Rex pane the run opened.

5. **Report** which part agy did and how you checked it.

## Keep runs short

A run costs time per step, not per token: every file read, edit and command is one more model turn (logs, 2026-11-18/19: one wiki task spent 1,129 s thinking and 917 s in 29 small edits; a test fix thought 218 s against 130 s of commands). The tool's ground rules already tell agy to batch reads, merge edits, run the full check once and stop on environment trouble. Your package decides the rest:

- **Effort is the model suffix** (`-low`/`-medium`/`-high`); agy rejects `--effort` for every allowed model (Orchestrator: unsupported; suffixed: conflict).
- **Pick the model by how settled the plan is.** You wrote the plan and named the files: Hydrogen. agy must plan across several files or parts: Orchestrator (Neon). Four Orchestrator runs on spec-complete UI work took 9–15 min each.
- **Hand over what you already know.** Name the files (and line ranges) to read, the hypothesis you formed, and a real data sample when the code parses data — agy wrote a furigana parser from the spec's example and missed the real `<b>`/Anki-space format.
- **Pre-solve the environment in `rules`.** A worktree has no `node_modules`, Docker and secrets: say how to link `node_modules`, which Node to use, and which tests it cannot run (testcontainers need Docker — run those yourself). One unanswered setup question cost several probing commands per run.
- **Keep `verify` fast and targeted.** agy runs the tests itself: the cases for the change or the full suite, whichever is faster (Eric 2026-11-22: fewer round trips). Python goes through `/opt/homebrew/bin/uv`; agy's sandbox cannot read `~/.asdf`, and the tool already drops it from agy's PATH. For a repo with `uv.lock` the tool runs `uv sync --frozen` in the worktree before agy starts (result field `setup`), because agy's sandbox blocks fresh package versions (403 "in cooldown"). git does not work inside agy's sandbox for a worktree; the tool reads changes from git outside.
- **Find out where a slow run's time went.** The result and `~/workspace/.agy-runs/ledger.jsonl` keep `goal`, `conversation_id` and `timing` (turns, model seconds, longest turn, tool seconds, thinking tokens), and they survive cleanup; log lines carry `at` timestamps.
- **One package per landing unit.** Split work that lands on different branches into separate runs; run independent ones in parallel (each gets its own worktree).
- **Don't ask for extras.** No coverage reports, stress runs or docs unless the task needs them; each is a full extra pass.

## Claude Code specifics

- The sandbox lets this one command out through `sandbox.excludedCommands: ["agy-delegate *"]` in `~/.claude/settings.json` (agent-crew's admin has its own entry). Never add `dangerouslyDisableSandbox` to it. If it fails with `Operation not permitted`, the exclusion is missing; tell Eric.
- Use the Bash tool's background mode for runs over ~8 minutes.

## Anti-patterns

- Delegating a vague goal and then redoing the work yourself: costs both quotas.
- Reading every line agy changed instead of running the check: verification is the verify command plus a look at the diff.
- Using an Orchestrator or Neon/Argon for a two-minute edit (use Hydrogen).
- Passing whole skills, MCP access, or secrets to agy.
