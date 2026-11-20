#!/usr/bin/env bash
# Offline unit tests for tools/keychain-secret using a stubbed `security` binary on PATH.
# Never touches the real macOS Keychain.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOL="$REPO_ROOT/tools/keychain-secret"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/keychain-secret-test.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/bin"
export KEYCHAIN_STUB_DB="$TMP/db.json"
echo "{}" > "$KEYCHAIN_STUB_DB"

cat > "$TMP/bin/security" <<'STUB'
#!/usr/bin/env python3
import json
import os
import pathlib
import sys

db_path = pathlib.Path(os.environ["KEYCHAIN_STUB_DB"])
db = json.loads(db_path.read_text(encoding="utf-8"))

def save():
    db_path.write_text(json.dumps(db, indent=2), encoding="utf-8")

def format_item(svce: str, acct: str, info: dict) -> str:
    icmt = info.get("icmt", "")
    icmt_str = f'"{icmt}"' if icmt else "<NULL>"
    return (
        'keychain: "/tmp/stub.keychain-db"\n'
        'version: 512\n'
        'class: "genp"\n'
        'attributes:\n'
        f'    0x00000007 <blob>="Label for {svce}"\n'
        f'    "acct"<blob>="{acct}"\n'
        '    "cdat"<timedate>=0x32303236  "20261101000000Z\\000"\n'
        f'    "icmt"<blob>={icmt_str}\n'
        '    "mdat"<timedate>=0x32303236  "20261118000000Z\\000"\n'
        f'    "svce"<blob>="{svce}"\n'
    )

args = sys.argv[1:]
if not args:
    sys.exit(2)

sub = args[0]
rest = args[1:]

if sub == "find-generic-password":
    svce = ""
    acct = None
    want_w = False
    want_g = False
    i = 0
    while i < len(rest):
        if rest[i] == "-s":
            svce = rest[i + 1]
            i += 2
        elif rest[i] == "-a":
            acct = rest[i + 1]
            i += 2
        elif rest[i] == "-w":
            want_w = True
            i += 1
        elif rest[i] == "-g":
            want_g = True
            i += 1
        else:
            i += 1
    matches = []
    for k, v in db.items():
        s, a = k.split("\x1f", 1)
        if s == svce and (acct is None or a == acct):
            matches.append((s, a, v))
    if not matches:
        sys.stderr.write("security: SecKeychainSearchCopyNext: The specified item could not be found in the keychain.\n")
        sys.exit(44)
    s, a, info = matches[0]
    secret = info["secret"]
    # Mirror real `security`: non-printable or non-ASCII values come out as hex.
    is_hex = any(not (0x20 <= b < 0x7f) for b in secret.encode("utf-8"))
    if want_w:
        sys.stdout.write((secret.encode("utf-8").hex() if is_hex else secret) + "\n")
    elif want_g:
        sys.stdout.write(format_item(s, a, info))
        if is_hex:
            sys.stderr.write(f'password: 0x{secret.encode("utf-8").hex().upper()}  "<octal>"\n')
        else:
            sys.stderr.write(f"password: {json.dumps(secret)}\n")
    else:
        sys.stdout.write(format_item(s, a, info))
    sys.exit(0)

if sub == "add-generic-password":
    svce = ""
    acct = ""
    icmt = ""
    secret = ""
    update = False
    i = 0
    while i < len(rest):
        if rest[i] == "-U":
            update = True
            i += 1
        elif rest[i] == "-s":
            svce = rest[i + 1]
            i += 2
        elif rest[i] == "-a":
            acct = rest[i + 1]
            i += 2
        elif rest[i] == "-j":
            icmt = rest[i + 1]
            i += 2
        elif rest[i] == "-w":
            secret = rest[i + 1]
            i += 2
        else:
            i += 1
    key = f"{svce}\x1f{acct}"
    if key in db and not update:
        sys.stderr.write("security: SecKeychainItemCreateFromContent: The specified item already exists in the keychain.\n")
        sys.exit(45)
    db[key] = {"icmt": icmt, "secret": secret}
    save()
    sys.exit(0)

if sub == "delete-generic-password":
    svce = ""
    acct = None
    i = 0
    while i < len(rest):
        if rest[i] == "-s":
            svce = rest[i + 1]
            i += 2
        elif rest[i] == "-a":
            acct = rest[i + 1]
            i += 2
        else:
            i += 1
    for k in list(db.keys()):
        s, a = k.split("\x1f", 1)
        if s == svce and (acct is None or a == acct):
            del db[k]
            save()
            sys.exit(0)
    sys.exit(44)

