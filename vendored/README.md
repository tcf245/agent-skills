# Vendored Third-Party Skills

This directory contains **verbatim snapshots** of skills owned by other authors, vendored here so that **non-Claude-Code platforms** (Codex CLI, Gemini CLI, etc.) — which cannot install plugin-marketplace skills the way Claude Code can — still have access to the same behavioral discipline.

## How to use

- **On Claude Code**: prefer the original upstream plugins, installed via the plugin marketplace. They get updates faster and include support files (extended examples, helper scripts) that we don't vendor here.
- **On Codex / Gemini CLI**: the build script wires these vendored files into `dist/AGENTS.md` and `dist/GEMINI.md` so the agent reads them on demand.

## Vendoring rules

1. **Verbatim snapshots.** No paraphrasing, no edits to the body. We only prepend an attribution comment block.
2. **License preserved.** All vendored content is MIT-licensed (see below); the original copyright notice is reproduced in the attribution header of each file.
3. **Snapshot, not symlink.** Each file is a frozen copy with a `Snapshot date:` field in the header. We refresh on a deliberate schedule, not automatically.
4. **No support files.** Some upstream skills reference adjacent files (e.g. `condition-based-waiting.md`, `testing-anti-patterns.md`). Those are NOT vendored — links in the body will dead-end on non-CC platforms. Users wanting full content should consult upstream.

## Refresh procedure

Recommended cadence: **quarterly**, or sooner if upstream announces a major change.

1. Compare each file's `Source version:` against the upstream version.
2. For each version drift:
   - Pull fresh `SKILL.md` from upstream.
   - Re-run the vendoring step (`scripts/vendor.sh` or the inline shell snippet in `scripts/build.sh`).
   - Eyeball-diff the result; commit with a message referencing the upstream version bump.
3. Update the snapshot date in this README.

## Currently vendored (as of 2026-07-04)

| File | Upstream | Version | License |
|------|----------|---------|---------|
| `karpathy-guidelines.md` | `andrej-karpathy-skills:karpathy-guidelines` | 1.0.0 | MIT © 2025 Andrej Karpathy |

## Full MIT license notice (applies to all vendored files)

```
MIT License

Copyright (c) 2025 Andrej Karpathy (karpathy-skills)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```
