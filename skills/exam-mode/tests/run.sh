#!/bin/sh
# Usage: sh tests/run.sh
# Runs the real inotifywait and pandoc, with a fake notify-send that logs. Needs inotifywait and pandoc, and about 30 seconds.
set -u
here=$(cd "$(dirname "$0")" && pwd)
s=$here/../scripts
for t in inotifywait pandoc; do command -v "$t" >/dev/null 2>&1 || { echo "skip: $t is not installed (run sh scripts/check-tools.sh)"; exit 0; }; done
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
mkdir -p "$T/bin"
for tool in sh awk date stat cp sha256sum cut sort tr mkdir cat wc tail head diff grep chmod pandoc inotifywait git sleep dirname mv rm touch env id; do ln -s "$(command -v $tool)" "$T/bin/$tool"; done
printf '#!/bin/sh\nprintf "%%s\\n" "$*" >> "$FAKE_LOG"\n' > "$T/bin/notify-send"; chmod +x "$T/bin/notify-send"
run() { env PATH="$T/bin" FAKE_LOG="$T/notify.log" "$@"; }
doc() { printf '%s\n' "$2" | pandoc -f markdown -o "$1"; }
printf 'QUESTIONTEXT\n\nQ1. Name a thing.\n' > "$T/paper.md"
printf 'KEYSECRET answer is a thing\n' > "$T/key.md"
doc "$T/v1.docx" "QUESTIONTEXT

ANSWERONE"
doc "$T/v2.docx" "QUESTIONTEXT

ANSWERTWO"
doc "$T/late.docx" "QUESTIONTEXT

LATEWORD"

echo "== durations =="
for pair in "60:3600" "1h:3600" "90m:5400" "1h30m:5400" "45s:45"; do
  [ "$(run sh "$s/monitor.sh" --parse "${pair%%:*}")" = "${pair##*:}" ] && ok "duration ${pair%%:*} is ${pair##*:} seconds" || bad "duration ${pair%%:*} is wrong"
done
run sh "$s/monitor.sh" --parse banana >/dev/null 2>&1; [ $? -eq 2 ] && ok "a bad duration is exit 2" || bad "a bad duration was accepted"

echo "== the paper =="
A=$T/exams/a
run sh "$s/make-paper.sh" "$A" "$T/paper.md" "$T/key.md" >/dev/null 2>&1; c=$?
[ "$c" -eq 0 ] && [ -f "$A/paper.docx" ] && ok "make-paper builds paper.docx" || bad "make-paper failed (exit $c)"
[ "$(stat -c %a "$A/.state/key.md")" = 600 ] && ok "the answer key is mode 600" || bad "the key is not mode 600"
pandoc "$A/paper.docx" -t plain 2>/dev/null | grep -q KEYSECRET && bad "the key leaked into the paper" || ok "the key is not in the paper"
mkdir -p "$T/repo" && git -C "$T/repo" init -q 2>/dev/null; run sh "$s/make-paper.sh" "$T/repo/exam" "$T/paper.md" "$T/key.md" >/dev/null 2>&1; [ $? -eq 2 ] && ok "make-paper refuses a folder inside a git repository" || bad "make-paper wrote inside a repo"

echo "== a full exam, 8 seconds =="
run sh "$s/monitor.sh" "$A" 8s 3s & mp=$!
sleep 1; cp "$T/v1.docx" "$A/tmp.docx"; mv "$A/tmp.docx" "$A/paper.docx"
sleep 2; cp "$T/v2.docx" "$A/paper.docx"
wait "$mp"; c=$?
[ "$c" -eq 0 ] && ok "the monitor ends with exit 0 at the timeout" || bad "the monitor exit was $c"
. "$A/.state/exam.env"
[ $((END - START)) -eq 8 ] && ok "the start and end times are recorded, 8 seconds apart" || bad "start and end are wrong"
[ "${DONE:-}" = timeout ] && ok "the result is recorded as timeout" || bad "the result is '${DONE:-}'"
saves=$(wc -l < "$A/.state/saves.log")
[ "$saves" -ge 1 ] && [ "$(tail -1 "$A/.state/saves.log" | cut -d"|" -f5)" = "$(sha256sum "$T/v2.docx" | cut -c1-64)" ] && ok "the last saved version recorded is exactly the last file the student saved" || bad "the last version is wrong ($saves saves)"
[ "$(ls "$A/.state/versions" | wc -l)" -eq "$saves" ] && ok "each recorded save keeps its version" || bad "versions kept: $(ls "$A/.state/versions" | wc -l) for $saves saves"
grep -q "Exam started" "$T/notify.log" && grep -q "Time left" "$T/notify.log" && grep -q "Time is up" "$T/notify.log" && ok "notify-send said the start, the time left and the time up" || bad "notifications are missing: $(cat "$T/notify.log")"
run sh "$s/status.sh" "$A" > "$T/status.txt" 2>&1
grep -q "saves seen: $saves" "$T/status.txt" && grep -q "state: timeout" "$T/status.txt" && ! grep -q KEYSECRET "$T/status.txt" && ok "status shows the saves and never the key" || bad "status is wrong"
run sh "$s/monitor.sh" "$A" 8s >/dev/null 2>&1; [ $? -eq 2 ] && ok "the same exam cannot be started twice" || bad "an exam was started twice"
run sh "$s/collect.sh" "$A" > "$T/collect.txt" 2>&1
grep -q "saves seen: $saves" "$T/collect.txt" && grep -q "ANSWERTWO" "$A/.state/answers.txt" && ! grep -q ANSWERONE "$A/.state/answers.txt" && ok "collect grades the last version saved before the end" || bad "collect picked the wrong version: $(cat "$T/collect.txt")"
! grep -q KEYSECRET "$T/collect.txt" && ! grep -q ANSWERTWO "$T/collect.txt" && ok "collect prints a summary, not the key or the answers" || bad "collect printed the key or the answers"
sleep 1; cp "$T/late.docx" "$A/paper.docx"
run sh "$s/collect.sh" "$A" > "$T/collect2.txt" 2>&1
grep -q "edited after the end" "$T/collect2.txt" && grep -q ANSWERTWO "$A/.state/answers.txt" && ! grep -q LATEWORD "$A/.state/answers.txt" && ok "an edit after the end is reported and ignored" || bad "a late edit was not handled: $(cat "$T/collect2.txt")"

