#!/bin/sh
# Usage: sh screenshot.sh [OUT.png]
# Saves the phone screen as a PNG (default: $TMPDIR/android-screen-<time>.png, never inside a repo) and prints the path.
# Exit codes of android-check.sh are passed through. Exit 5: the screen is off. Exit 8: the capture is not a PNG (no file is left).
here=$(cd "$(dirname "$0")" && pwd)
sh "$here/android-check.sh" || exit $?
out=${1:-${TMPDIR:-/tmp}/android-screen-$(date +%Y%m%d-%H%M%S).png}
wake=$(adb shell dumpsys power 2>/dev/null | grep -m1 -o 'mWakefulness=[A-Za-z]*')
case "$wake" in mWakefulness=Asleep|mWakefulness=Dozing) echo "the screen is off. Ask the user to wake and unlock the phone, then to tell you to continue"; exit 5 ;; esac
adb exec-out screencap -p > "$out" 2>/dev/null
if [ "$(head -c 4 "$out" 2>/dev/null | od -An -tx1 | tr -d ' \n')" != "89504e47" ]; then
  rm -f "$out"; echo "the capture failed or is not a PNG, so there is nothing to look at"; exit 8
fi
echo "$out"
