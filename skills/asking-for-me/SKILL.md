---
name: asking-for-me
description: Make study material on a topic with a checked pipeline. The parent writes questions, exercises and study notes, a fresh subagent solves them blind and tries to refute the answers, a script validates the result, and the asking-for-me-* skills render the pages. Lean by default, with optional deeper profiles. Use when the user types /asking-for-me or asks for verified practice material on a topic.
---

# Asking for me

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/asking-for-me <topic> [--kinds study,quiz,exercise,video] [--profile quick|standard|deep] [--source <path>]`. Defaults: kinds `study,quiz`, profile `quick`, no source. With no topic, ask for one.

One agent that writes its own questions and checks them leaves wrong keys and ambiguous stems. This skill separates writing from checking, keeps all state in one `run.json`, and lets scripts do the format checks. Subagents cost tokens, so the default uses one.

## Rules
- **You write; subagents check.** In `quick` and `standard` you write every item yourself. Subagents only research, review, solve or refute, and never write the final files.
- **One writer of state.** Only you write `run.json`. A subagent returns one JSON object and writes no files.
- **Respect the budget.** The budget is the maximum number of subagents. Tell the user the planned count before starting. `quick` starts without asking; `standard` and `deep` ask once.
- **Batch.** One subagent checks all items of a kind in one call. Never spawn one subagent per question.
- **Sonnet at low effort only.** Every subagent uses `model: sonnet` and the lowest reasoning effort. Never use another model or a higher effort, in any profile.
- **Source is read-only.** A `--source` path is used to check facts, never copied. Write every item in your own words.
- **Private files stay private.** `run.json` and `progress.json` live in the course folder, never in a public repository.
- Do not commit unless the user asks.

## Steps
1. **Setup.** Resolve topic, `<course folder>` (ask if unclear), kinds, profile and source. Create `<course folder>/Gen-asking-for-me/<Topic>/run.json`. Its shape is in `references/pipeline.md`.
2. **Plan.** One unit per concept and kind. If `<course folder>/Gen-asking-for-me/progress.json` exists, run `python3 <skill-dir>/scripts/progress.py <that file> weak 3` and add units for the weakest concepts.
3. **Run the profile** in `references/pipeline.md`. Prompts for the subagents are in `references/prompts.md`.
4. **Validate.** `python3 <skill-dir>/scripts/validate.py run.json` must exit 0. Fix the items, never the validator.
5. **Blind check.** Save the solver's answers to `solver.json` and run `validate.py run.json --solver solver.json`. Rewrite every item it flags, then check those items again.
6. **Render.** Invoke the matching `asking-for-me-*` skill for each kind. Tell it the verified items are in `run.json`, so it skips its own writing step.
7. **Reply** in two or three lines: topic, kinds, profile, subagents used of the budget, any deferred units, and the page links.

The run ends in one of two states: `complete`, or `incomplete` with a reason (for example `budget_exhausted`). Never stop mid-way, and never claim a deferred unit is covered.

## After the user practises
When the user reports which questions they got wrong, run `progress.py <progress.json> record <concept> right|wrong` for each, so the next run targets their weak concepts.
