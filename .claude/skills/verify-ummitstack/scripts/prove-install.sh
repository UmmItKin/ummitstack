#!/bin/sh
# Usage: sh prove-install.sh SKILL [EVIDENCE_DIR]
# Installs SKILL from this checkout into a throwaway HOME the way a user would (npx skills add -g), then checks the installed copy:
# identical to the repo, passes the static check, and passes its own tests/run.sh when it has one. Your real ~/.claude is never touched.
# Evidence goes to EVIDENCE_DIR (default $TMPDIR/verify-ummitstack/<time>-SKILL) and is kept; only the throwaway HOME is removed.
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../../.." && pwd)
skill=${1:-}
[ -n "$skill" ] && [ -d "$root/skills/$skill" ] || { echo "Usage: sh prove-install.sh SKILL (a folder under skills/)" >&2; exit 2; }
ev=${2:-${TMPDIR:-/tmp}/verify-ummitstack/$(date +%Y%m%d-%H%M%S)-$skill}
mkdir -p "$ev"
H=$(mktemp -d)
trap 'rm -rf "$H"' EXIT
real_before=$(ls -R "$HOME/.claude/skills" 2>/dev/null | sha256sum | cut -c1-16)
bad=0
check() { if [ "$2" -eq 0 ]; then echo "PASS $1" | tee -a "$ev/summary.txt"; else echo "FAIL $1" | tee -a "$ev/summary.txt"; bad=1; fi; }
: > "$ev/summary.txt"
(cd "$H" && HOME="$H" npm_config_cache="${npm_config_cache:-$HOME/.npm}" npx -y skills add "$root" --skill "$skill" -g -a claude-code -y) > "$ev/install.txt" 2>&1
inst=$H/.claude/skills/$skill
[ -f "$inst/SKILL.md" ]; check "the installer put SKILL.md in a throwaway HOME" $?
diff -rq "$root/skills/$skill" "$inst" -x __pycache__ > "$ev/diff.txt" 2>&1; check "the installed copy is identical to skills/$skill" $?
python3 "$root/skills/verify-skill/scripts/static_check.py" "$inst" > "$ev/static.txt" 2>&1; check "the installed copy passes the static check" $?
if [ -f "$inst/tests/run.sh" ]; then
  HOME="$H" sh "$inst/tests/run.sh" > "$ev/tests.txt" 2>&1; rc=$?
  tail -1 "$ev/tests.txt" >> "$ev/summary.txt"
  check "the installed copy's own tests pass from the installed location" $rc
else
  echo "SKIP the skill has no tests/run.sh" | tee -a "$ev/summary.txt"
fi
real_after=$(ls -R "$HOME/.claude/skills" 2>/dev/null | sha256sum | cut -c1-16)
[ "$real_before" = "$real_after" ]; check "your real ~/.claude/skills is unchanged" $?
echo "evidence: $ev"
exit "$bad"
