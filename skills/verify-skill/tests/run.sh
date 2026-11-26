#!/bin/sh
# Usage: sh tests/run.sh
# Checks that static_check.py passes a good skill and fails each kind of bad one.
set -u
here=$(cd "$(dirname "$0")" && pwd)
s=$here/../scripts/static_check.py
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
expect() {
  name=$1
  want=$2
  shift 2
  "$@" >/dev/null 2>&1
  got=$?
  [ "$got" -eq "$want" ] && ok "$name" || bad "$name (exit $got, wanted $want)"
}
mk() {
  d=$T/$1
  mkdir -p "$d/scripts"
  printf -- '---\nname: %s\ndescription: Does a thing. Use when the user asks for the thing.\n---\n\n# %s\n\nRun scripts/ok.py.\n' "$1" "$1" > "$d/SKILL.md"
  printf '#!/usr/bin/env python3\n"""Usage: ok.py"""\nprint(1)\n' > "$d/scripts/ok.py"
}
mk good
expect "a good skill passes" 0 python3 "$s" "$T/good"
mk badyaml
printf -- '---\nname: badyaml\ndescription: Does a thing: with a colon. Use when asked.\n---\n\nbody ok.py\n' > "$T/badyaml/SKILL.md"
expect "an unquoted colon in the description fails" 1 python3 "$s" "$T/badyaml"
mk badname
sed -i 's/^name: badname/name: other/' "$T/badname/SKILL.md"
expect "a name that differs from the folder fails" 1 python3 "$s" "$T/badname"
mk badsyntax
printf 'def (:\n' > "$T/badsyntax/scripts/ok.py"
expect "a script that does not compile fails" 1 python3 "$s" "$T/badsyntax"
mk dash
printf 'Wait \xe2\x80\x94 this has an em dash. ok.py\n' >> "$T/dash/SKILL.md"
expect "an em dash fails" 1 python3 "$s" "$T/dash"
mk userpath
printf 'See /%s/alice/notes ok.py\n' home >> "$T/userpath/SKILL.md"
expect "a home directory path fails" 1 python3 "$s" "$T/userpath"
mk mail
printf 'Mail bob@%s.org ok.py\n' corp >> "$T/mail/SKILL.md"
expect "an email address fails" 1 python3 "$s" "$T/mail"
mk orphan
printf '#!/usr/bin/env python3\n"""Usage: lost.py"""\n' > "$T/orphan/scripts/lost.py"
python3 "$s" "$T/orphan" 2>&1 | grep -q 'WARN scripts/lost.py' && ok "an unreferenced script is warned about" || bad "an unreferenced script is not warned about"
# leak_scan.py: a private source line in a commit is found, a clean history passes
L=$here/../scripts/leak_scan.py
R=$T/repo
mkdir -p "$R" && cd "$R" && git init -q && git config user.email a@example.com && git config user.name t
printf 'this private sentence is secret\nanother private sentence here\n' > "$T/private.txt"
printf 'nothing to see here at all\n' > a.txt && git add a.txt && git commit -q -m clean
expect "leak_scan passes a clean history" 0 python3 "$L" --source "$T/private.txt" --history
printf 'this private sentence is SECRET\n' >> a.txt && git add a.txt
expect "leak_scan finds a private line in the staged diff" 1 python3 "$L" --source "$T/private.txt" --staged
expect "and ignores a phrase when told to" 0 python3 "$L" --source "$T/private.txt" --ignore "this private sentence is secret" --staged
git commit -q -m "add"
expect "and finds it in the history" 1 python3 "$L" --source "$T/private.txt" --history
expect "and finds a private line in the commit message" 1 python3 "$L" --source "$T/private.txt" --staged --message "another private sentence here"
cd "$here"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
