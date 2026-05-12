---
name: quark-resource-search
description: |
  Search, save, and organize Quark Cloud (pan.quark.cn) movie/TV resources.
  Two entry points — (A) full flow: user says "find me X" / "search X on Quark" / "download X to pan",
  the agent runs search -> filter quality -> save to Quark via browser -> update watchlist ->
  Alist rename. (B) organize-only: user says "organize X" or gives a path/link, skips the
  search+save and goes straight to renaming.
type: workflow
triggers:
  - "find resource"
  - "search quark"
  - "download to pan"
  - "organize this folder"
  - "帮我找资源"
  - "搜索 .* 夸克"
  - "下载 .* 到网盘"
  - "整理 .*"
platforms: [cc, codex, gemini]
---

# Quark Cloud Resource Search & Organize

## Setup (one-time)

This skill bundles three Python helper scripts. Before first use:

1. Copy `config.example.json` to `config.local.json` (gitignored).
2. Fill in your values:
   - `alist_url` — typically `http://localhost:5244` for a local Alist instance
   - `alist_user` / `alist_password` — your Alist admin credentials
   - `alist_organizer_dir` — absolute path to your locally-installed [alist-organizer](https://github.com/) checkout (the renaming back-end). The skill calls `run.sh` inside this directory.
   - `tmdb.api_key` / `tmdb.access_token` — optional, for richer metadata; leave blank to skip
3. Export the config path so scripts can find it:
   ```bash
   export QUARK_SKILL_CONFIG=/abs/path/to/config.local.json
   ```

Scripts live under `scripts/` next to this `SKILL.md`. They take all credentials as CLI args — no hardcoded paths in the Python.

## Design principle

- **Scripts handle determinism**: HTTP, link extraction, quality scoring, JSON I/O, Alist API calls.
- **LLM handles judgment**: pick the best candidate, infer the canonical English title/year, handle exceptions.
- **Minimize token use**: only invoke the LLM at decision points.

## Entry decision

| User says | Entry |
|-----------|-------|
| "find resource X" / "search X quark" / "download X to pan" / "帮我找资源…" | **A — full flow** |
| "organize X" / "帮我整理" / gives an Alist path or Quark link | **B — organize only** |

---

## Entry A — full flow

### A1. Run the candidate-search script

```bash
python scripts/search_quark.py "{title}" 2>/dev/null
```

Search priority: **tvso.uk → Google → mizixing/kuakes**. The script emits a JSON array sorted by quality score. Each candidate has `title`, `url`, `quality_score`, `is_tc`, `valid`, `pub_date`, `source`.

- Quality score: 4K/2160p/UHD = 3; original disc / Blu-ray = 2; 1080P = 1; other = 0
- `is_tc: true` flags theatrical-camera / pirated low-quality rips
- `valid` is set by a HEAD request on the top three non-TC candidates
- All three sources combine; deduplicated by URL

Exceptions:
- tvso.uk empty/timeout → script auto-falls back to Google
- Google blocked → script switches to resource-site-only search
- Single-source timeout doesn't kill the run

### A2. [LLM decision] Pick the best candidate

Rules in order:
1. `valid: true` AND `is_tc: false` AND highest `quality_score`
2. On a tie, prefer the more recent `pub_date` (newer = less likely to be revoked)
3. On a date tie, prefer the candidate whose `title`/`snippet` suggests larger file or cleaner naming
4. If all valid candidates are tied, ask the user

If no valid candidate: retry A1 once with the query rewritten as `"{title} 1080P 夸克"` or `"{title} {current_year}"`. Cap at 2 retries; if still empty, tell the user and stop.

### A3. Save to Quark via the browser

Open the chosen `https://pan.quark.cn/s/XXXX`:

1. Verify the file list renders (no "失效" / "expired" banner)
2. Click the header checkbox to select all
3. Click the "保存到网盘" (save to pan) button
4. Confirm the dialog: "保存成功，已保存至：来自：分享"

Record the resulting Alist path: `/Quark/来自：分享/{top-level folder}`.

Exceptions:
- Dialog timeout → refresh page once, retry
- "账号异常" / account error → tell the user to check their Quark login; stop
- Link expired only on save → go back to A2 and pick the next candidate

### A4. Wait for Alist to refresh

```bash
sleep 60 && echo "Alist refresh complete"
```

### A5. Enter the organize flow (see below).

---

## Entry B — organize only

Collect the target:
- User gives a path → use directly
- User gives a Quark share link → record path as `/Quark/来自：分享/{top folder from share}`
- User gives only a name → list the Alist share dir and let the LLM match:

```bash
python scripts/alist_rename.py list \
    --path "/Quark/来自：分享" \
    --url "${ALIST_URL}" --user "${ALIST_USER}" --password "${ALIST_PASSWORD}"
```

(Substitute the env vars from your `config.local.json`.)

---

## Organize flow (after A5 or as Entry B)

### Step 1: List directory contents

```bash
python scripts/alist_rename.py list \
    --path "{alist_path}" \
    --recursive --videos-only \
    --url "${ALIST_URL}" --user "${ALIST_USER}" --password "${ALIST_PASSWORD}"
```

### Step 2: [LLM decision] Determine canonical naming

From filenames and folder structure, infer:
- **Canonical English title** (use the TMDB-common form for the organizer)
- **Type**: `movie` | `tv`
- **Year** (required — disambiguates remakes)
- **Season number** (required for `tv`)
- **Alist path** per organize target (one watch_list entry each)

Naming spec (Infuse/Plex-compatible):
- Movie file: `Movie English Name (Year).ext`
- TV file: `Series Name S01E01.ext`
- Parent folder: human-readable, no special chars (no `()`, `[]`, `!`, `*`). Suggested form: `中文名 English Name Year` or `中文名 English Name Year1-Year2`

### Step 3: Update watch_list (via script)

For each target:

```bash
# Movie
python scripts/update_watchlist.py add \
    --config "${QUARK_SKILL_CONFIG}" \
    --path "{alist_path}" \
    --series-name "{English Name}" \
    --type movie \
    --year {year} \
    --update

# TV
python scripts/update_watchlist.py add \
    --config "${QUARK_SKILL_CONFIG}" \
    --path "{alist_path}" \
    --series-name "{English Name}" \
    --type tv \
    --year {year} \
    --season {season} \
    --update
```

Exceptions:
- `config.json` missing → report, stop
- JSON malformed → script detects and refuses to overwrite

### Step 4: Run the alist-organizer back-end

```bash
cd "${ALIST_ORGANIZER_DIR}" && bash run.sh 2>&1 | tee /tmp/organizer_last.log
```

Check the log:
- `Renamed:` lines = successful renames
- `Scan complete.` = run finished
- `API Error` / `Login failed` = check Alist credentials in config

Exceptions:
- "no files found" → Alist may still be refreshing; sleep 30s and retry once
- Result still non-conformant (e.g., Chinese chars / numeric names) → proceed to Step 5

### Step 5: Verify and supplemental rename

Re-list the directory:

```bash
python scripts/alist_rename.py list \
    --path "{alist_path}" --recursive --videos-only \
    --url "${ALIST_URL}" --user "${ALIST_USER}" --password "${ALIST_PASSWORD}"
```

**[LLM decision]** If any filename is still off-spec, build a batch rename operations list:

```json
[
  {"path": "/Quark/来自：分享/xxx/old.mkv", "name": "Movie Name (2024) 4K.mkv"},
  {"path": "/Quark/来自：分享/xxx_folder",  "name": "Movie Name 中文名 2024"}
]
```

Execute:

```bash
echo '[{"path":"...","name":"..."}]' | \
python scripts/alist_rename.py batch --stdin \
    --url "${ALIST_URL}" --user "${ALIST_USER}" --password "${ALIST_PASSWORD}"
```

### Step 6: Report to user

- Resource name and quality of what was saved
- New watch_list entries added
- Count of `Renamed:` lines from organizer log
- Final file list from Step 5
- Any failures and suggested next steps

---

## Script vs LLM split

| Step | Owner | Reason |
|------|-------|--------|
| Google / tvso scrape + link extraction | script | deterministic HTTP |
| Quality scoring (4K / 1080P / TC) | script | fixed keyword matches |
| Link validity check | script | HTTP status |
| **Pick the best candidate** | **LLM** | composite judgment (quality + naming + recency) |
| Save to Quark in browser | browser-automation tool | requires authenticated session |
| Wait for Alist refresh | script (sleep) | fixed delay |
| Update watch_list | script | JSON write, no judgment |
| Run organizer | script (run.sh) | fixed command |
| **Determine canonical title / year / season** | **LLM** | requires title recognition |
| File / folder rename spec | script + LLM | script lists state, LLM proposes rename map |
| Execute batch rename | script | Alist API calls |

---

## Cross-platform notes

- On Claude Code, browser automation can use the `claude-in-chrome` MCP if installed, or `mcp__computer-use__*` for native fallback.
- On Codex / Gemini CLI, you'll need a separate browser-automation tool — Playwright via shell is the usual fallback. The Quark login state must be pre-established (browser cookies); these agents cannot perform the initial login interactively for you.
- All three Python scripts work cross-platform — they're pure stdlib (`urllib`, `argparse`, `json`).
