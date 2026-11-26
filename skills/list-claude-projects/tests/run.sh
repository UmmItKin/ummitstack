#!/bin/sh
# Usage: sh tests/run.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
t=$here/../scripts/list_titles.py
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
C=$T/claude
mkdir -p "$T/work/alpha" "$C/projects/-fake-alpha" "$C/projects/-fake-beta" "$C/projects/-fake-empty"
ev() { printf '%s\n' "$1"; }
s=$C/projects/-fake-alpha
{ ev "{\"type\":\"user\",\"cwd\":\"$T/work/alpha\",\"message\":\"SECRETWORD aiTitle customTitle\"}"
  ev '{"type":"ai-title","aiTitle":"Old auto title"}'
  ev '{"type":"ai-title","aiTitle":"Fix the login page"}'; } > "$s/a1.jsonl"
{ ev "{\"type\":\"user\",\"cwd\":\"$T/work/alpha\"}"
  ev '{"type":"ai-title","aiTitle":"Auto but renamed"}'
  ev '{"type":"custom-title","customTitle":"my-renamed"}'; } > "$s/a2.jsonl"
{ ev "{\"type\":\"user\",\"cwd\":\"$T/work/alpha\"}"; ev '{"type":"custom-title","customTitle":"  "}'; ev 'not json {{{'; } > "$s/a3.jsonl"
{ ev '{"type":"user","cwd":"/nonexistent/place/beta"}'; ev '{"type":"ai-title","aiTitle":"Beta thing"}'; } > "$C/projects/-fake-beta/b1.jsonl"
i=0
while [ $i -lt 25 ]; do ev "{\"type\":\"ai-title\",\"aiTitle\":\"bulk $i\"}" > "$C/projects/-fake-empty/e$i.jsonl"; i=$((i + 1)); done
run() { python3 "$t" --claude-dir "$C" "$@"; }
run >"$T/out.txt" 2>&1; code=$?
[ "$code" -eq 0 ] && head -1 "$T/out.txt" | grep -q "3 projects, 29 sessions; named 1, auto-titled 27, untitled 1" && ok "the summary line counts projects, sessions and each kind" || bad "the summary line is wrong (exit $code)"
grep -q "^$T/work/alpha  (3 sessions)" "$T/out.txt" && ok "the project path comes from the recorded working directory" || bad "the path is not the recorded working directory"
grep -q "my-renamed" "$T/out.txt" && ! grep -q "Auto but renamed" "$T/out.txt" && ok "a session with both titles is listed once, under its own title" || bad "a session with both titles is listed twice or wrongly"
grep -q "Fix the login page" "$T/out.txt" && ! grep -q "Old auto title" "$T/out.txt" && ok "the latest auto title wins" || bad "an old auto title was used"
grep -q "1 sessions have no title" "$T/out.txt" && ok "an empty or missing title is counted as untitled" || bad "untitled sessions are not counted"
! grep -q "SECRETWORD" "$T/out.txt" && ok "conversation text is never printed" || bad "conversation text leaked into the output"
grep -q "Named (you set the title)" "$T/out.txt" && grep -q "Auto (what the session was doing)" "$T/out.txt" && ok "the two groups are listed separately" || bad "the groups are missing"
grep -q "/nonexistent/place/beta  \[folder no longer exists\]" "$T/out.txt" && ok "a project whose folder is gone is marked" || bad "a missing folder is not marked"
grep -q "\.\.\. and 5 more" "$T/out.txt" && ok "a long group is cut at 20 titles and says how many more" || bad "the default limit is wrong"
run --all | grep -q "bulk 24" && ok "--all shows every title" || bad "--all does not show every title"
run --limit 2 | grep -q "\.\.\. and 23 more" && ok "--limit N is respected" || bad "--limit N is not respected"
run beta | head -1 | grep -q "^1 projects" && ok "a filter keeps only matching project paths" || bad "the filter is wrong"
run --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert len(d)==3 and any(p['named']==['my-renamed'] for p in d)" && ok "--json is valid" || bad "--json is wrong"
mkdir -p "$T/noproj" && python3 "$t" --claude-dir "$T/noproj" >/dev/null 2>&1; [ $? -eq 1 ] && ok "a missing projects folder is an error" || bad "a missing projects folder was accepted"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
