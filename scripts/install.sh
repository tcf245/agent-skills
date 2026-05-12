#!/usr/bin/env bash
# Install agent-skills into the target platform's config location.
# Usage: ./scripts/install.sh <cc|codex|gemini|all>
#
# Env vars:
#   AGENT_SKILLS_HOME  — where to publish a stable copy of skills/ and vendored/
#                        (default: ~/.config/agent-skills)
#   CODEX_AGENTS_FILE  — override Codex target (default: ~/.codex/AGENTS.md)
#   GEMINI_AGENTS_FILE — override Gemini target (default: ~/.gemini/GEMINI.md)
#   CC_SKILLS_DIR      — override CC target (default: ~/.claude/skills)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_SKILLS_HOME="${AGENT_SKILLS_HOME:-$HOME/.config/agent-skills}"
CODEX_AGENTS_FILE="${CODEX_AGENTS_FILE:-$HOME/.codex/AGENTS.md}"
GEMINI_AGENTS_FILE="${GEMINI_AGENTS_FILE:-$HOME/.gemini/GEMINI.md}"
CC_SKILLS_DIR="${CC_SKILLS_DIR:-$HOME/.claude/skills}"

PLATFORM="${1:-}"

# --- helpers ----------------------------------------------------------------

log() { printf '[install] %s\n' "$*"; }
die() { printf '[install] ERROR: %s\n' "$*" >&2; exit 1; }

ensure_built() {
  if [ ! -f "$REPO_ROOT/dist/AGENTS.md" ] || [ ! -f "$REPO_ROOT/dist/GEMINI.md" ]; then
    log "dist/ missing — running build..."
    "$REPO_ROOT/scripts/build.sh"
  fi
}

publish_skills() {
  # Symlink skills/ and vendored/ into AGENT_SKILLS_HOME for stable absolute paths.
  mkdir -p "$AGENT_SKILLS_HOME"
  ln -sfn "$REPO_ROOT/skills" "$AGENT_SKILLS_HOME/skills"
  ln -sfn "$REPO_ROOT/vendored" "$AGENT_SKILLS_HOME/vendored"
  log "published skills+vendored to $AGENT_SKILLS_HOME (symlinks)"
}

rewrite_paths() {
  # stdin: index file with relative paths "skills/..." and "vendored/..."
  # stdout: same with absolute paths under $AGENT_SKILLS_HOME
  sed -e "s|\`skills/|\`$AGENT_SKILLS_HOME/skills/|g" \
      -e "s|\`vendored/|\`$AGENT_SKILLS_HOME/vendored/|g"
}

splice_into_file() {
  # Append (or replace) the agent-skills sentinel block in $TARGET_FILE.
  local target="$1"
  local content_file="$2"
  mkdir -p "$(dirname "$target")"
  local tmp="$(mktemp)"
  if [ -f "$target" ]; then
    # Drop any existing block, keep the rest
    awk '
      /^# === agent-skills BEGIN ===$/ { skip=1; next }
      /^# === agent-skills END ===$/   { skip=0; next }
      !skip
    ' "$target" > "$tmp"
  fi
  {
    if [ -s "$tmp" ]; then
      cat "$tmp"
      echo ""
    fi
    echo "# === agent-skills BEGIN ==="
    cat "$content_file"
    echo "# === agent-skills END ==="
  } > "${target}.new"
  mv "${target}.new" "$target"
  rm -f "$tmp"
  log "wrote $target"
}

# --- platform installers ----------------------------------------------------

install_cc() {
  # CC reads skills from ~/.claude/skills/<name>/SKILL.md or the plugin marketplace.
  # Simplest path: symlink each category dir under skills/ into ~/.claude/skills/agent-skills/...
  mkdir -p "$CC_SKILLS_DIR"
  ln -sfn "$REPO_ROOT/skills" "$CC_SKILLS_DIR/agent-skills"
  log "CC: linked $CC_SKILLS_DIR/agent-skills -> $REPO_ROOT/skills"
  log "CC: restart Claude Code to pick up new skills"
}

install_codex() {
  ensure_built
  publish_skills
  local tmp="$(mktemp)"
  rewrite_paths < "$REPO_ROOT/dist/AGENTS.md" > "$tmp"
  splice_into_file "$CODEX_AGENTS_FILE" "$tmp"
  rm -f "$tmp"
  log "Codex: AGENTS.md updated"
}

install_gemini() {
  ensure_built
  publish_skills
  local tmp="$(mktemp)"
  rewrite_paths < "$REPO_ROOT/dist/GEMINI.md" > "$tmp"
  splice_into_file "$GEMINI_AGENTS_FILE" "$tmp"
  rm -f "$tmp"
  log "Gemini: GEMINI.md updated"
}

case "$PLATFORM" in
  cc)     install_cc ;;
  codex)  install_codex ;;
  gemini) install_gemini ;;
  all)    install_cc; install_codex; install_gemini ;;
  ""|-h|--help)
    cat <<USAGE
Usage: $0 <cc|codex|gemini|all>

Installs agent-skills into the named platform's config location.

  cc      Symlinks skills/ into \$CC_SKILLS_DIR (default: ~/.claude/skills)
  codex   Splices dist/AGENTS.md into \$CODEX_AGENTS_FILE (default: ~/.codex/AGENTS.md)
  gemini  Splices dist/GEMINI.md into \$GEMINI_AGENTS_FILE (default: ~/.gemini/GEMINI.md)
  all     Run all three.

A stable copy of skills/+vendored/ is published as symlinks under
\$AGENT_SKILLS_HOME (default: ~/.config/agent-skills) so the AGENTS.md
references resolve to absolute paths that survive cwd changes.

Re-running this is idempotent: existing # === agent-skills BEGIN/END ===
blocks in target files are replaced, not duplicated.
USAGE
    exit 0
    ;;
  *)
    die "unknown platform: $PLATFORM (try: cc / codex / gemini / all)"
    ;;
esac
