#!/bin/sh
# Usage: sh monitor.sh EXAM-DIR DURATION [EVERY]
#        sh monitor.sh --parse DURATION
# Starts the clock for the paper in EXAM-DIR/paper.docx, watches the folder with inotifywait, logs every save, and sends the time left with notify-send.
# DURATION and EVERY look like 60 (minutes), 90m, 1h, 1h30m or 45s; EVERY defaults to 10m. It runs until the time is up.
# Exit 0: time is up. Exit 1: a tool is missing. Exit 2: bad arguments or the exam was already started. Exit 3: stopped early by stop.sh.
secs() {
  echo "$1" | awk '
    /^[0-9]+$/ {print $0 * 60; ok = 1; exit}
    /^[0-9]+s$/ {sub(/s$/, ""); print $0 + 0; ok = 1; exit}
    /^[0-9]+m$/ {sub(/m$/, ""); print $0 * 60; ok = 1; exit}
    /^[0-9]+h$/ {sub(/h$/, ""); print $0 * 3600; ok = 1; exit}
    /^[0-9]+h[0-9]+m$/ {split($0, a, /[hm]/); print a[1] * 3600 + a[2] * 60; ok = 1; exit}
    END {exit ok ? 0 : 1}'
}
[ "${1:-}" = "--parse" ] && { secs "${2:-}" || exit 2; exit 0; }
dir=${1:-}
dur=$(secs "${2:-}") || { echo "bad duration '${2:-}': use 60, 90m, 1h30m or 45s" >&2; exit 2; }
every=$(secs "${3:-10m}") || { echo "bad interval '${3:-}'" >&2; exit 2; }
for t in inotifywait notify-send; do command -v "$t" >/dev/null 2>&1 || { echo "$t is not installed; run check-tools.sh" >&2; exit 1; }; done
paper=$dir/paper.docx
[ -f "$paper" ] || { echo "no paper.docx in '$dir'" >&2; exit 2; }
state=$dir/.state
[ -f "$state/exam.env" ] && { echo "this exam was already started" >&2; exit 2; }
mkdir -p "$state/versions"
start=$(date +%s); end=$((start + dur))
printf 'START=%s\nEND=%s\nSECONDS_TOTAL=%s\nPAPER=%s\n' "$start" "$end" "$dur" "$paper" > "$state/exam.env"
echo $$ > "$state/monitor.pid"
: > "$state/saves.log"
fmt() { if [ "$1" -ge 3600 ]; then printf '%d h %02d min' $(($1 / 3600)) $(($1 % 3600 / 60)); else printf '%d min %02d s' $(($1 / 60)) $(($1 % 60)); fi; }
notify() { notify-send -a "Exam" "$@" >/dev/null 2>&1 || echo "$(date +%s) notify-send failed" >> "$state/events.log"; }
sig() { stat -c '%.9Y %s' "$paper"; }
last=$(sig)
n=0
check() {
  cur=$(sig 2>/dev/null) || return 0
  [ "$cur" = "$last" ] && return 0
  last=$cur; n=$((n + 1)); mt=${cur%%.*}
  cp -p "$paper" "$state/versions/$n-$mt.docx"
  echo "$n|$(date +%s)|$mt|${cur#* }|$(sha256sum "$paper" | cut -c1-64)" >> "$state/saves.log"
}
done_with() { check; echo "DONE=$1" >> "$state/exam.env"; }
marks=
t=$((start + every)); while [ "$t" -lt "$end" ]; do marks="$marks $t"; t=$((t + every)); done
[ "$dur" -gt 600 ] && marks="$marks $((end - 300))"
[ "$dur" -gt 120 ] && marks="$marks $((end - 60))"
marks=$(printf '%s\n' $marks | sort -un | tr '\n' ' ')
iw=
trap '[ -n "$iw" ] && kill "$iw" 2>/dev/null; done_with early; notify "Exam submitted early" "About $(fmt $((end - $(date +%s)))) were left"; exit 3' TERM INT
notify "Exam started" "$(date +%H:%M) to $(date -d "@$end" +%H:%M), $(fmt "$dur")"
lastmark=$start
while :; do
  now=$(date +%s); left=$((end - now))
  [ "$left" -le 0 ] && break
  for m in $marks; do
    if [ "$m" -le "$now" ] && [ "$m" -gt "$lastmark" ]; then lastmark=$m; notify "Time left: $(fmt "$left")" "Ends at $(date -d "@$end" +%H:%M)"; fi
  done
  next=$end; for m in $marks; do [ "$m" -gt "$lastmark" ] && { next=$m; break; }; done
  w=$((next - now)); [ "$w" -gt "$left" ] && w=$left; [ "$w" -gt 30 ] && w=30; [ "$w" -lt 1 ] && w=1
  inotifywait -q -t "$w" -e close_write,moved_to,create,delete "$dir" >/dev/null 2>&1 &
  iw=$!
  wait "$iw" 2>/dev/null
  iw=
  check
done
done_with timeout
notify-send -u critical -a "Exam" "Time is up" "Stop writing. The paper is collected." >/dev/null 2>&1
exit 0
