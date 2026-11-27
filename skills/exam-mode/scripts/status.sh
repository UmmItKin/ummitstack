#!/bin/sh
# Usage: sh status.sh EXAM-DIR
# Read only. Prints the start and end time, the time left, how many saves were seen and when the last one was. It never prints the paper or the key.
state=${1:-}/.state
[ -f "$state/exam.env" ] || { echo "no exam started in '${1:-}'" >&2; exit 1; }
. "$state/exam.env"
now=$(date +%s); left=$((END - now)); [ "$left" -lt 0 ] && left=0
saves=$(wc -l < "$state/saves.log")
echo "start: $(date -d "@$START" '+%Y-%m-%d %H:%M:%S')"
echo "end:   $(date -d "@$END" '+%Y-%m-%d %H:%M:%S')"
echo "time left: $((left / 60)) min $((left % 60)) s"
echo "state: ${DONE:-running}"
echo "saves seen: $saves"
[ "$saves" -gt 0 ] && echo "last save: $(date -d "@$(tail -1 "$state/saves.log" | cut -d'|' -f3)" '+%H:%M:%S')"
exit 0
