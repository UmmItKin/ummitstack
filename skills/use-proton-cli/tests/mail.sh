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
for tool in sh; do ln -s "$(command -v $tool)" "$T/bin/$tool"; done
printf '#!/bin/sh\nprintf "%%s\\n" "$*" >> "$FAKE_LOG"\n' > "$T/bin/proton"
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
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
