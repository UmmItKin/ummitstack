# Verify a skill

A maintainer checks a skill before publishing it: static checks catch an invalid frontmatter, a script that does not compile, forbidden glyphs and personal paths.

## Sub-features

- `static-check` checks one skill folder and exits 1 on an error.
- `leak-scan` compares staged changes or history with private source files.
- `cold-start` (a fresh subagent follows the SKILL.md) is covered by the skill's own instructions, not by this map.

## How to get to it (user POV)

- Type `/verify-skill <skill-dir>`.
- Or run `python3 skills/verify-skill/scripts/static_check.py <skill-dir>`.

## Driving it with the scripts

Preconditions:

- Work in a scratch folder for anything you create.

- **Pass.** Run `python3 skills/verify-skill/scripts/static_check.py skills/verify-skill`. It prints `verify-skill: 0 errors, 0 warnings` and exits 0.
- **Fail.** Copy a skill to `$W/bad`, change its `description` to contain `: `, and run the check on `$W/bad`. It prints an `ERROR` line about invalid YAML and exits 1.
- **Leak scan.** Write a text file with one private-looking sentence, commit it in a scratch git repo, and run `python3 skills/verify-skill/scripts/leak_scan.py --source <file> --history`. It prints a `HIT` line and exits 1.
- **Proof.** Keep both transcripts and exit codes.

## Gotchas

- `static_check.py` reports errors on two older skills at the time of writing (an arrow glyph in `review-pr/scripts/report.py` and detector patterns in `unslop-writing/scripts/scan.py`). Do not treat all skills passing as the bar; treat new errors as the failure.
- `leak_scan.py` needs the private source files, which are never stored in the repo. Use a made-up file for verification.
- A `WARN` is not a failure, but an unreferenced script means an agent will not know to use it.