if sub == "dump-keychain":
    if "-d" in rest:
        sys.stderr.write("FORBIDDEN: dump-keychain -d called!\n")
        sys.exit(99)
    for k, info in db.items():
        s, a = k.split("\x1f", 1)
        sys.stdout.write(format_item(s, a, info))
    sys.exit(0)

sys.exit(2)
STUB
chmod +x "$TMP/bin/security"

export PATH="$TMP/bin:$PATH"

assert_eq() {
  local got="$1" want="$2" msg="$3"
  if [ "$got" != "$want" ]; then
    printf 'FAIL: %s\n  got:  %s\n  want: %s\n' "$msg" "$got" "$want" >&2
    exit 1
  fi
}

assert_contains() {
  local haystack="$1" needle="$2" msg="$3"
  if [[ "$haystack" != *"$needle"* ]]; then
    printf 'FAIL: %s\n  missing: %s\n  in:\n%s\n' "$msg" "$needle" "$haystack" >&2
    exit 1
  fi
}

assert_not_contains() {
  local haystack="$1" needle="$2" msg="$3"
  if [[ "$haystack" == *"$needle"* ]]; then
    printf 'FAIL: %s\n  unexpectedly found: %s\n' "$msg" "$needle" >&2
    exit 1
  fi
}

# 1. --help
help_out="$("$TOOL" --help)"
assert_contains "$help_out" "keychain-secret get" "--help lists subcommands"

# 2. add (with stdin)
export KEYCHAIN_SECRET_TODAY="2026-11-01"
add_err="$(printf 'my-super-secret-value-1' | "$TOOL" add "dabia/backend/production/SECRET_KEY" "vercel" --expires "2026-12-15" --note "initial" 2>&1 >/dev/null)"
assert_contains "$add_err" "Reminder: update" "add prints registry reminder on stderr"
assert_not_contains "$add_err" "my-super-secret-value-1" "add never prints secret on stderr"

# 2b. add refuses duplicate
if printf 'second-val' | "$TOOL" add "dabia/backend/production/SECRET_KEY" "vercel" 2>/dev/null; then
  echo "FAIL: duplicate add should fail" >&2
  exit 1
fi

# 2c. add refuses secret passed on argv
if "$TOOL" add "some-svc" "eric" "secret-on-argv" 2>/dev/null; then
  echo "FAIL: add with extra positional arg should fail" >&2
  exit 1
fi

# 3. get outputs value on stdout ONLY
got_val="$("$TOOL" get "dabia/backend/production/SECRET_KEY" "vercel")"
assert_eq "$got_val" "my-super-secret-value-1" "get returns exact secret on stdout"

got_val_no_acct="$("$TOOL" get "dabia/backend/production/SECRET_KEY")"
assert_eq "$got_val_no_acct" "my-super-secret-value-1" "get without account returns exact secret"

# 4. info outputs metadata and never the secret
info_out="$("$TOOL" info "dabia/backend/production/SECRET_KEY")"
assert_contains "$info_out" "service:  dabia/backend/production/SECRET_KEY" "info prints service"
assert_contains "$info_out" "account:  vercel" "info prints account"
assert_contains "$info_out" "created:  2026-11-01" "info prints created"
assert_contains "$info_out" "expires:  2026-12-15" "info prints expires"
assert_not_contains "$info_out" "my-super-secret-value-1" "info never prints secret"

# 5. rotate updates value, keeps created, sets rotated
export KEYCHAIN_SECRET_TODAY="2026-11-18"
rot_err="$(printf 'rotated-secret-value-2' | "$TOOL" rotate "dabia/backend/production/SECRET_KEY" "vercel" 2>&1 >/dev/null)"
assert_contains "$rot_err" "Reminder: update" "rotate prints registry reminder"
assert_not_contains "$rot_err" "rotated-secret-value-2" "rotate never prints secret"

got_rot="$("$TOOL" get "dabia/backend/production/SECRET_KEY" "vercel")"
assert_eq "$got_rot" "rotated-secret-value-2" "get after rotate returns new secret"

info_rot="$("$TOOL" info "dabia/backend/production/SECRET_KEY" "vercel")"
assert_contains "$info_rot" "created:  2026-11-01" "rotate preserves created date"
assert_contains "$info_rot" "rotated:  2026-11-18" "rotate sets rotated=today"
assert_contains "$info_rot" "expires:  2026-12-15" "rotate preserves expires when not overridden"

# 6. expire updates only comment expires without changing or printing secret
exp_err="$("$TOOL" expire "dabia/backend/production/SECRET_KEY" "2026-11-25" 2>&1 >/dev/null)"
assert_contains "$exp_err" "Reminder: update" "expire prints registry reminder"
assert_not_contains "$exp_err" "rotated-secret-value-2" "expire never prints secret"

