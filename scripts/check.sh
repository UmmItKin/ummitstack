#!/bin/sh
# Usage: sh scripts/check.sh
# The one check for this repo, run the same way locally and in CI.
set -u
cd "$(dirname "$0")/.."
fail=0
for t in skills/*/tests/run.sh; do
  [ -e "$t" ] || continue
  echo "== $t"
  sh "$t" || fail=1
done
echo "== TLA+ model check"
sh scripts/tla-check.sh || fail=1
echo "== shared files must be identical"
for f in run.py pagescore.py; do
  cmp -s skills/docx-reverse-pandoc/scripts/$f skills/pdf-reverse-pandoc/scripts/$f || { echo "FAIL $f differs between docx-reverse-pandoc and pdf-reverse-pandoc"; fail=1; }
done
echo "== unslop scan"
if [ -f skills/unslop-writing/scripts/scan.py ]; then
  python3 skills/unslop-writing/scripts/scan.py skills/docx-reverse-pandoc/SKILL.md skills/docx-reverse-pandoc/references/*.md >/dev/null 2>&1 || echo "scan reported hits (review by hand)"
fi
exit $fail
