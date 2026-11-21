---
name: keychain-secrets
description: Use when looking up, adding, rotating, setting expiry on, retiring, or auditing secrets in macOS Keychain and the LLM Wiki Keychain Secrets Registry.
type: workflow
triggers:
  - "keychain"
  - "secret"
  - "API key"
  - "token"
  - "密钥"
  - "key 轮换"
  - "新增 key"
  - "过期"
  - "退休"
  - "where is the key"
  - "怎么拿 key"
platforms: [cc, codex, gemini]
---

# macOS Keychain Secrets Management

Manage all API keys, tokens, credentials, and sensitive personal pointers in macOS Keychain (login keychain, generic passwords) paired with the LLM Wiki index at `~/Library/Mobile Documents/iCloud~md~obsidian/Documents/LLM-Wiki/wiki/records/Keychain Secrets Registry.md`.

## Core Principles

1. **Values live only in Keychain**: store secret values exclusively as generic passwords in the macOS login keychain.
2. **Wiki holds pointers only**: `[[Keychain Secrets Registry]]` records service, account, project, purpose, sensitivity, lifecycle dates, and the retrieval command — never secret values.
3. **Never echo or log secrets**: never print a secret into chat, terminal stdout, logs, git commits, or wiki pages. Retrieve values only into an environment variable or a pipe:
   ```bash
   export API_KEY="$(keychain-secret get '<service>' '<account>')"
   # or directly via macOS security:
   export API_KEY="$(security find-generic-password -s '<service>' -a '<account>' -w)"
   ```

## Naming Convention

- **New project/service keys**: service = `<project>/<component>/<env>/<NAME>` (e.g. `dabia/backend/production/SECRET_KEY`), account = owner or source platform (`eric`, `vercel`, `cloudflare`).
- **New personal keys**: service = short kebab-case id (e.g. `typesafe-api-key`), account = `eric` (or provider name).
- **Existing keys**: keep existing service and account names as they are — no mass renames.

## Lifecycle Metadata Format

`keychain-secret` stores lifecycle metadata in the Keychain item's comment attribute (`-j`) using semicolon-separated `key=value` pairs:

```text
created=YYYY-MM-DD;rotated=YYYY-MM-DD;expires=YYYY-MM-DD;registry=Keychain Secrets Registry
```

Missing fields are allowed (e.g. before first rotation or when no expiry is set); optional `note=<text>` is appended when `--note` is given. Mirror `Created`, `Rotated`, and `Expires` (`—` when unknown/unset) in the registry table.

## Who Does What (Human vs. Agent)

- **Human enters secret values**: agents must never see secret values or pass them as CLI arguments. For `add` and `rotate`, the agent prepares the exact command for the human to run in their terminal (where `read -s` prompts with hidden input), then the agent updates `[[Keychain Secrets Registry]]` and `log.md`.
- **Agent runs pointer & metadata ops**: the agent looks up rows in the registry, runs `info`, `expire`, `audit`, and updates the registry in the **same session**. When a task needs a secret at runtime, the agent binds `$(keychain-secret get ...)` to an env var in the command subshell without printing it.
- **Deleting requires explicit approval**: never run `retire --yes` without the owner's explicit OK in the current session.
- **Why `security -w` is accepted**: internally, `keychain-secret` reads the secret via `read -s` (TTY) or stdin (pipe) and calls `security add-generic-password ... -w "$secret"`. Passing `-w` to `security` briefly exposes the argument in local `ps` during the sub-millisecond call; this is accepted on a single-user Mac because `security` has no non-interactive stdin password flag for `-U` updates, while `keychain-secret` keeps the value out of shell history, agent context, and logs.

## Reading Values as a Human

The registry's `Get` column must give the owner plain text with no agent involved. `security find-generic-password -w` prints the value as **hex** whenever it holds any non-ASCII or non-printable byte (Chinese in a JSON blob, a newline), so new rows use `keychain-secret get`, which detects that case (via `security -g`) and decodes it. Without the tool: Keychain Access.app → search the service → double-click → tick **Show password**; or append `| xxd -r -p` to the `security ... -w` command for hex-printed items only.

