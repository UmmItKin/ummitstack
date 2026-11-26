#!/bin/sh
# Usage: sh tests/run.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
s=$here/../scripts
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
mkbin() {
  d=$T/$1; mkdir -p "$d/bin" "$d/fakehome"
  for tool in sh awk cut tr ls dirname; do ln -s "$(command -v $tool)" "$d/bin/$tool"; done
  shift
  for b in "$@"; do printf '#!/bin/sh\n' > "$d/bin/$b"; chmod +x "$d/bin/$b"; done
  printf '#!/bin/sh\nfor a in "$@"; do printf "%%s\\n" "$a"; done >> "$HOME/args.log"\n[ "$1" = get ] && echo "https://example.invalid/page"\nexit 0\n' > "$d/bin/agent-browser"
  chmod +x "$d/bin/agent-browser"
}
env_for() { echo "HOME=$T/$1/fakehome PATH=$T/$1/bin"; }
det() { env $(env_for "$1") sh "$s/detect.sh"; }

mkbin all chromium google-chrome-stable brave
mkdir -p "$T/all/fakehome/.agent-browser/browsers/chrome-1"
det all > "$T/all.txt"; code=$?
[ "$code" -eq 0 ] && [ "$(cut -f1 "$T/all.txt" | tr '\n' ' ')" = "chromium chrome brave testing " ] && ok "all four browsers are listed in menu order" || bad "the list is wrong: $(cut -f1 "$T/all.txt" | tr '\n' ' ')"
mkbin braveonly brave-browser
det braveonly > "$T/b.txt"; [ "$(cut -f1 "$T/b.txt")" = brave ] && ok "Brave is found under the name brave-browser too" || bad "brave-browser was not found"
mkbin none
det none >/dev/null; [ $? -eq 1 ] && ok "no browser gives exit 1 and no lines" || bad "no browser was not reported"
mkbin chronly chromium-browser google-chrome
[ "$(det chronly | cut -f1 | tr '\n' ' ')" = "chromium chrome " ] && ok "chromium-browser and google-chrome are found" || bad "alternative names were not found"
grep -q "brave	Brave	$T/all/bin/brave	$T/all/fakehome/.agent-browser-profile-brave" "$T/all.txt" && ok "Brave has its own profile folder" || bad "Brave does not have its own profile"
grep -q "chromium	Chromium	$T/all/bin/chromium	$T/all/fakehome/.agent-browser-profile$" "$T/all.txt" && ok "Chromium keeps the existing profile folder" || bad "Chromium profile changed"

opn() { rm -f "$T/$1/fakehome/args.log"; env $(env_for "$1") sh "$s/open.sh" "$2" "$3"; }
args() { tr '\n' '|' < "$T/$1/fakehome/args.log"; }
opn all brave "https://example.com/a?x=1&y=2 z" >"$T/o.txt" 2>&1; code=$?
[ "$code" -eq 0 ] && [ "$(args all)" = "--headed|--executable-path|$T/all/bin/brave|--profile|$T/all/fakehome/.agent-browser-profile-brave|open|https://example.com/a?x=1&y=2 z|get|url|" ] && ok "open brave builds the exact command, and the URL with a space and an ampersand stays one argument" || bad "the brave command is wrong: $(args all)"
grep -q "https://example.invalid/page" "$T/o.txt" && ok "the page URL is printed" || bad "the page URL is not printed"
opn all chromium example.com >/dev/null 2>&1; [ "$(args all)" = "--headed|--executable-path|$T/all/bin/chromium|--profile|$T/all/fakehome/.agent-browser-profile|open|example.com|get|url|" ] && ok "open chromium uses its path and the shared profile" || bad "the chromium command is wrong: $(args all)"
opn all testing example.com >/dev/null 2>&1; [ "$(args all)" = "--headed|--profile|$T/all/fakehome/.agent-browser-profile|open|example.com|get|url|" ] && ok "open testing passes no executable path" || bad "the testing command is wrong: $(args all)"
opn braveonly chromium example.com >"$T/na.txt" 2>&1; code=$?
[ "$code" -eq 2 ] && grep -q "not available here: chromium; available: brave" "$T/na.txt" && [ ! -f "$T/braveonly/fakehome/args.log" ] && ok "an unavailable browser is exit 2, lists the available ones and opens nothing" || bad "an unavailable browser was not handled (exit $code)"
env $(env_for all) sh "$s/open.sh" brave >/dev/null 2>&1; [ $? -eq 2 ] && ok "a missing URL is an error" || bad "a missing URL was accepted"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
