#!/bin/sh
# Usage: sh tests/run.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
f=$here/../scripts/fetch_list.py
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
mkdir -p "$T/bin" "$T/data"
cat > "$T/bin/gh" <<'SH'
#!/bin/sh
[ -n "${FAKE_AUTH_FAIL:-}" ] && { echo "To get started with GitHub CLI, please run:  gh auth login" >&2; exit 4; }
q=""; cursor=""
for a in "$@"; do
  case "$a" in query=*) q=${a#query=} ;; cursor=*) cursor=${a#cursor=} ;; esac
done
case "$q" in
  *"node(id"*) if [ -z "$cursor" ]; then cat "$FAKE_DIR/page1.json"; else cat "$FAKE_DIR/page2.json"; fi ;;
  *) cat "$FAKE_DIR/lists.json" ;;
esac
SH
chmod +x "$T/bin/gh"
cat > "$T/data/lists.json" <<'JSON'
{"data":{"user":{"lists":{"pageInfo":{"hasNextPage":false,"endCursor":null},"nodes":[
 {"id":"L1","slug":"tools","name":"Tools","description":"Sample tools","isPrivate":false,"items":{"totalCount":4}},
 {"id":"L2","slug":"misc","name":"Misc","description":null,"isPrivate":true,"items":{"totalCount":0}}]}}}}
JSON
repo() { printf '{"__typename":"Repository","nameWithOwner":"%s","description":%s,"stargazerCount":%s,"isArchived":%s,"pushedAt":"2026-01-02T00:00:00Z","url":"https://example.invalid/%s","primaryLanguage":{"name":"Python"},"licenseInfo":null,"repositoryTopics":{"nodes":[{"topic":{"name":"demo"}}]}}' "$1" "$2" "$3" "$4" "$1"; }
printf '{"data":{"node":{"items":{"totalCount":4,"pageInfo":{"hasNextPage":true,"endCursor":"c1"},"nodes":[%s,%s]}}}}' "$(repo ann/alpha '"First sample"' 10 false)" "$(repo bob/beta '"Second sample"' 500 true)" > "$T/data/page1.json"
printf '{"data":{"node":{"items":{"totalCount":4,"pageInfo":{"hasNextPage":false,"endCursor":null},"nodes":[%s,{"__typename":"Gist"}]}}}}' "$(repo cat/gamma null 90 false)" > "$T/data/page2.json"
g() { env FAKE_DIR="$T/data" PATH="$T/bin:$PATH" python3 "$f" "$@"; }

g https://github.com/stars/someone/lists/tools >"$T/out.txt" 2>&1; code=$?
[ "$code" -eq 0 ] && head -1 "$T/out.txt" | grep -q "Tools (someone/tools): 3 repositories, 1 items that are not repositories" && ok "a list URL works and the header counts repositories and skipped items" || bad "the URL form or the header is wrong (exit $code)"
g someone/tools >"$T/out2.txt" 2>&1 && cmp -s "$T/out.txt" "$T/out2.txt" && ok "USER/SLUG gives the same result" || bad "USER/SLUG differs from the URL form"
grep -q "^bob/beta" "$T/out.txt" && [ "$(grep -n '^bob/beta' "$T/out.txt" | cut -d: -f1)" -lt "$(grep -n '^ann/alpha' "$T/out.txt" | cut -d: -f1)" ] && ok "repositories from both pages are listed, most starred first" || bad "pagination or sorting is wrong"
grep -q "bob/beta .*ARCHIVED" "$T/out.txt" && ! grep "ann/alpha" "$T/out.txt" | grep -q ARCHIVED && ok "an archived repository is marked and others are not" || bad "the archived marker is wrong"
grep -q "cat/gamma .* | -$" "$T/out.txt" && ok "an empty description prints as a dash" || bad "an empty description is not handled"
g someone/tools --json | python3 -c "import json,sys; d=json.load(sys.stdin); assert len(d['repositories'])==3 and d['not_repositories']==1 and d['repositories'][0]['nameWithOwner']=='bob/beta'" && ok "--json is valid and complete" || bad "--json is wrong"
[ "$(g someone/tools --limit 1 | grep -c ' stars ')" -eq 1 ] && g someone/tools --limit 1 | head -1 | grep -q "showing the top 1" && ok "--limit cuts the list and says so" || bad "--limit is wrong"
g --lists someone | grep -q "^misc | Misc | 0 items | private" && ok "--lists shows the lists and marks a private one" || bad "--lists is wrong"
g someone/nope >"$T/nope.txt" 2>&1; code=$?
[ "$code" -eq 1 ] && grep -q "no list 'nope'.*tools, misc" "$T/nope.txt" && ok "an unknown list is an error that shows the available lists" || bad "an unknown list is not handled (exit $code)"
g "not a list" >/dev/null 2>&1; [ $? -eq 1 ] && ok "a bad argument is an error" || bad "a bad argument was accepted"
FAKE_AUTH_FAIL=1 g someone/tools >"$T/auth.txt" 2>&1; code=$?
[ "$code" -eq 1 ] && grep -q "gh auth login" "$T/auth.txt" && ok "a logged-out gh gives the login command" || bad "a logged-out gh is not handled (exit $code)"
mkdir -p "$T/nogh" && ln -s "$(command -v python3)" "$T/nogh/python3"
PATH="$T/nogh" python3 "$f" someone/tools >"$T/nogh.txt" 2>&1; code=$?
[ "$code" -eq 1 ] && grep -q "gh is not installed" "$T/nogh.txt" && ok "a missing gh gives the install hint" || bad "a missing gh is not handled (exit $code)"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
