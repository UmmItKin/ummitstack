---
name: open-ag
description: Open a URL in a visible Chromium or Chrome window through agent-browser, reusing the saved profile at ~/.agent-browser-profile, then print the page URL. Use when the user types /open-ag, asks to open a page in the browser, or asks to use agent-browser for them.
---

# Open agent-browser

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

## Check first

If you do not already know from memory or this session that this machine has `agent-browser` and a browser, read `<skill-dir>/README.md` and follow it before opening.

## Open

Open the URL in a visible window with the saved profile, using Chromium or Chrome stable if either is installed, else agent-browser's own Chrome for Testing:

```sh
exe=$(command -v chromium || command -v google-chrome-stable || true)
agent-browser --headed ${exe:+--executable-path "$exe"} --profile ~/.agent-browser-profile open "<url>" && agent-browser get url
```

- Quote the URL. Accept a bare host too (`example.com`). If the argument is empty, ask for the URL instead of opening a blank window.
- The second command prints the page that opened. Reply with that URL on one line.
