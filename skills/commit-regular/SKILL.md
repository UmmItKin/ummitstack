---
name: commit-regular
description: Toggle regular commits. When on, commit after every finished change without being asked, each with a one-line Conventional Commits message. /commit-regular on (default) or /commit-regular off.
disable-model-invocation: true
---

# Commit regular

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

- `on`, or no argument: commit regularly from now on. Reply with one line: `commit-regular: on`.
- `off`: stop committing on your own. Commit only when the user asks again. Reply with one line: `commit-regular: off`.

## While it is on
**Active every response.** Stay on until the user runs `/commit-regular off` or says "stop committing". Do not drift back to waiting for the user to ask.

- Commit after each finished, working change: a bug fixed, a feature added, a file renamed. Not after every edit, and not halfway through a change.
- Before each commit, run the project's quick checks if it has them (tests, lint, a smoke script). If they fail, fix the change or leave it uncommitted and say why. Never commit a broken state.
- Write each message with the `conventional-commit` skill: one line, as short as possible.
- Stage only the files you changed for that change. Leave the user's other uncommitted work alone.
- Never commit secrets, `.env` files, build output or large generated files.
- Never push, amend, rebase or force anything. Pushing stays the user's call.
- If the folder is not a git repository, or the user is in the middle of a merge or rebase, do not commit; say so once.
- After each commit, add one line to your reply: the short hash and the message, for example `committed a1b2c3d feat: add council skill`.
