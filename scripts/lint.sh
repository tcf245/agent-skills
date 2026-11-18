#!/usr/bin/env bash
# Lint agent-skills repo for sensitive data leaks and native skill frontmatter rules.
# Exit 0 on success, non-zero on any finding. CI gate.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

violations=0
report() {
  printf '  [lint] %s\n' "$*" >&2
  violations=$((violations + 1))
}

scan_for() {
  # Args: <description> <grep-extended-regex>
  local desc="$1"
  local pattern="$2"
  local hits
  hits=$(
    grep -rEn --binary-files=without-match \
      --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yml' --include='*.yaml' \
      "$pattern" . 2>/dev/null \
      | grep -v '^./.git/' \
      | grep -v '^./scripts/lint.sh:' \
      || true
  )
  if [ -n "$hits" ]; then
    report "found $desc:"
    while IFS= read -r line; do
      printf '    %s\n' "$line" >&2
    done <<< "$hits"
  fi
}

echo "[lint] starting…"

# --- 1. Personal emails ----------------------------------------------------
# tcf245@gmail.com is the public maintainer address (appears in every commit's
# Author field and in .claude-plugin/plugin.json) — not treated as sensitive.
# whc2458@gmail.com is a non-public alternative address — must never appear.
scan_for "non-public personal emails" 'whc2458@gmail\.com'

# --- 2. Credential patterns (excluding placeholders / example files) -------
hits=$(
  grep -rEn --binary-files=without-match \
    --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yml' --include='*.yaml' \
    -e 'password[[:space:]]*[:=][[:space:]]*"[^<][^"]+"' \
    -e 'api[_-]?key[[:space:]]*[:=][[:space:]]*"[^<][^"]+"' \
    -e 'access_token[[:space:]]*[:=][[:space:]]*"[^<][^"]+"' \
    -e 'Bearer[[:space:]]+[A-Za-z0-9_\-]{20,}' \
    . 2>/dev/null \
    | grep -v '^./.git/' \
    | grep -v '^./scripts/lint.sh:' \
    | grep -vE '/(config\.example|.*\.example\.)' \
    || true
)
if [ -n "$hits" ]; then
  report "credential-shaped values:"
  while IFS= read -r line; do
    printf '    %s\n' "$line" >&2
  done <<< "$hits"
fi

# --- 3. Specific known leaked secrets (defense in depth) -------------------
scan_for "TVDB API key (ed65e055…)" 'ed65e055-997a-476a-b663-5e670b941ead'

# --- 4. Non-local IPv4 addresses --------------------------------------------
hits=$(
  grep -rEn --binary-files=without-match \
    --include='*.md' --include='*.py' --include='*.sh' --include='*.json' --include='*.yml' --include='*.yaml' \
    '([0-9]{1,3}\.){3}[0-9]{1,3}' . 2>/dev/null \
    | grep -v '^./.git/' \
    | grep -v '^./scripts/lint.sh:' \
    | grep -vE '127\.0\.0\.1|0\.0\.0\.0|255\.255\.255\.|192\.168\.|10\.0\.0\.[0-9]+|0\.0\.0|1\.0\.0' \
    || true
)
if [ -n "$hits" ]; then
  report "non-local IP addresses:"
  while IFS= read -r line; do
    printf '    %s\n' "$line" >&2
  done <<< "$hits"
fi

# --- 5. Native skill directory format (no loose skill .md files) -----------
loose=$(find skills -mindepth 2 -maxdepth 2 -type f -name '*.md' || true)
if [ -n "$loose" ]; then
  report "non-directory skill files under skills/<category>/ (must be skills/<category>/<name>/SKILL.md):"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    printf '    %s\n' "$line" >&2
  done <<< "$loose"
fi

# --- 6. Frontmatter sanity and directory-name match ------------------------
missing=""
while IFS= read -r f; do
  fm=$(awk '/^---$/{c++; if(c==1) start=1; else if(c==2){print; exit}} c==1 && !/^---$/{print}' "$f")
  for key in name description; do
    if ! grep -qE "^${key}:" <<< "$fm"; then
      missing="${missing}${f}: missing frontmatter key '${key}'
"
    fi
  done
  dir_name="$(basename "$(dirname "$f")")"
  fm_name="$(awk -F': *' '/^name:/{gsub(/["'\'']/, "", $2); print $2; exit}' <<< "$fm")"
  if [ -n "$fm_name" ] && [ "$fm_name" != "$dir_name" ]; then
    missing="${missing}${f}: frontmatter name '${fm_name}' does not match directory '${dir_name}'
"
  fi
done < <(find skills -name 'SKILL.md' | sort)

if [ -n "$missing" ]; then
  report "frontmatter completeness:"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    printf '    %s\n' "$line" >&2
  done <<< "$missing"
fi

# --- summary ----------------------------------------------------------------
if [ "$violations" -eq 0 ]; then
  echo "[lint] ✅ clean"
  exit 0
fi
echo "[lint] ❌ $violations finding(s)" >&2
exit 1
