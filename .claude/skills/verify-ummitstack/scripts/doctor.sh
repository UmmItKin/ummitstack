#!/bin/sh
# Usage: sh doctor.sh
# Read-only check of whether this checkout is worth verifying. Prints one line per check and ends with ok or the problems. Exit 1 on a problem.
here=$(cd "$(dirname "$0")" && pwd)
root=$(cd "$here/../../../.." && pwd)
bad=0
fail() { echo "PROBLEM $1"; bad=1; }
[ -f "$root/scripts/check.sh" ] && [ -d "$root/skills" ] || fail "not the ummitstack repo: $root"
for t in git python3 npx; do command -v "$t" >/dev/null 2>&1 || fail "$t is not installed"; done
n=$(ls -d "$root"/skills/*/SKILL.md 2>/dev/null | wc -l)
echo "skills in the repo: $n"
listed=$(cd /tmp && npx -y skills add "$root" -l 2>&1 | grep -o 'Found [0-9]* skills' | grep -o '[0-9]*')
echo "skills the installer finds: ${listed:-none}"
[ "${listed:-0}" -eq "$n" ] || fail "the installer finds ${listed:-0} skills but the repo has $n; a frontmatter may be invalid"
changed=$(git -C "$root" status --porcelain | wc -l)
echo "uncommitted changes: $changed"
find "$root/skills" -name __pycache__ | grep -q . && echo "NOTE __pycache__ folders exist under skills; git ignores them but a local install copies them"
[ "$bad" -eq 0 ] && echo ok
exit "$bad"
