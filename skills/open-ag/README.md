# Prerequisite check

Read this only when you do not already know, from memory or this session, that this machine has `agent-browser` and a browser.

```sh
command -v agent-browser && sh <skill-dir>/scripts/detect.sh
```

- No `agent-browser`: tell the user in one line that it installs with `npm i -g agent-browser`, and stop.
- `detect.sh` prints nothing (exit 1): no Chromium, Chrome, Brave or agent-browser browser. Tell the user to install one of them, or run `agent-browser install` for Chrome for Testing.
- Everything present: say nothing, just open.
