#!/bin/sh
# Usage: sh make-paper.sh EXAM-DIR PAPER.md KEY.md
# Builds EXAM-DIR/paper.docx from PAPER.md with pandoc (questions only), keeps a blank copy and the answer key in EXAM-DIR/.state
# (the key is mode 600 and is not printed until the exam is over). Never run this inside a git repository.
dir=${1:-}; paper=${2:-}; key=${3:-}
[ -n "$dir" ] && [ -f "$paper" ] && [ -f "$key" ] || { echo "Usage: sh make-paper.sh EXAM-DIR PAPER.md KEY.md" >&2; exit 2; }
command -v pandoc >/dev/null 2>&1 || { echo "pandoc is not installed; run check-tools.sh" >&2; exit 1; }
[ -f "$dir/.state/exam.env" ] && { echo "this exam was already started; use a new folder" >&2; exit 2; }
up=$dir; while [ ! -d "$up" ]; do up=$(dirname "$up"); done
git -C "$up" rev-parse --git-dir >/dev/null 2>&1 && { echo "refusing: $dir is inside a git repository" >&2; exit 2; }
mkdir -p "$dir/.state" || exit 1
pandoc "$paper" -o "$dir/paper.docx" || exit 1
cp "$dir/paper.docx" "$dir/.state/blank.docx"
cp "$key" "$dir/.state/key.md" && chmod 600 "$dir/.state/key.md"
echo "$dir/paper.docx"
