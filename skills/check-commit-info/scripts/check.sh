#!/bin/sh
# Usage: check.sh ["commit message"]. Run after staging, before committing.
# Exit 0 clean, 1 blocks the commit, 2 needs one user confirmation.
git rev-parse --git-dir >/dev/null 2>&1 || { echo "stop not-a-git-repository"; exit 1; }
stop=0; ask=0
name=$(git config user.name); email=$(git config user.email)
[ -n "$name" ] || { echo "stop identity user.name-not-set"; stop=1; }
[ -n "$email" ] || { echo "stop identity user.email-not-set"; stop=1; }
if [ -n "$email" ] && [ -n "$(git remote)" ]; then
  case "$email" in
    *@gmail.com|*@outlook.com|*@hotmail.com|*@yahoo.com|*@icloud.com|*@qq.com)
      echo "ask identity free-mailbox-email-in-public-history"; ask=1 ;;
  esac
fi
git diff --cached --quiet && { echo "stop nothing-staged"; exit 1; }

EMAIL='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
HOME_PATH='/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+|[A-Za-z]:\\Users\\[A-Za-z0-9_.-]+'
TOKEN='AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|xox[abprs]-[A-Za-z0-9-]+|sk-[A-Za-z0-9]{20,}|BEGIN [A-Z ]*PRIVATE KEY'
OK_EMAIL=':[^:]*@(example\.(com|org|net)|users\.noreply\.github\.com)$'
OK_PATH=':/(home|Users)/(user|you|name|username|example|runner)$'

files() { git diff --cached --name-only -z; }
report() { if [ -n "$2" ]; then echo "$2" | sed "s/^/stop $1 /"; stop=1; fi; }
scan() {
  out=$(files | xargs -0 git grep --cached -noE "$2" -- 2>/dev/null)
  [ -n "${3:-}" ] && out=$(echo "$out" | grep -vE "$3")
  report "$1" "$(echo "$out" | cut -d: -f1,2 | sort -u | grep .)"
}
own() {
  [ -n "$2" ] || return 0
  report "$1" "$(files | xargs -0 git grep --cached -nFw -e "$2" -- 2>/dev/null | cut -d: -f1,2 | sort -u)"
}

report secret-file "$(git diff --cached --name-only | grep -Ei '(^|/)(\.env[^/]*|id_(rsa|ed25519)[^/]*|[^/]*\.(pem|key|p12|pfx)|credentials[^/]*)$' | grep -viE '\.(example|sample|template)$')"
scan email "$EMAIL" "$OK_EMAIL"
scan home-path "$HOME_PATH" "$OK_PATH"
scan token "$TOKEN"
own own-name "$name"
own own-login "$(id -un)"
own own-home "$HOME"

if [ -n "${1:-}" ]; then
  if printf '%s\n' "$1" | grep -qE "$EMAIL|$HOME_PATH|$TOKEN"; then echo "stop message personal-info"; stop=1; fi
  for v in "$name" "$(id -un)" "$HOME"; do
    if [ -n "$v" ] && printf '%s\n' "$1" | grep -qFw -e "$v"; then echo "stop message own-name-or-login"; stop=1; break; fi
  done
fi

[ "$stop" = 1 ] && exit 1
[ "$ask" = 1 ] && exit 2
echo ok
