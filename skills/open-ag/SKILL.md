---
name: open-ag
description: Open a URL in a visible Chromium, Chrome or Brave window through agent-browser, reusing a saved profile, and ask which browser to use when more than one is installed. Use when the user types /open-ag, asks to open a page in the browser, or asks to use agent-browser for them.
---

# Open agent-browser

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/open-ag <url> [--browser chromium|chrome|brave|testing]`. Quote the URL. Accept a bare host too (`example.com`). If the URL is empty, ask for it instead of opening a blank window.

## Check first

If you do not already know from memory or this session that this machine has `agent-browser` and a browser, read `<skill-dir>/README.md` and follow it before opening.

## Choose the browser
1. Run `sh <skill-dir>/scripts/detect.sh`. Each line is `key`, label, path and profile, separated by tabs.
2. If `--browser <key>` was given, use that key. If it is not in the list, say which keys are available and stop.
3. If the list has one line, use it without asking.
4. If it has two or more, ask once with a single-select menu (AskUserQuestion) that lists the labels in the order printed, and no other question. If the user already chose a browser earlier in this session, use that one without asking again, unless they ask to change.

## Open
`sh <skill-dir>/scripts/open.sh <key> "<url>"`. It opens a visible window with that browser's saved profile and prints the page that opened. Reply with that URL on one line.

Brave has its own profile folder (`~/.agent-browser-profile-brave`), so it never shares a profile with Chromium or Chrome. The others keep using `~/.agent-browser-profile`.
