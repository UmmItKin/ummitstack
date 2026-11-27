#!/bin/sh
# Usage: sh tests/mail.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
g=$here/../scripts/mail-read.sh
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
mkdir -p "$T/bin"
for tool in sh python3 mktemp dirname rm cat; do ln -s "$(command -v $tool)" "$T/bin/$tool"; done
printf '#!/bin/sh\nprintf "%%s\\n" "$*" >> "$FAKE_LOG"\n[ -n "${FAKE_OUT:-}" ] && cat "$FAKE_OUT"\n[ -n "${FAKE_ERR:-}" ] && printf "%%s\\n" "$FAKE_ERR" >&2\nexit "${FAKE_RC:-0}"\n' > "$T/bin/proton"
chmod +x "$T/bin/proton"
g() { rm -f "$T/log"; env PATH="$T/bin" FAKE_LOG="$T/log" sh "$g" "$@" >/dev/null 2>"$T/err"; }
allow() {
  name=$1; shift
  g "$@"; code=$?
  [ "$code" -eq 0 ] && [ -f "$T/log" ] && ok "allowed: $name" || bad "not allowed but should be: $name (exit $code)"
}
refuse() {
  name=$1; shift
  g "$@"; code=$?
  [ "$code" -eq 64 ] && [ ! -f "$T/log" ] && ok "refused and proton not run: $name" || bad "should be refused: $name (exit $code, proton run: $([ -f "$T/log" ] && echo yes || echo no))"
}
allow "messages list" messages list --limit 5 --output json
allow "messages get with a target" messages get "some subject" --render text
allow "conversations count" conversations count
allow "attachments list" messages attachments list REF
allow "a settings list" settings filters list
for v in send reply forward move trash delete empty label unlabel star unstar update export unsubscribe receipt; do refuse "messages $v" messages $v REF; done
refuse "messages mark read" messages mark read REF
refuse "messages mark phishing" messages mark phishing REF
refuse "attachments download" messages attachments download REF
refuse "conversations trash" conversations trash REF
refuse "drafts create" drafts create
refuse "drafts send" drafts send REF
refuse "settings filters delete" settings filters delete X
refuse "settings smtp-tokens get (it prints a token)" settings smtp-tokens get X
refuse "a mutating word placed before a flag" messages trash --yes
refuse "a flag first" --yes messages trash REF
refuse "a mutating verb whose target is named list" messages trash list
refuse "a mutating verb whose target is named get" messages trash get
refuse "a non-mail command" account get
refuse "nothing at all"
g messages list --limit 1; grep -q -- "mail messages list --limit 1 --no-input" "$T/log" && ok "proton gets mail, the words, the flags and --no-input" || bad "the command line is wrong: $(cat "$T/log")"
env PATH="$T/nobin" FAKE_LOG="$T/log" /bin/sh "$g" messages list >/dev/null 2>&1; [ $? -eq 1 ] && ok "a missing proton is exit 1" || bad "a missing proton is not exit 1"
echo "== links in mail are never read =="
addr=$(printf 'who%sexample.invalid' '@')
{
  echo 'Hello team. See https://evil.example.invalid/login?id=1&x=2 and http://bad.example.invalid.'
  echo 'Also www.shop.example.invalid/path, mailto:victim.example.invalid, ftp://files.example.invalid/x'
  echo 'Bare login.example.invalid/verify?token=abc, hxxps://hx.example.invalid/q and obf[.]example[.]invalid here.'
  printf 'Safe: report.pdf notes.md v1.2.3 at 10.30 from %s\n' "$addr"
} > "$T/text.txt"
cat > "$T/json.txt" <<'JSON'
{"body":"go to https://evil.example.invalid/a?x=1\u0026y=2 now \"https://quote.example.invalid/q\" end","count":1}
JSON
printf '%s\n' 'see https://errlink.example.invalid/e' > "$T/err.txt"
FAKE_OUT="$T/text.txt" g messages get X
out=$(env PATH="$T/bin" FAKE_LOG="$T/log" FAKE_OUT="$T/text.txt" sh "$g" messages get X 2>/dev/null)
for needle in evil bad.example shop.example victim files.example login.example hx.example "obf\[" ; do
  printf '%s' "$out" | grep -q "$needle" && bad "a link still shows: $needle"
done
[ "$(printf '%s' "$out" | grep -o 'link removed' | wc -l)" -ge 8 ] && ok "every link in the text is replaced with [link removed]" || bad "the links were not all replaced: $(printf '%s' "$out" | grep -o 'link removed' | wc -l)"
printf '%s' "$out" | grep -qF "report.pdf notes.md v1.2.3 at 10.30 from $addr" && ok "file names, versions, times and an email address are left alone" || bad "ordinary text was changed"
outj=$(env PATH="$T/bin" FAKE_LOG="$T/log" FAKE_OUT="$T/json.txt" sh "$g" messages get X 2>/dev/null)
printf '%s' "$outj" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['count']==1 and 'example.invalid' not in d['body'] and 'link removed' in d['body']" && ok "JSON stays valid and its links are removed, even with escaped characters" || bad "the JSON output is wrong: $outj"
env PATH="$T/bin" FAKE_LOG="$T/log" FAKE_OUT="$T/text.txt" FAKE_ERR="$(cat "$T/err.txt")" sh "$g" messages get X 2>"$T/e2" >/dev/null
grep -q errlink "$T/e2" && bad "a link in an error message still shows" || ok "links in error messages are removed too"
env PATH="$T/bin" FAKE_LOG="$T/log" FAKE_OUT="$T/text.txt" FAKE_RC=5 sh "$g" messages get X >/dev/null 2>&1; [ $? -eq 5 ] && ok "proton's own exit code is kept" || bad "the exit code was lost"
mkdir -p "$T/nopy"; for tool in sh mktemp dirname rm cat; do ln -s "$(command -v $tool)" "$T/nopy/$tool"; done; cp "$T/bin/proton" "$T/nopy/proton"
env PATH="$T/nopy" FAKE_LOG="$T/log2" FAKE_OUT="$T/text.txt" sh "$g" messages get X >"$T/nopy.out" 2>/dev/null; code=$?
[ "$code" -eq 1 ] && [ ! -s "$T/nopy.out" ] && [ ! -f "$T/log2" ] && ok "without python3 nothing is run and nothing is printed" || bad "the guard did not fail closed (exit $code)"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
