#!/bin/sh
# Usage: sh tests/run.sh
# Checks that migrate.py copies memory safely, using a temporary Claude folder only.
set -u
here=$(cd "$(dirname "$0")" && pwd)
m=$here/../scripts/migrate.py
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
C=$T/claude
OLD=$T/work/old.repo
NEW=$T/work/new-repo
mkdir -p "$OLD" "$NEW"
okey=$(python3 -c "import re,sys; print(re.sub(r'[^A-Za-z0-9]','-',sys.argv[1]))" "$OLD")
nkey=$(python3 -c "import re,sys; print(re.sub(r'[^A-Za-z0-9]','-',sys.argv[1]))" "$NEW")
mkdir -p "$C/projects/$okey/memory"
printf -- '- [One](one.md): first\n- [Two](two.md): second\n' > "$C/projects/$okey/memory/MEMORY.md"
printf 'note about %s\n' "$OLD" > "$C/projects/$okey/memory/one.md"
printf 'two\n' > "$C/projects/$okey/memory/two.md"
printf '{}\n' > "$C/projects/$okey/session-1.jsonl"
run() { python3 "$m" "$NEW" --from "$OLD" --claude-dir "$C" "$@"; }

run >"$T/dry.txt" 2>&1; code=$?
[ "$code" -eq 0 ] && [ ! -e "$C/projects/$nkey" ] && ok "a dry run changes nothing" || bad "a dry run changed something or failed (exit $code)"
grep -q "copy     memory/one.md" "$T/dry.txt" && ok "the plan lists the files to copy" || bad "the plan does not list the files"
snap() { (cd "$C/projects/$okey" && find . -type f | sort | xargs sha256sum | sha256sum); }
before=$(snap)
run --apply >"$T/apply.txt" 2>&1; code=$?
[ "$code" -eq 0 ] && cmp -s "$C/projects/$okey/memory/two.md" "$C/projects/$nkey/memory/two.md" && ok "apply copies the memory" || bad "apply did not copy the memory (exit $code)"
[ "$(snap)" = "$before" ] && ok "the old folder is left exactly as it was (checksum of every file)" || bad "the old folder was changed"
[ ! -e "$C/projects/$nkey/session-1.jsonl" ] && ok "sessions are not copied without --with-sessions" || bad "sessions were copied without the flag"
grep -q "still mention the old path" "$T/apply.txt" && ok "lines that mention the old path are reported" || bad "old path mentions were not reported"
grep -q "$OLD" "$C/projects/$nkey/memory/one.md" && ok "and the memory text is not edited" || bad "the memory text was edited"
run --apply >"$T/again.txt" 2>&1; [ $? -eq 0 ] && ok "running it again is safe" || bad "running it again failed"
printf 'changed\n' > "$C/projects/$nkey/memory/two.md"
run --apply >"$T/conf.txt" 2>&1; code=$?
[ "$code" -eq 2 ] && [ "$(cat "$C/projects/$nkey/memory/two.md")" = changed ] && ok "a differing file is a conflict and is not overwritten" || bad "a differing file was overwritten or not reported (exit $code)"
printf -- '- [Three](three.md): third\n' >> "$C/projects/$okey/memory/MEMORY.md"
printf 'three\n' > "$C/projects/$okey/memory/three.md"
run --apply >/dev/null 2>&1
grep -q "Three" "$C/projects/$nkey/memory/MEMORY.md" && [ "$(grep -c 'One' "$C/projects/$nkey/memory/MEMORY.md")" -eq 1 ] && ok "MEMORY.md gets only the missing lines" || bad "MEMORY.md was not merged correctly"
run --apply --with-sessions >/dev/null 2>&1
[ -f "$C/projects/$nkey/session-1.jsonl" ] && ok "--with-sessions copies the transcripts" || bad "--with-sessions did not copy the transcripts"
python3 "$m" "$T/missing-dir" --from "$OLD" --claude-dir "$C" >/dev/null 2>&1; [ $? -eq 1 ] && ok "a new path that is not a directory is an error" || bad "a missing new path was accepted"
python3 "$m" "$NEW" --from "$T/work/nothing" --claude-dir "$C" >/dev/null 2>&1; [ $? -eq 1 ] && ok "an old path with no project folder is an error" || bad "a missing old project folder was accepted"
python3 "$m" "$OLD" --from "$OLD" --claude-dir "$C" >/dev/null 2>&1; [ $? -eq 1 ] && ok "the same path twice is an error" || bad "the same path was accepted"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
