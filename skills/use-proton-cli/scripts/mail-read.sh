#!/bin/sh
# Usage: sh mail-read.sh COMMAND-WORDS... [FLAGS...]
# Runs proton mail COMMAND-WORDS FLAGS, but only for commands that read: the command words come first, then the flags,
# for example: sh mail-read.sh messages list --limit 5 --output json. Anything else is refused and proton is not run.
# Exit 64: refused by the read-only rule. Exit 1: proton is not installed. Otherwise proton's own exit code.
bin=$(command -v proton || command -v proton-cli) || { echo "proton is not installed" >&2; exit 1; }
allowed2=" conversations-list conversations-get conversations-count messages-list messages-get messages-count drafts-list mailing-lists-list mailing-lists-get settings-get settings-list "
allowed3=" conversations-attachments-list messages-attachments-list messages-trackers-list settings-addresses-get settings-addresses-list settings-autoreply-get settings-categories-list settings-domains-get settings-domains-list settings-filters-get settings-filters-list settings-folders-list settings-forwarding-get settings-forwarding-list settings-imports-get settings-imports-list settings-labels-list settings-senders-list "
w1=${1:-}; w2=${2:-}; w3=${3:-}
refuse() { echo "refused: the mailbox is read only, and 'proton mail $*' is not a read command. Ask the user to run it themselves if they want it done" >&2; exit 64; }
case "$allowed3" in *" $w1-$w2-$w3 "*) ok=1 ;; *) case "$allowed2" in *" $w1-$w2 "*) ok=1 ;; *) ok= ;; esac ;; esac
[ -n "$ok" ] || refuse "$@"
exec "$bin" mail "$@" --no-input
