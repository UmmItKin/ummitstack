---
name: verify-ummitstack
description: Prove that the skills in this repo work the way a user gets them, by installing a skill from this checkout into a throwaway HOME with npx skills add and running the installed copy. Use when changing anything under skills/ or scripts/, before pushing, or when asked to verify, smoke-test or prove a skill in ummitstack.
metadata:
  internal: true
---

# Verify ummitstack

ummitstack is a collection of agent skills that users install with `npx skills add`. There is no server to start. What a user touches is the installed copy of a skill: its `SKILL.md`, its scripts and its tests. This skill proves that copy works, not only the files in `skills/`. Read `features/README.md` first, then the feature file that matches what you changed.

## Launch
Nothing to start. Check the tools, then run the repo's own gate once:

```sh
sh .claude/skills/verify-ummitstack/scripts/doctor.sh
sh scripts/check.sh
```

`check.sh` runs every skill's `tests/run.sh`, the TLA+ model check (it needs `java` and the network once) and the identical-files check. A skill's tests skip with a message when a tool is missing, so read the output for `skip:` lines before calling it a pass. Tools per skill: `sh skills/pdf-reverse-pandoc/scripts/setup.sh`.

## Doctor
`sh .claude/skills/verify-ummitstack/scripts/doctor.sh` is read-only. It checks that this is the ummitstack repo, that `git`, `python3` and `npx` exist, that the installer finds as many skills as there are folders under `skills/` (a mismatch means a skill has an invalid frontmatter and is silently skipped), and how many uncommitted changes there are. Run it first whenever anything looks off.

## Drive
For one skill, install it the way a user does and check the installed copy:

```sh
sh .claude/skills/verify-ummitstack/scripts/prove-install.sh <skill> [evidence-dir]
```

Then drive the user-facing behavior of what you changed with the recipe in its feature file. Always use throwaway locations for anything that writes: a scratch folder for outputs, and `--settings <file>` or `--claude-dir <dir>` for the skills that edit `~/.claude`. Never point a recipe at the real `~/.claude`.

## Evidence
Every proof keeps: the command, its output, and the exit code, plus a second view of the result (for an install, the diff against `skills/<skill>`; for a rebuild, the four gate lines and `gates.json`). Proof standards:
- Run the real user path: install through `npx skills add`, run the installed scripts, use the skill's own commands. Do not call internals or edit files by hand to make a check pass.
- A passing test count is not proof by itself. Open the output and confirm no `skip:` line hides the part you changed.
- A failure the skill reports on purpose (a missing font, a scanned PDF) is evidence too. Record it, do not hide it.
Evidence goes to `${TMPDIR:-/tmp}/verify-ummitstack/<time>-<name>/`. Cleanup never removes it.

## Cleanup
`prove-install.sh` removes only the throwaway HOME it created. If you started other scratch folders, remove those by their exact paths. Do not delete anything in the user's folders, and never stop processes by name.

## Helpers
- `scripts/doctor.sh`: the read-only check above.
- `scripts/prove-install.sh <skill> [evidence-dir]`: installs into a throwaway HOME, then checks that the installed copy is identical to the repo, passes `static_check.py`, passes its own `tests/run.sh` from the installed location, and that your real `~/.claude/skills` is unchanged. It prints PASS or FAIL per check and the evidence folder, and exits 1 on any FAIL.

## What is not covered
The cold-start run (a fresh subagent following only the SKILL.md) is the `verify-skill` skill's job. Skills that need a live service, such as `open-ag` with a real browser window, are checked only through their scripts with fakes, so a real window needs a person to look at it once.
