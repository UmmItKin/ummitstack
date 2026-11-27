# Auto find best skill

A user turns on a SessionStart hook so each new Claude Code session starts with a reminder to pick the best installed skill. The toggle edits only its own entry in the settings file.

## Sub-features

- `toggle-on` adds the hook and keeps every other setting and hook.
- `toggle-off` removes only that hook.
- `toggle-safe` refuses a settings file that is not valid JSON and leaves it unchanged.

## How to get to it (user POV)

- Type `/auto-find-best-skill on`, `off` or `status`.

## Driving it with a temporary settings file

Preconditions:

- Never run the toggle against the real `~/.claude/settings.json` during verification. Always pass `--settings`.
- Work in a scratch folder: `W=$(mktemp -d)`, then write `$W/settings.json` as `{"model": "x", "hooks": {"PreToolUse": []}}`.

- **On.** Run `python3 skills/auto-find-best-skill/scripts/toggle.py on --settings $W/settings.json`. It prints `auto-find-best-skill: on`. The file still has `model` and `PreToolUse`, and has a `SessionStart` entry.
- **Reminder.** Read the hook command from the file and run it. It prints a line that starts with `auto-find-best-skill is on.`
- **Twice.** Run `on` again. The file has exactly one such entry.
- **Off.** Run `off`. The file equals the original again, and `$W/settings.json.before-auto-find-best-skill` exists.
- **Broken file.** Write `{ not json` to `$W/broken.json`, run `on --settings $W/broken.json`. It exits 1 and the file is unchanged.
- **Proof.** Keep the transcripts and a `diff` of the file before `on` and after `off`, which is empty.

## Gotchas

- The default settings path is the real `~/.claude/settings.json`. A recipe that forgets `--settings` changes the user's file.
- A new Claude Code session is needed before the hook runs; the current session does not reload it.
- Whether the model then follows the reminder is judgment, not something a script can prove.
