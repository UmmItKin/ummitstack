#!/bin/sh
# Usage: sh android-check.sh
# Checks adb and the phone without printing any device serial. Exit 0: one phone is ready. Exit 1: adb is not installed.
# Exit 2: no phone is connected. Exit 3: a phone is there but not ready (unauthorized or offline). Exit 4: more than one phone is ready
# and ANDROID_SERIAL is not set. The message printed says what the user has to do.
command -v adb >/dev/null 2>&1 || { echo "adb is not installed. Ask the user to install Android platform-tools (Arch: android-tools; https://developer.android.com/tools/releases/platform-tools), then to tell you to continue"; exit 1; }
list=$(adb devices 2>/dev/null | awk 'NR > 1 && NF {print $2}')
count() { printf '%s\n' "$list" | grep -c "^$1\$"; }
ready=$(count device)
if [ "$ready" -ge 2 ] && [ -z "${ANDROID_SERIAL:-}" ]; then
  echo "more than one phone is ready. Ask the user which one, then set ANDROID_SERIAL to its serial (adb devices -l lists them)"; exit 4
fi
[ "$ready" -ge 1 ] && { echo "ready: an Android phone is connected and authorized"; exit 0; }
[ "$(count unauthorized)" -ge 1 ] && { echo "the phone has not allowed this computer. Ask the user to unlock it and tap Allow on the USB debugging prompt (tick always allow), then to tell you to continue"; exit 3; }
[ "$(count offline)" -ge 1 ] && { echo "the phone shows as offline. Ask the user to unplug and replug the cable and unlock the phone, then to tell you to continue"; exit 3; }
echo "no Android phone is connected. Ask the user to connect it with a USB cable first, turn on USB debugging (Settings, Developer options) and unlock the screen, then to tell you to continue"
exit 2
