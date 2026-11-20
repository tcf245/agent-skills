---
name: working-rules
description: >-
  Eric's standing rules for every agent: fix a repeated mistake in code or a check before adding prose; when a hook
  blocks you, do what its message says and never rephrase to slip past; keep secrets in macOS Keychain (keychain-secrets
  skill) and never read, print or pass them as arguments; run git push/pull yourself as a lone command; say the
  acceptance standard and show evidence before claiming done.
type: behavior
triggers:
  - always-on
platforms: [cc, codex, gemini]
---

# Working rules

The long-term practices Eric settled on (2026-11-20, from Lauren Tan's "All Code Is Slop (Except Mine)" and the
agent-crew feedback log FB-008, FB-032, FB-038, FB-040). They apply to Claude Code, Codex and agy alike. The ones that
must never be broken are also enforced by a hook, so the same rule holds even when this file is not read.

## 1. Fix mistakes in the cheapest layer that makes them impossible

When the same mistake happens a second time (or once, if it is hard to undo), fix it in the first layer that works:

1. **Design**: change the code or the flow so the wrong thing cannot be written.
2. **A check**: a test, a lint rule, or a hook such as `agent-crew/scripts/hard_rules.py`.
3. **Prose**: a line in CLAUDE.md, AGENTS.md or a skill. Keep prose for things that need judgment.

A check's error message says how to fix the problem. Checks can be wrong too: when one blocks normal work, record it
as feedback, relax or remove it, and add a test that the command should pass. Add rules sparingly; nothing that has not
gone wrong gets a rule.

## 2. When a hook blocks you

- Do what the message says. It names the rule and the fix.
- If the rule is wrong for this case, stop and tell Eric the rule's name. Never rephrase the command, split it oddly or
  use another tool just to get past the check.
- The hard rules today (source of truth: `RULES` in `~/workspace/agent-crew/scripts/hard_rules.py`): never open
  `crew.sqlite` on the Mac (use `kubectl -n crew exec deploy/crew -- python -c ...`); no `git rebase` or `git stash` in
  agent-crew; no force push or branch deletion; do not run the wiki's `snapshot.sh` by hand; git remotes from a sandbox
  that cannot read `~/.ssh` run as a lone command outside it.
- The hook runs in Claude Code (`~/.claude/settings.json`, agent-crew's admin) and in agy
  (`~/.gemini/config/hooks.json`). `python3 ~/workspace/agent-crew/scripts/hard_rules.py report` shows what it blocked.

## 3. Secrets live in Keychain

- Never read, print, paste or log a secret: `.env` files, tokens, API keys, private keys, login files, ID numbers.
- Store and fetch secrets with the `keychain-secrets` skill (`keychain-secret` CLI); its registry page in the wiki holds
  only names and the command to fetch each one, so a person can find every value without an agent.
- Values go through stdin or a pipe, never as command-line arguments, in chat, or in files under `~/workspace`.
- Found a plaintext secret (a `.env`, a token in a wiki page)? Report the file and line, not the value, and offer to
  move it into Keychain (`keychain-secret import-env`).

## 4. Git: act like a person at a terminal

- Run `git push`, `git pull` and `git fetch` yourself; do not ask Eric to run them. Git uses its own key; you never
  read key files.
- Keep `add` and `commit` where they are; take only the remote command, alone, outside a sandbox that hides `~/.ssh`.
- No force push, branch deletion or data deletion without Eric's explicit consent in this conversation.
- In a repo other sessions share, check what is staged, commit only your own paths, and never stash their work.

## 5. Done means shown

- No acceptance criteria given? Pick the usual standard for that kind of task and say it in one line when you start.
- Run the check, read its output, then claim the result. Separate what you verified from what you did not; a mock or a
  unit test is not the real phone or the real Discord.

## 6. Pages go to our own domain

Web pages, "Artifacts", mock-ups and reports are published to `artifacts.erictans.com` (agent-crew's `publish_page`
tool or `scripts/publish-page.sh`), not to claude.ai Artifacts, because only our domain can be shared with people
outside and has access Eric controls. Public links come from the page panel at `/go/pages` and expire.

## Anti-patterns

- Adding a sentence to a prompt for a mistake a test or hook could catch.
- Rewriting a blocked command so the hook no longer recognises it.
- `echo $TOKEN`, `cat .env`, or a secret as `--password value`.
- Asking Eric to push, or reading `~/.ssh` to push.
- "Should work now" without having run anything.
