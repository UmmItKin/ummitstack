#!/bin/sh
# Usage: sh tests/run.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
p=$here/../scripts/preflight.sh
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
mkbin() {
  d=$T/$1; mkdir -p "$d"
  for tool in sh sed head basename; do ln -s "$(command -v $tool)" "$d/$tool"; done
  shift
  for name in "$@"; do
    cat > "$d/$name" <<'SH'
#!/bin/sh
printf '%s\n' "$*" >> "$FAKE_LOG"
case "$1" in
  version) printf 'Version:   9.9.9\nGo:        go0\n' ;;
  account) echo '{"who":"HIDDENPERSON","token":"SECRETTOKEN"}'; exit "${FAKE_RC:-0}" ;;
esac
SH
    chmod +x "$d/$name"
  done
}
run() { d=$1; shift; env PATH="$T/$d" FAKE_LOG="$T/$d.log" "$@"; }
mkbin none
run none sh "$p" >"$T/none.txt" 2>&1; code=$?
[ "$code" -eq 1 ] && grep -q "https://proton-cli.lerchster.dev/install/" "$T/none.txt" && ok "a missing proton gives exit 1 and the install page" || bad "a missing proton is not handled (exit $code)"
mkbin both proton
run both sh "$p" >"$T/in.txt" 2>&1; code=$?
[ "$code" -eq 0 ] && grep -q "command: proton, version: 9.9.9" "$T/in.txt" && grep -q "signed in: yes" "$T/in.txt" && ok "signed in gives exit 0 with the version" || bad "signed in is wrong (exit $code)"
! grep -qE "HIDDENPERSON|SECRETTOKEN" "$T/in.txt" && ok "account data is never printed" || bad "account data leaked into the output"
mkbin onlycli proton-cli
run onlycli sh "$p" >"$T/cli.txt" 2>&1; grep -q "command: proton-cli" "$T/cli.txt" && ok "proton-cli is used when proton is not there" || bad "proton-cli was not found"
FAKE_RC=2 run both sh "$p" >"$T/out.txt" 2>&1; code=$?
[ "$code" -eq 2 ] && grep -q "proton account login" "$T/out.txt" && ok "nobody signed in gives exit 2 and tells the user to log in themselves" || bad "nobody signed in is wrong (exit $code)"
FAKE_RC=5 run both sh "$p" >"$T/trouble.txt" 2>&1; code=$?
[ "$code" -eq 3 ] && grep -q "could not tell" "$T/trouble.txt" && ok "a network error gives exit 3, not a false answer" || bad "a network error is wrong (exit $code)"
rm -f "$T/both.log"; run both sh "$p" work >/dev/null 2>&1
grep -q "account get --output json --no-input --profile work" "$T/both.log" && ok "the profile is passed through" || bad "the profile was not passed: $(cat "$T/both.log")"
grep -q "account get --output json --no-input" "$T/both.log" && ! grep -qiE "login|password" "$T/both.log" && ok "it only reads: no login, no password" || bad "preflight did something besides read"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
