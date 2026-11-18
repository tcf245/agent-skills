#!/usr/bin/env bash
# Install agent-skills into ~/.agents/skills, ~/.claude/skills, ~/.gemini/skills,
# and splice the minimal always-on block into CLAUDE.md, AGENTS.md, and GEMINI.md.
#
# Usage: ./scripts/install.sh [--dry-run] [all|cc|codex|gemini]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
AGENTS_SKILLS_DIR="${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}"
CC_SKILLS_DIR="${CC_SKILLS_DIR:-$HOME/.claude/skills}"
GEMINI_SKILLS_DIR="${GEMINI_SKILLS_DIR:-$HOME/.gemini/skills}"
CC_CLAUDE_FILE="${CC_CLAUDE_FILE:-$HOME/.claude/CLAUDE.md}"
CODEX_AGENTS_FILE="${CODEX_AGENTS_FILE:-$HOME/.codex/AGENTS.md}"
GEMINI_AGENTS_FILE="${GEMINI_AGENTS_FILE:-$HOME/.gemini/GEMINI.md}"
LEGACY_CC_LINK="$CC_SKILLS_DIR/agent-skills"
LEGACY_CONFIG_DIR="${AGENT_SKILLS_HOME:-$HOME/.config/agent-skills}"
TODAY="$(date +%Y%m%d)"
REPLACED_DIR="$AGENTS_SKILLS_DIR/.replaced-$TODAY"

DRY_RUN=0
PLATFORM="all"

for arg in "$@"; do
  case "$arg" in
    --dry-run|-n)
      DRY_RUN=1
      ;;
    all|cc|codex|gemini)
      PLATFORM="$arg"
      ;;
    -h|--help)
      cat <<USAGE
Usage: $0 [--dry-run] [all|cc|codex|gemini]

Installs native skill symlinks and minimal agent config blocks:
  1. For each skill dir under skills/ containing SKILL.md:
     - Symlinks ~/.agents/skills/<name> -> <repo>/skills/<cat>/<name>
       (backs up any existing real directory to ~/.agents/skills/.replaced-YYYYmmdd/<name>)
     - Symlinks ~/.claude/skills/<name> -> ~/.agents/skills/<name>
     - Symlinks ~/.gemini/skills/<name> -> ~/.agents/skills/<name>
  2. Removes legacy ~/.claude/skills/agent-skills and ~/.config/agent-skills if present.
  3. Splices minimal dist/{CLAUDE,AGENTS,GEMINI}.md blocks (# === agent-skills BEGIN/END ===)
     into ~/.claude/CLAUDE.md, ~/.codex/AGENTS.md, and ~/.gemini/GEMINI.md.
USAGE
      exit 0
      ;;
    *)
      printf '[install] ERROR: unknown argument: %s\n' "$arg" >&2
      exit 1
      ;;
  esac
done

log() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf '[install --dry-run] %s\n' "$*"
  else
    printf '[install] %s\n' "$*"
  fi
}

ensure_built() {
  if [ ! -f "$REPO_ROOT/dist/CLAUDE.md" ] || [ ! -f "$REPO_ROOT/dist/AGENTS.md" ] || [ ! -f "$REPO_ROOT/dist/GEMINI.md" ]; then
    if [ "$DRY_RUN" -eq 1 ]; then
      log "would run $REPO_ROOT/scripts/build.sh"
    else
      log "dist/ missing — running build..."
      "$REPO_ROOT/scripts/build.sh"
    fi
  fi
}

cleanup_legacy() {
  for old_path in "$LEGACY_CC_LINK" "$LEGACY_CONFIG_DIR"; do
    if [ -L "$old_path" ] || [ -e "$old_path" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then
        log "rm -rf $old_path"
      else
        rm -rf "$old_path"
        log "removed legacy $old_path"
      fi
    elif [ "$DRY_RUN" -eq 1 ]; then
      log "cleanup check (absent): $old_path"
    fi
  done
}

link_skill_dirs() {
  if [ "$DRY_RUN" -eq 0 ]; then
    mkdir -p "$AGENTS_SKILLS_DIR" "$CC_SKILLS_DIR" "$GEMINI_SKILLS_DIR"
  else
    log "mkdir -p $AGENTS_SKILLS_DIR $CC_SKILLS_DIR $GEMINI_SKILLS_DIR"
  fi

  while IFS= read -r skill_md; do
    local skill_dir name agents_target
    skill_dir="$(dirname "$skill_md")"
    name="$(basename "$skill_dir")"
    agents_target="$AGENTS_SKILLS_DIR/$name"

    if [ -d "$agents_target" ] && [ ! -L "$agents_target" ]; then
      if [ "$DRY_RUN" -eq 1 ]; then
        log "mv $agents_target $REPLACED_DIR/$name"
      else
        mkdir -p "$REPLACED_DIR"
        rm -rf "$REPLACED_DIR/$name"
        mv "$agents_target" "$REPLACED_DIR/$name"
        log "backed up real dir $agents_target -> $REPLACED_DIR/$name"
      fi
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
      log "ln -sfn $skill_dir $agents_target"
    else
      ln -sfn "$skill_dir" "$agents_target"
      log "linked $agents_target -> $skill_dir"
    fi

    for consumer_dir in "$CC_SKILLS_DIR" "$GEMINI_SKILLS_DIR"; do
      local consumer_target="$consumer_dir/$name"
      if [ -d "$consumer_target" ] && [ ! -L "$consumer_target" ]; then
        local consumer_backup="$consumer_dir/.replaced-$TODAY"
        if [ "$DRY_RUN" -eq 1 ]; then
          log "mv $consumer_target $consumer_backup/$name"
        else
          mkdir -p "$consumer_backup"
          rm -rf "$consumer_backup/$name"
          mv "$consumer_target" "$consumer_backup/$name"
        fi
      fi
      if [ "$DRY_RUN" -eq 1 ]; then
        log "ln -sfn $agents_target $consumer_target"
      else
        ln -sfn "$agents_target" "$consumer_target"
        log "linked $consumer_target -> $agents_target"
      fi
    done
  done < <(find "$REPO_ROOT/skills" -name 'SKILL.md' | sort)
}

splice_into_file() {
  local target="$1"
  local content_file="$2"
  if [ "$DRY_RUN" -eq 1 ]; then
    log "splice $content_file -> $target (# === agent-skills BEGIN/END ===)"
    return 0
  fi
  mkdir -p "$(dirname "$target")"
  local tmp
  tmp="$(mktemp)"
  if [ -f "$target" ]; then
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

ensure_built
cleanup_legacy
link_skill_dirs

case "$PLATFORM" in
  cc)
    splice_into_file "$CC_CLAUDE_FILE" "$REPO_ROOT/dist/CLAUDE.md"
    ;;
  codex)
    splice_into_file "$CODEX_AGENTS_FILE" "$REPO_ROOT/dist/AGENTS.md"
    ;;
  gemini)
    splice_into_file "$GEMINI_AGENTS_FILE" "$REPO_ROOT/dist/GEMINI.md"
    ;;
  all)
    splice_into_file "$CC_CLAUDE_FILE" "$REPO_ROOT/dist/CLAUDE.md"
    splice_into_file "$CODEX_AGENTS_FILE" "$REPO_ROOT/dist/AGENTS.md"
    splice_into_file "$GEMINI_AGENTS_FILE" "$REPO_ROOT/dist/GEMINI.md"
    ;;
esac
