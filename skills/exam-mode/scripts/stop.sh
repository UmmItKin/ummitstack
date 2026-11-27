#!/bin/sh
# Usage: sh stop.sh EXAM-DIR
# Ends the exam early (the student handed in): stops the monitor it started, by the pid it wrote, and waits until the result is recorded.
state=${1:-}/.state
[ -f "$state/monitor.pid" ] || { echo "no running exam in '${1:-}'" >&2; exit 1; }
grep -q '^DONE=' "$state/exam.env" && { echo "the exam has already ended"; exit 0; }
kill -TERM "$(cat "$state/monitor.pid")" 2>/dev/null
i=0; while [ "$i" -lt 50 ]; do grep -q '^DONE=' "$state/exam.env" && { echo "the exam ended early"; exit 0; }; sleep 0.1; i=$((i + 1)); done
echo "the monitor did not stop in 5 seconds" >&2; exit 1
