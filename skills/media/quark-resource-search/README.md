# quark-resource-search

Search Quark Cloud (`pan.quark.cn`) for movie/TV resources, save to your pan via browser, and organize the result through a locally-running [Alist](https://alist.nn.ci/) instance.

## Prerequisites

- Python 3.9+ (the scripts use only the standard library)
- An Alist server reachable from the agent host (default expected: `http://localhost:5244`)
- A separate **alist-organizer** installation (the renaming back-end). The skill calls `run.sh` inside its directory; install and configure that tool independently.
- A logged-in Quark Cloud session in the browser that the agent drives (the skill does not log in for you)

## Setup

```bash
cd skills/media/quark-resource-search
cp config.example.json config.local.json
# edit config.local.json with your real Alist credentials, paths, optional API keys
export QUARK_SKILL_CONFIG="$(pwd)/config.local.json"
```

`config.local.json` is gitignored. Never commit real credentials.

## Files

- `SKILL.md` — the full procedure the agent follows
- `config.example.json` — template config; never commit `config.local.json`
- `scripts/search_quark.py` — Quark link discovery (tvso.uk → Google → fallback sites)
- `scripts/alist_rename.py` — list / batch-rename via Alist API
- `scripts/update_watchlist.py` — manage watch_list entries in the organizer config

## Sensitive data

This skill touches credentials. The repo enforces:

- `config.json` / `config.local.*` / `.env` are gitignored
- The lint script in `scripts/lint.sh` scans for hardcoded credentials, real email addresses, and real API keys
- The `watch_list` field of your config is personal data — keep it in `config.local.json`, not in the example
