#!/bin/sh
# Usage: sh check-tools.sh
# Checks the tools exam mode needs and prints how to install what is missing. It never installs anything. Exit 0: all there. Exit 1: something is missing.
miss=
for t in inotifywait notify-send pandoc; do command -v "$t" >/dev/null 2>&1 || miss="$miss $t"; done
[ -z "$miss" ] && { echo "all tools found"; exit 0; }
echo "missing:$miss"
echo "Arch: sudo pacman -S inotify-tools libnotify pandoc   (inotifywait is in inotify-tools, notify-send is in libnotify)"
echo "Ask the user to install them themselves, then to tell you to continue"
exit 1
