#!/bin/sh
# Usage: sh detect.sh
# Prints one line per browser that can be used: key, label, executable path (empty for agent-browser's own), profile folder, separated by tabs.
# Keys in menu order: chromium, chrome, brave, testing. Exit 1 when none is available.
first() { for n in "$@"; do p=$(command -v "$n" 2>/dev/null) && { echo "$p"; return 0; }; done; return 1; }
line() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4"; found=1; }
found=0
p=$(first chromium chromium-browser) && line chromium "Chromium" "$p" "$HOME/.agent-browser-profile"
p=$(first google-chrome-stable google-chrome) && line chrome "Google Chrome" "$p" "$HOME/.agent-browser-profile"
p=$(first brave brave-browser brave-browser-stable) && line brave "Brave" "$p" "$HOME/.agent-browser-profile-brave"
ls "$HOME"/.agent-browser/browsers/* >/dev/null 2>&1 && line testing "Chrome for Testing (agent-browser's own)" "" "$HOME/.agent-browser-profile"
[ "$found" -eq 1 ]
