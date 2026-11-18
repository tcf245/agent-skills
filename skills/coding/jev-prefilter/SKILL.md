---
name: jev-prefilter
description: Use when a task would load many items or a long text into context only to judge which parts matter (search results, log files, file lists, wiki pages). Send the bulk to Jev with the `jev` CLI and read only its short result.
type: workflow
triggers:
  - "many search results"
  - "long log"
  - "find the relevant"
  - "which of these"
  - "triage"
  - "wiki INGEST / LINT"
platforms: [cc, codex, gemini]
---

# Jev pre-filter

Jev (TypeSafe System One) answers one typed question per item — yes/no probability, a
score on described levels, or a choice — in well under a second per batch. Use it to
throw away noise **before** content enters the context. Tool: `tools/jev/jev.py`,
installed as `jev` on PATH. Key: `TYPESAFE_API_KEY` or Keychain `typesafe-api-key`.

## When to use

Use it when all three hold:

1. **Bulk**: about 20+ items, or a text of several thousand tokens or more.
2. **Simple per-item judgment**: is it relevant, which bucket, how well does it match.
3. **You only need the survivors**: you would otherwise read everything just to discard most of it.

Do not use it for a single branch decision in your own reasoning. Writing the request costs
more than deciding. Do not use it for fixed numeric thresholds, which belong in code. Do not
use it for multi-step reasoning or generation.

## Commands

```bash
# keep items where the answer is yes (P >= 0.5), best first
… | jev filter -q "Is this line about X?" [-c "background"] [--top 20]

# sort by graded match; levels are worst → best and describe situations
… | jev rank -q "How well does it match what we want?" -c "What we want: …" \
      -l "Wrong thing" "Right thing, poor quality" "Right thing, good" --top 5 --fields title,url

# label each item
… | jev classify -q "Which area?" -o "A=desc" -o "B=desc"

# locate relevant lines in a text log (Choice over line ids, 200-line windows)
jev lines -q "Which line shows the failure?" --input app.log --around 2
```

Input: JSON array, JSONL, or plain lines on stdin (`--input FILE` also works). Output: one
short JSONL row per kept item (`i` = input index); a stats line with Jev token use goes to stderr.

## Wired-in uses

| Workflow | Command |
|---|---|
| Quark resource search | `search_quark.py "{title}" --want "{what we want}" --top 5` (or `--candidates FILE` for rows collected in the browser) |
| Wiki INGEST | `python3 bin/jev_wiki.py related "raw/<file>.md"`: pages to update or link |
| Wiki LINT | `python3 bin/jev_wiki.py status-audit`: `refined` pages that read like stubs |
| Text logs | `jev lines` |
| netmon logs | **not Jev**: they are numeric, so use `netmon/incidents.py --at "…"` |

## Fallback when Jev is down

Jev is an optimisation, never a dependency. When it cannot answer (no key, network failure,
timeout, persistent 5xx/429, or a rejected key), `jev` prints `jev: UNAVAILABLE …` on stderr,
nothing on stdout, and **exits 3**. It needs about 2 s to give up, and a circuit breaker stops
the remaining items. Exit 2 means a bad request, which is a bug in the caller.

| Workflow | Degrades to (automatic) |
|---|---|
| Quark search `--want` | keyword `quality_score` order; log line `[jev] skipped` |
| `jev_wiki.py related` | keyword overlap with index entries; rows say `"via": "keyword-fallback"` |
| `jev_wiki.py status-audit` | refined pages under 1200 chars; rows say `"via": "length-fallback"` |
| Ad-hoc `jev filter/rank/lines` | do it the old way: `grep` / `rg`, or read the input in chunks |

Fallback output is noisier (for example, keyword order can rank the wrong film second), so
verify it more carefully and tell the user the run was degraded.

## Reading results

- `filter` → `p` is a probability. Near 0.5 means the model is unsure, not that the item is half relevant.
- `rank` → `score` is a probability-weighted level number; `conf` < 0.5 means the levels were close, so look at that row yourself.
- Typed output guarantees the format, not that the answer is true. Spot-check the top rows before acting, especially before anything destructive.