echo "== a save is seen as it happens (inotify, not polling) =="
D=$T/exams/d
run sh "$s/make-paper.sh" "$D" "$T/paper.md" "$T/key.md" >/dev/null 2>&1
run sh "$s/monitor.sh" "$D" 6s 60s & mp=$!
sleep 1; cp "$T/v1.docx" "$D/tmp.docx"; mv "$D/tmp.docx" "$D/paper.docx"
wait "$mp"
line=$(head -1 "$D/.state/saves.log"); det=$(echo "$line" | cut -d'|' -f2); mt=$(echo "$line" | cut -d'|' -f3)
[ -n "$line" ] && [ $((det - mt)) -le 1 ] && ok "a save was recorded within a second of it happening, long before the end" || bad "the save was recorded late: detected $((det - mt)) s after it happened"

echo "== a version saved after the deadline is never graded =="
E=$T/exams/e
run sh "$s/make-paper.sh" "$E" "$T/paper.md" "$T/key.md" >/dev/null 2>&1
end=$(( $(date +%s) - 100 )); mkdir -p "$E/.state/versions"; : > "$E/.state/saves.log"
printf 'START=%s\nEND=%s\nSECONDS_TOTAL=60\nPAPER=%s\nDONE=timeout\n' $((end - 60)) "$end" "$E/paper.docx" > "$E/.state/exam.env"
cp "$T/v1.docx" "$E/.state/versions/1-$((end - 5)).docx"; cp "$T/late.docx" "$E/.state/versions/2-$((end + 5)).docx"
printf '1|x|%s|1|a\n2|x|%s|1|b\n' $((end - 5)) $((end + 5)) > "$E/.state/saves.log"
run sh "$s/collect.sh" "$E" >/dev/null 2>&1
grep -q ANSWERONE "$E/.state/answers.txt" && ! grep -q LATEWORD "$E/.state/answers.txt" && ok "collect grades the version from before the deadline, not the late one" || bad "collect graded a late version"

echo "== handing in early =="
B=$T/exams/b
run sh "$s/make-paper.sh" "$B" "$T/paper.md" "$T/key.md" >/dev/null 2>&1
run sh "$s/monitor.sh" "$B" 60s 20s & mp=$!
sleep 1; run sh "$s/stop.sh" "$B" >/dev/null 2>&1; wait "$mp"; c=$?
[ "$c" -eq 3 ] && grep -q "^DONE=early" "$B/.state/exam.env" && grep -q "submitted early" "$T/notify.log" && ok "stop.sh ends the exam early with exit 3 and a notification" || bad "an early stop is wrong (exit $c)"

echo "== nothing saved =="
C=$T/exams/c
run sh "$s/make-paper.sh" "$C" "$T/paper.md" "$T/key.md" >/dev/null 2>&1
run sh "$s/monitor.sh" "$C" 2s 1s; run sh "$s/collect.sh" "$C" 2>&1 | grep -q "nothing was saved before the end" && [ ! -s "$C/.state/answers.txt" ] && ok "no save means an empty answer file and a clear message" || bad "an empty exam is not handled"

echo "== missing tools =="
mkdir -p "$T/nobin"; for tool in sh awk date stat cp sha256sum cut sort tr mkdir cat wc grep; do ln -s "$(command -v $tool)" "$T/nobin/$tool"; done
env PATH="$T/nobin" sh "$s/monitor.sh" "$A" 5s >/dev/null 2>&1; [ $? -eq 1 ] && ok "a missing inotifywait is exit 1" || bad "a missing inotifywait was not caught"
env PATH="$T/nobin" sh "$s/check-tools.sh" > "$T/tools.txt" 2>&1; c=$?
[ "$c" -eq 1 ] && grep -q "inotify-tools" "$T/tools.txt" && ok "check-tools lists what is missing and how to install it" || bad "check-tools is wrong (exit $c)"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
