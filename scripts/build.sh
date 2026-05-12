#!/usr/bin/env bash
# Build dist/AGENTS.md and dist/GEMINI.md.
# Thin wrapper around build.py; lets you `./scripts/build.sh` without remembering python3.
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/build.py "$@"
