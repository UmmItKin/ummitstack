#!/bin/sh
# Usage: sh collect.sh EXAM-DIR
# After the exam. Picks the last version saved before the end, lists saves made after the end as late (ignored), and writes
# EXAM-DIR/.state/answers.txt with the lines the student added to the blank paper. Prints a summary and the path; not the answers.
dir=${1:-}; state=$dir/.state
[ -f "$state/exam.env" ] || { echo "no exam started in '$dir'" >&2; exit 1; }
. "$state/exam.env"
grep -q '^DONE=' "$state/exam.env" || echo "note: the exam is still running"
saves=$(wc -l < "$state/saves.log")
graded=
for f in "$state"/versions/*.docx; do [ -f "$f" ] || continue; b=${f##*/}; mt=${b#*-}; mt=${mt%.docx}; [ "$mt" -le "$END" ] && graded=$f; done
echo "saves seen: $saves"
[ "$saves" -gt 0 ] && echo "first save: $(date -d "@$(head -1 "$state/saves.log" | cut -d'|' -f3)" +%H:%M:%S), last save: $(date -d "@$(tail -1 "$state/saves.log" | cut -d'|' -f3)" +%H:%M:%S), deadline: $(date -d "@$END" +%H:%M:%S)"
cur=$(stat -c %Y "$PAPER" 2>/dev/null)
[ -n "$cur" ] && [ "$cur" -gt "$END" ] && echo "the paper was edited after the end, so that version is ignored"
if [ -z "$graded" ]; then echo "nothing was saved before the end"; : > "$state/answers.txt"; exit 0; fi
pandoc "$state/blank.docx" -t plain --wrap=none > "$state/blank.txt" 2>/dev/null
pandoc "$graded" -t plain --wrap=none > "$state/submission.txt" 2>/dev/null
diff --unchanged-line-format= --old-line-format= --new-line-format='%L' "$state/blank.txt" "$state/submission.txt" > "$state/answers.txt"
echo "graded version: ${graded##*/}"
echo "answers: $state/answers.txt ($(wc -l < "$state/answers.txt") lines added to the blank paper)"
