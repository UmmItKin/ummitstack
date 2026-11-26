#!/bin/sh
# Usage: sh tests/run.sh
# Checks that toggle.py adds and removes only its own hook and never damages the settings file.
set -u
here=$(cd "$(dirname "$0")" && pwd)
t=$here/../scripts/toggle.py
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
S=$T/settings.json
cat > "$S" <<'JSON'
{
  "model": "x",
  "hooks": {
    "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "true"}]}],
    "SessionStart": [{"matcher": "startup", "hooks": [{"type": "command", "command": "echo other"}]}]
  }
}
JSON
cp "$S" "$T/original.json"
py() { python3 -c "$1" "$S"; }
python3 "$t" status --settings "$S" | grep -q ': off' && ok "status is off at the start" || bad "status is not off at the start"
python3 "$t" on --settings "$S" >/dev/null
python3 "$t" status --settings "$S" | grep -q ': on' && ok "on turns it on" || bad "on does not turn it on"
py 'import json,sys; d=json.load(open(sys.argv[1])); assert d["model"]=="x" and "PreToolUse" in d["hooks"] and any("echo other" in h["command"] for g in d["hooks"]["SessionStart"] for h in g["hooks"])' && ok "other settings and hooks are kept" || bad "other settings or hooks were lost"
python3 "$t" on --settings "$S" >/dev/null
py 'import json,sys; d=json.load(open(sys.argv[1])); n=sum(1 for g in d["hooks"]["SessionStart"] for h in g["hooks"] if "auto-find-best-skill" in h["command"]); assert n==1, n' && ok "running on twice leaves one hook" || bad "running on twice duplicated the hook"
[ "$(sh -c "$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print([h['command'] for g in d['hooks']['SessionStart'] for h in g['hooks'] if 'auto-find-best-skill' in h['command']][0])" "$S")" | grep -c 'Skill tool')" -eq 1 ] && ok "the hook command prints the reminder" || bad "the hook command does not print the reminder"
python3 "$t" off --settings "$S" >/dev/null
python3 -c "import json,sys; a=json.load(open(sys.argv[1])); b=json.load(open(sys.argv[2])); assert a==b" "$S" "$T/original.json" && ok "off restores the original settings exactly" || bad "off did not restore the original settings"
[ -f "$S.before-auto-find-best-skill" ] && ok "a one-time copy of the original is kept" || bad "no copy of the original was kept"
printf '{"model": "y"}' > "$T/plain.json"
python3 "$t" on --settings "$T/plain.json" >/dev/null && python3 "$t" off --settings "$T/plain.json" >/dev/null
python3 -c "import json,sys; assert json.load(open(sys.argv[1]))=={'model':'y'}" "$T/plain.json" && ok "off removes the empty hooks key it created" || bad "off left an empty hooks key"
printf '{ not json' > "$T/broken.json"
cp "$T/broken.json" "$T/broken.copy"
python3 "$t" on --settings "$T/broken.json" >/dev/null 2>&1; code=$?
[ "$code" -ne 0 ] && cmp -s "$T/broken.json" "$T/broken.copy" && ok "an invalid settings file fails and is left untouched" || bad "an invalid settings file was changed or accepted"
python3 "$t" on --settings "$T/new/settings.json" >/dev/null && python3 "$t" status --settings "$T/new/settings.json" | grep -q ': on' && ok "a missing settings file is created" || bad "a missing settings file was not created"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
