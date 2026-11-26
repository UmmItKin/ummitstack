---
name: verify-skill
description: Verify an agent skill in one shot, with no questions asked unless a sample input is missing. Runs static checks, the skill's own tests, then a cold-start run by a fresh low-effort subagent that follows only the SKILL.md, and fixes the gaps it reports. Use when the user types /verify-skill or asks to check, test or harden a skill, especially before publishing it.
---

# Verify a skill

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/verify-skill <skill-dir> [sample-input]`. The skill dir is a folder with a `SKILL.md`. Run it start to finish without asking the user anything. The only allowed question is the menu in step 3, and only when there is no sample input.

A skill that passes its author's own tests can still fail for a reader who has no memory of how it was built. Three cold-start runs on a PDF skill each found a real bug that its own tests had missed: a required file with no producer, a gate that did not block closing, and a stop path that was documented in one place only. This skill makes that check routine.

## Rules
- Never edit the skill under test until the cold-start run has reported. Fix what it reports, at the highest level that works: a script or gate first, a test second, wording last.
- The cold-start subagent is `sonnet` at low effort, never another model or a higher effort, and fresh every round. It reads only the SKILL.md and the files that SKILL.md points to. Never tell it how the skill works or what went wrong before.
- Never commit, push or delete anything. Report what you changed.
- Never accept a loss or choose an option on the skill's behalf during the cold-start run. The subagent takes the safest option and says so.
- At most 3 rounds. Then report what is left.

## Steps
1. **Static.** `python3 <this-skill-dir>/scripts/static_check.py <skill-dir>`. Fix every ERROR. Read the WARN lines and fix the ones that are real. Rerun until there are no errors.
2. **Tests.** If the skill has `tests/run.sh`, run `sh tests/run.sh`. A failure or a crash counts as a failure. Fix the skill, not the test, unless the test is wrong, and say why.
3. **Sample input.** Use the sample input from the arguments. Otherwise look for `tests/make_fixture.py` or a fixture folder in the skill and generate one in a scratch folder. If there is none, ask once with a menu: give a path, let the skill author a fake sample, or skip the cold-start run (and say in the report that the skill was not run cold). Never use a file with real personal content.
4. **Cold start.** Start one fresh subagent with the prompt in `references/cold-start.md`, filled in with the skill dir, the sample input and a new empty out-dir. Do not run the skill yourself at the same time.
5. **Sort the report.** Each point the subagent lists is one of: a bug (the skill does the wrong thing or lets a wrong result through), a gap (something is missing, such as a file nothing writes or a step that is not documented), or a limitation of the test (for example the subagent cannot ask a question). Fix bugs and gaps. Ignore limitations, but note them.
6. **Repeat** steps 2 to 5 with a new subagent until a round reports no bug and no gap, or 3 rounds are used.
7. **Report** in a few lines: the rounds, each bug and gap with the fix and its level, what was ignored and why, what was not checked (for example, the skill was not run with the standard or deep profile, or on another system), and the files changed. Do not commit. If the user wants it, they say so.

Read `references/cold-start.md` for the prompt and how to read the report.