info_exp="$("$TOOL" info "dabia/backend/production/SECRET_KEY")"
assert_contains "$info_exp" "created:  2026-11-01" "expire preserves created"
assert_contains "$info_exp" "rotated:  2026-11-18" "expire preserves rotated"
assert_contains "$info_exp" "expires:  2026-11-25" "expire updates expires"
assert_eq "$("$TOOL" get "dabia/backend/production/SECRET_KEY")" "rotated-secret-value-2" "expire preserves secret value"

# 6b. Non-ASCII values: real `security -w` prints hex; get must return plain text
#     and expire must not re-save the hex string as the secret.
printf '%s' '{"name_en":"TAN","name_zh":"谭"}' | "$TOOL" add "passport-probe" "eric" 2>/dev/null
assert_eq "$("$TOOL" get "passport-probe" "eric")" '{"name_en":"TAN","name_zh":"谭"}' "get decodes hex-printed non-ASCII value"
"$TOOL" expire "passport-probe" "eric" "2027-01-01" 2>/dev/null
assert_eq "$("$TOOL" get "passport-probe" "eric")" '{"name_en":"TAN","name_zh":"谭"}' "expire keeps non-ASCII value intact"
printf 'deadbeef' | "$TOOL" add "hexlike-key" "eric" 2>/dev/null
assert_eq "$("$TOOL" get "hexlike-key" "eric")" "deadbeef" "get leaves an ASCII hex-looking secret untouched"

# 7. retire dry-run vs --yes
printf 'temp-secret' | "$TOOL" add "temp-key" "eric" 2>/dev/null
retire_preview="$("$TOOL" retire "temp-key" "eric" 2>/dev/null)"
assert_contains "$retire_preview" "Would delete Keychain generic-password: service=temp-key account=eric" "retire without --yes previews deletion"
assert_eq "$("$TOOL" get "temp-key" "eric")" "temp-secret" "retire without --yes does not delete"

retire_err="$("$TOOL" retire "temp-key" "eric" --yes 2>&1 >/dev/null)"
assert_contains "$retire_err" "Reminder: update" "retire --yes prints registry reminder"
if "$TOOL" get "temp-key" "eric" 2>/dev/null; then
  echo "FAIL: retired key should be gone" >&2
  exit 1
fi

# 8. audit against a fake registry
printf 'app-tok' | "$TOOL" add "Claude Code-credentials" "eric" 2>/dev/null
printf 'elec-tok' | "$TOOL" add "Cursor Safe Storage" "Cursor" 2>/dev/null
printf 'sys-tok' | "$TOOL" add "com.apple.cloudd.device" "apple" 2>/dev/null
printf 'unreg-tok' | "$TOOL" add "mystery-unregistered-key" "eric" 2>/dev/null
printf 'exp-past' | "$TOOL" add "already-expired-key" "eric" --expires "2026-11-10" 2>/dev/null
printf 'far-future' | "$TOOL" add "far-future-key" "eric" --expires "2027-06-01" 2>/dev/null

FAKE_REG="$TMP/Registry.md"
cat > "$FAKE_REG" <<'EOF'
# Keychain Secrets Registry

## User-Managed Keys

| Service | Account | Project | Purpose | Sensitivity | Get | Created | Rotated | Expires | Status |
|---|---|---|---|---|---|---|---|---|---|
| `dabia/backend/production/SECRET_KEY` | `vercel` | Dabia | Backend secret | high | `security find-generic-password -s 'dabia/backend/production/SECRET_KEY' -a 'vercel' -w` | 2026-11-01 | 2026-11-18 | 2026-11-25 | active |
| `already-expired-key` | `eric` | Personal | Old key | high | `security find-generic-password -s 'already-expired-key' -a 'eric' -w` | 2026-10-01 | — | 2026-11-10 | active |
| `far-future-key` | `eric` | Personal | Future key | high | `security find-generic-password -s 'far-future-key' -a 'eric' -w` | 2026-11-01 | — | 2027-06-01 | active |
| `missing-from-keychain-key` | `vercel` | Dabia | Missing key | high | `security find-generic-password -s 'missing-from-keychain-key' -a 'vercel' -w` | — | — | 2026-12-01 | active |

## App-managed (do not edit by hand)

| Service | Account | Purpose |
|---|---|---|
| `Claude Code-credentials` | `eric` | Claude Code login |
| `* Safe Storage` | `*` | Electron Safe Storage |

## Retired

| Service | Account | Retired on | Reason |
|---|---|---|---|
| `retired-old-key` | `eric` | 2026-10-01 | Replaced |
EOF

