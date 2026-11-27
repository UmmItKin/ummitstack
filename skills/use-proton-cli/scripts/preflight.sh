#!/bin/sh
# Usage: sh preflight.sh [PROFILE]
# Says which proton command is installed, its version, and whether someone is signed in. It never prints account data.
# Exit 0: signed in. Exit 1: not installed. Exit 2: nobody signed in or Proton refused. Exit 3: could not tell.
bin=$(command -v proton || command -v proton-cli) || { echo "proton is not installed. Ask the user to install it themselves (https://proton-cli.lerchster.dev/install/) and sign in with proton account login, then to tell you to continue"; exit 1; }
ver=$("$bin" version 2>/dev/null | sed -n 's/^Version: *//p' | head -1)
echo "command: $(basename "$bin"), version: ${ver:-unknown}"
if [ -n "${1:-}" ]; then set -- --profile "$1"; else set --; fi
"$bin" account get --output json --no-input "$@" >/dev/null 2>&1
case $? in
  0) echo "signed in: yes"; exit 0 ;;
  2) echo "signed in: no, or Proton refused. Ask the user to sign in themselves with proton account login in their own terminal, then to tell you to continue"; exit 2 ;;
  *) echo "could not tell whether anyone is signed in (network or Proton trouble)"; exit 3 ;;
esac
