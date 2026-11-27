#!/bin/sh
# Usage: sh sync.sh
# Says whether the files listed under "Covers:" in coverage.md changed after the sync commit, in a commit or in the working tree.
# Exit 0: in step. Exit 1: the code moved, so the verification needs another look.
here=$(cd "$(dirname "$0")" && pwd)
cov=$here/../coverage.md
root=$(cd "$here/../../../.." && pwd)
sync=$(sed -n 's/^Sync commit: *//p' "$cov" | head -1)
files=$(awk '/^Covers:/{on=1; next} on && /^- /{sub(/^- /,""); print; next} on{exit}' "$cov")
[ -n "$sync" ] && [ -n "$files" ] || { echo "coverage.md has no Sync commit or no Covers list" >&2; exit 1; }
git -C "$root" cat-file -e "$sync" 2>/dev/null || { echo "sync commit $sync is not in this repository" >&2; exit 1; }
changed=$(for f in $files; do git -C "$root" diff --name-only "$sync" -- "$f"; done)
if [ -z "$changed" ]; then echo "in step: $files unchanged since $sync"; exit 0; fi
echo "the code moved since $sync:"; echo "$changed"
for f in $changed; do git -C "$root" diff --stat "$sync" -- "$f" | tail -1; done
exit 1
