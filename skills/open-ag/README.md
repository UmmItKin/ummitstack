# Prerequisite check

Read this only when you do not already know, from memory or this session, that this machine has `agent-browser` and a browser.

```sh
command -v agent-browser chromium google-chrome-stable; ls ~/.agent-browser/browsers 2>/dev/null
```

- No `agent-browser`: tell the user in one line that it installs with `npm i -g agent-browser`, and stop.
- No `chromium`, no `google-chrome-stable` and no browser in `~/.agent-browser/browsers`: tell the user to install Chromium or Chrome, or run `agent-browser install` for Chrome for Testing. The open command then falls back to agent-browser's own browser.
- Everything present: say nothing, just open.
