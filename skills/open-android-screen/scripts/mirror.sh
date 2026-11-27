#!/bin/sh
# Usage: sh mirror.sh
# Opens a live window of the phone screen with scrcpy and prints its pid. The user closes the window themselves.
# Exit codes of android-check.sh are passed through. Exit 6: scrcpy is not installed. Exit 7: scrcpy quit right away.
here=$(cd "$(dirname "$0")" && pwd)
sh "$here/android-check.sh" || exit $?
command -v scrcpy >/dev/null 2>&1 || { echo "scrcpy is not installed, so there is no live window (Arch: sudo pacman -S scrcpy). A screenshot still works"; exit 6; }
nohup scrcpy --no-audio >/dev/null 2>&1 &
pid=$!
sleep 2
kill -0 "$pid" 2>/dev/null && { echo "the live screen window is open (pid $pid)"; exit 0; }
echo "scrcpy quit right away; run scrcpy in a terminal to see why"
exit 7