## Lifecycle Commands & Same-Session Registry Actions

Tool: `keychain-secret` on PATH (`~/.local/bin/keychain-secret` → `agent-skills/tools/keychain-secret`).

| Action | Command | Same-session update in `[[Keychain Secrets Registry]]` |
|---|---|---|
| **Get** | `export X="$(keychain-secret get '<service>' ['<account>'])"` | None (look up the row first to find `<service>` and `<account>`). |
| **Add** | `keychain-secret add '<service>' '<account>' [--expires YYYY-MM-DD] [--note TEXT]` | Add a row to the User-Managed table (`Created` = today, `Rotated` = `—`, `Expires` = date or `—`, `Status` = `active`, `Get` = `keychain-secret get '<service>' '<account>'`) + append `log.md`. |
| **Rotate** | `keychain-secret rotate '<service>' ['<account>'] [--expires YYYY-MM-DD]` | Update `Rotated` = today (and `Expires` if changed) on the row + append `log.md`. |
| **Inspect** | `keychain-secret info '<service>' ['<account>']` | None (prints service, account, comment metadata, and Keychain timestamps — never the secret). |
| **Set expiry** | `keychain-secret expire '<service>' ['<account>'] YYYY-MM-DD` | Update `Expires` = `YYYY-MM-DD` on the row in the User-Managed table + append `log.md`. |
| **Retire** | `keychain-secret retire '<service>' ['<account>'] [--yes]` | Without `--yes`, previews target. With `--yes` (after owner OK), deletes from Keychain; move row from User-Managed table to **Retired** table with `Retired on` = today and `Reason` + append `log.md`. |
| **Backup** | `keychain-secret backup` (launchd `com.eric.keychain-backup` runs it daily 22:30) | None. Copies go to the vault's `_private/keychain-backup/` (never into the GitHub snapshot; any other destination is refused); recovery steps live in the registry's **Backup & Recovery** section. |
| **Audit** | `keychain-secret audit [--registry PATH]` | Reconcile output (names only): add missing user-managed items (or classify under **App-managed**), remove/retire rows missing from Keychain, and rotate keys expired or expiring within 30 days. |

## Project `.env` Files

Plaintext `.env` files are not allowed, even when gitignored. Each project keeps a value-free **`.env.keychain`** (committed) and renders values at use time:

```text
DISCORD_BOT_TOKEN=keychain:agent-crew/prod/DISCORD_BOT_TOKEN#eric   # from Keychain
NGINX_PORT=8080                                                     # plain, non-secret config
```

| Need | Command |
|---|---|
| Migrate an existing `.env` | `keychain-secret import-env .env <project>/<env> eric --keep PORT,... > .env.keychain`, check `diff <(keychain-secret env .env.keychain) <(grep -v -e '^#' -e '^$' .env)` is empty, then delete `.env` |
| Run a dev server / script | `keychain-secret run .env.keychain -- <command>` |
| Tool that only reads a file (k8s `--from-env-file`, compose `--env-file`) | `<(keychain-secret env .env.keychain)` (process substitution, never a file on disk) |
| Change one value | `keychain-secret rotate <project>/<env>/<KEY> eric` (human enters the value) |

Service naming: `<project>/<env>/<KEY>`, account `eric`. Add one registry row per item (the agent may group them by project in the Purpose text) in the same session.

## Anti-Patterns

- Never run `security find-generic-password -w` as a bare command whose stdout returns to the agent transcript.
- Never pass a secret value in command-line arguments (`add <service> <account> <secret>` is rejected by `keychain-secret`).
- Never edit or delete items listed under **App-managed (do not edit by hand)** in the registry (`Claude Code-credentials`, `gh:github.com`, `Supabase CLI`, `gemini`/`antigravity`, `* Safe Storage`) — use each tool's own login flow instead.