audit_out="$("$TOOL" audit --registry "$FAKE_REG")"
assert_contains "$audit_out" "mystery-unregistered-key (eric)" "audit reports unregistered keychain item"
assert_not_contains "$audit_out" "Claude Code-credentials" "audit ignores App-managed item"
assert_not_contains "$audit_out" "Cursor Safe Storage" "audit ignores wildcard Safe Storage item"
assert_not_contains "$audit_out" "com.apple.cloudd.device" "audit ignores macOS system item"
assert_contains "$audit_out" "missing-from-keychain-key (vercel)" "audit reports registry row missing from Keychain"
assert_contains "$audit_out" "already-expired-key (eric): expired on 2026-11-10" "audit reports expired item"
assert_contains "$audit_out" "dabia/backend/production/SECRET_KEY (vercel): expires on 2026-11-25" "audit reports item expiring within 30d"
assert_not_contains "$audit_out" "far-future-key" "audit does not flag item expiring >30d out"
assert_not_contains "$audit_out" "rotated-secret-value-2" "audit never prints secret values"
assert_not_contains "$audit_out" "unreg-tok" "audit never prints secret values"

# 9. import-env: move a plaintext .env into Keychain and emit a value-free mapping
DOTENV="$TMP/app.env"
cat > "$DOTENV" <<'EOF'
# comment line
API_TOKEN=tok-abc-123
DB_URL="postgres://u:pw-xyz@h/db"
PORT=8080

QUOTED_SPACE='a b'
EOF
map_out="$("$TOOL" import-env "$DOTENV" "app/local" "eric" --keep PORT 2>"$TMP/import.err")"
import_err="$(cat "$TMP/import.err")"
assert_contains "$map_out" "API_TOKEN=keychain:app/local/API_TOKEN#eric" "import-env maps secret var to Keychain ref"
assert_contains "$map_out" 'DB_URL=keychain:app/local/DB_URL#eric' "import-env maps quoted var"
assert_contains "$map_out" "PORT=8080" "import-env keeps --keep vars as plain values"
assert_not_contains "$map_out" "tok-abc-123" "mapping never contains secret values"
assert_not_contains "$map_out" "pw-xyz" "mapping never contains secret values"
assert_not_contains "$import_err" "tok-abc-123" "import-env never prints secrets on stderr"
assert_eq "$("$TOOL" get "app/local/API_TOKEN" "eric")" "tok-abc-123" "import-env stores value"
assert_eq "$("$TOOL" get "app/local/DB_URL" "eric")" '"postgres://u:pw-xyz@h/db"' "import-env stores right-hand side verbatim"

# 9b. import-env is idempotent when the stored value already matches
map_again="$("$TOOL" import-env "$DOTENV" "app/local" "eric" --keep PORT 2>/dev/null)"
assert_eq "$map_again" "$map_out" "import-env re-run with same values gives same mapping"

# 9c. import-env refuses to overwrite a different existing value
printf 'API_TOKEN=different\n' > "$TMP/changed.env"
if "$TOOL" import-env "$TMP/changed.env" "app/local" "eric" >/dev/null 2>&1; then
  echo "FAIL: import-env must refuse to overwrite a different value" >&2
  exit 1
fi

# 10. env renders the mapping back to the original dotenv (comments/blank lines dropped)
MAPFILE="$TMP/app.env.keychain"
printf '%s\n' "$map_out" > "$MAPFILE"
env_out="$("$TOOL" env "$MAPFILE")"
assert_eq "$env_out" "$(grep -v -e '^#' -e '^$' "$DOTENV")" "env reproduces the original dotenv"

# 10b. env fails loudly (no partial output) on a missing Keychain item
printf 'A=1\nB=keychain:no/such/item#eric\n' > "$TMP/bad.keychain"
if bad_out="$("$TOOL" env "$TMP/bad.keychain" 2>/dev/null)"; then
  echo "FAIL: env must fail on a missing item" >&2
  exit 1
fi
assert_eq "${bad_out:-}" "" "env prints nothing when an item is missing"

# 11. run injects unquoted values into the child environment
run_out="$("$TOOL" run "$MAPFILE" -- /usr/bin/env)"
assert_contains "$run_out" "API_TOKEN=tok-abc-123" "run exports Keychain value"
assert_contains "$run_out" "DB_URL=postgres://u:pw-xyz@h/db" "run strips dotenv double quotes"
assert_contains "$run_out" "QUOTED_SPACE=a b" "run strips dotenv single quotes"
assert_contains "$run_out" "PORT=8080" "run exports plain values"
if "$TOOL" run "$MAPFILE" /usr/bin/true 2>/dev/null; then
  echo "FAIL: run without -- should fail" >&2
  exit 1
fi

echo "[test-keychain-secret] ✅ all tests passed"
