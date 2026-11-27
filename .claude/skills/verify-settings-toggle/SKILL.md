---
name: verify-settings-toggle
description: Check that the auto-find-best-skill toggle never loses or damages the user's Claude Code settings, by running the real toggle.py on every settings file in a stated space. Use when changing skills/auto-find-best-skill/scripts/toggle.py, when a change touches how it reads or writes settings.json, or before trusting a claim that the toggle is safe.
metadata:
  internal: true
---

# Verify the settings toggle

## What is promised, and the harm if it breaks
`toggle.py` edits the user's real `~/.claude/settings.json`, which holds their model choice, environment variables, hooks and plugins. It promises to change only its own entry and to leave a file it cannot read alone. If that breaks, a user silently loses a hook or setting they wrote, or the file stops loading.

The checked promises, in plain words:
1. `on` changes nothing of yours except adding its own entry.
2. `off` removes only its own entry.
3. `on` then `off` gives back your original file.
4. `on` twice gives the same file as `on` once.
5. `status` says on exactly when its own entry is there.
6. A file it cannot understand is not changed, and you get a clear message, not a Python error.

Its own entry means the group exactly as `on` writes it. A hook of yours that only mentions the name, or shares a group with it, is yours.

## Tool and why
The real `toggle.py` is run in-process on every settings file in a bounded space. There is no hand model, so nothing can drift from the code. A model checker such as TLA+ would not help: this is about whether data comes out unchanged, not about the order of events. Python has no verifier that runs on the code here, so the check enumerates the inputs. It needs only `python3`.

## Scope
661 settings files: two bases (empty, and one with other settings), a `hooks` object that is missing, empty or has another event, and every sequence of up to three groups chosen from five kinds (a plain other hook, an empty group, its own entry, a group that shares a command with its own hook, a hook that mentions the name), plus 11 malformed files, each tried with `on`, `off` and `status`. A pass covers that space, not every possible settings file, and not a disk that fails while writing. When a known finding is fixed, a violation that it was hiding can appear, so rerun and read the new lines.

## Run it
```sh
python3 .claude/skills/verify-settings-toggle/scripts/check.py     # about a second
python3 .claude/skills/verify-settings-toggle/scripts/prove-catches.py   # can the check fail?
sh .claude/skills/verify-settings-toggle/scripts/sync.sh           # has the code moved?
```
`check.py` exits 0 when every violation is a known finding, and 1 on a new violation or on a known finding that no longer occurs. Each line gives the kind, how many files, and the smallest example in the file's own words (`<OUR ENTRY>` and `<OUR HOOK>` stand for what `on` writes).

## Is a change in scope
Read `coverage.md`. If `sync.sh` says the code moved, or your change touches `ours()`, `groups()`, `load()`, `save()` or the branches of `main()` in `skills/auto-find-best-skill/scripts/toggle.py`, run the three commands above.

## Read a result
- **A NEW line** is a real bug unless the example shows something this scope should not contain. Look at the smallest example, then at the branch it hits.
- **A line with `:plain`** means no unusual shape was needed. That is the most serious kind: ordinary files break.
- **A modeling error** shows up as a violation whose example is a file the tool is allowed to treat differently (for example you decided a group that shares a command should count as its own). Then change the promise in this file and `check.py` together, and say why.
- **FIXED** means a known finding no longer occurs. Remove its line from `known-findings.txt`.
- **MISSED** in `prove-catches.py` means the check is blind to a break it used to catch. Treat that as a failure of the verification, not of the code. **STALE** means `toggle.py` changed where a break was applied; update `mutants.json`.

## Known findings
`known-findings.txt` lists 20 kinds of violation in three findings. They are reported, not hidden, and the product code was not changed.
- **F1.** A hook of yours that mentions `auto-find-best-skill` in its command, or sits in a group with the tool's own hook, is treated as the tool's. `on` and `off` delete it (the whole group), and `status` says on.
- **F2.** An empty `hooks` object or an empty `SessionStart` list in your file is dropped by `off`, so `on` then `off` does not give back the file.
- **F3.** A settings file with an unexpected shape (`hooks` as a list or null, a null group, a command that is not text) makes it crash with a Python error. A `SessionStart` that is an object is silently replaced by a list.
Do not change `toggle.py` to fix these unless the user asks.

## When a change is intended
Change the code, run `check.py`, and decide each difference: a regression to fix, or a promise to change on purpose. Update `known-findings.txt` and `mutants.json` to match, run `prove-catches.py`, and only then set `Sync commit` in `coverage.md` to the new commit. Move it forward only after you have confirmed that the checks describe the code at that commit.
