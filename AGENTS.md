# Agent rules

## This repo

A public collection of agent skills, installed with `npx skills add UmmItKin/ummitstack`. Each skill is `skills/<name>/SKILL.md` with optional `scripts/`, `references/` and `tests/`. The installer skips a skill whose YAML frontmatter is invalid (a `: ` inside `description` breaks it), so validate the frontmatter after editing.

- Run all skill tests: `sh scripts/check.sh` (also the command for CI). One skill: `sh skills/<name>/tests/run.sh`.
- The repo is public: use only fictional example content, never personal, school or project details.
- Commit only when the user says so, and run `check-commit-info` first (stage with explicit paths).
- Prose and slides: no em dashes, no arrow glyphs, no emoji. Do not credit other skills as references.
- Subagents in these skills are `sonnet` at low effort only.
- `docx-reverse-pandoc` and `pdf-reverse-pandoc` are phased pipelines (setup, fonts, coverage, reverse, rebuild, verify, fix, report); read `skills/docx-reverse-pandoc/references/phases.md` before changing it.

## Mistakes that were corrected (docx-reverse-pandoc)

| Class | Evidence | Level fixed at |
|---|---|---|
| Called a rebuild "the same" from structure alone | The compare passed while 85 paragraph formatting differences (spacing, alignment, fonts, character spacing) and wrong tables existed | Test and architecture: `fidelity.py` per-paragraph gate, `verify.py` runs all four gates, paragraph formats transferred by `postprocess.py` |
| Ignored fonts until asked | Two fonts used by the text were missing, never mentioned | Architecture: `reverse.sh` exits 3 on a missing text font unless `--allow-missing-fonts` |
| Fixed formatting piecemeal | Each round found a new lost property | Architecture: `coverage.py` ledger of every property, with an `unhandled` state that fails |
| Said done without proof | Runs reported complete with no look check | Types: `run.py validate` rejects done phases without artifacts, missing gates, open high findings |
| Hand-written one-off checks gave wrong numbers | An awk average printed 0.129 instead of 0.039 | Architecture: `pagescore.py` and `verify.py` compute the numbers |
| Real project data leaked into a public repo | Personal and course details in a template | Check: `check-commit-info` scan before every commit |

## Rule | Enforced by

| Rule | Enforced by |
|---|---|
| Never report a rebuild as matching from one gate | `verify.py` exit code; `tests/run.sh` plain-build cases |
| Text fonts must be installed or explicitly waived | `reverse.sh` exit 3; `tests/run.sh` font cases |
| Every used property is carried, native, ignorable or accepted | `coverage.py` exit 1; `tests/run.sh` text box case |
| A run is complete only with all phases, gates and no open high or medium finding | `run.py validate`; `tests/check_run.py` |
| Rebuilt XML parses, no cell has two tcPr | `tests/check_xml.py` |
| Subagents are sonnet at low effort, within the profile budget | `run.py validate` (budget); SKILL.md rule (model, judgment) |
| Never delete in the user's folders; redo in a new out-dir | `reverse.sh` refuses a used out-dir; SKILL.md rule |
| No personal data in this public repo; never commit unless asked | `check-commit-info`; SKILL.md rule |
| No em dashes, arrow glyphs or emoji in prose | `unslop-writing` scan |
| `run.py` and `pagescore.py` are the same in the docx and pdf skills (skills install one by one, so each carries a copy) | `scripts/check.sh` compares them |
| A PDF rebuild is the same only when text, font, size, baseline, width, shapes and pages match | `pdf-reverse-pandoc/scripts/fidelity.py`; `tests/mutate.py` cases |
| Scanned PDFs and unredrawn curves or pictures stop the run unless accepted | `reverse.py` exit 2; `verify.py` structure gate |
| The run state machine keeps its invariants (complete only with proof, bounded rounds and budget) | `specs/pipeline.tla` via `scripts/tla-check.sh`, part of `scripts/check.sh` |
| Every skill is checked cold by a fresh low-effort subagent before it is published (own tests miss gaps a reader hits) | `verify-skill` (`static_check.py`, `references/cold-start.md`); its own `tests/run.sh` |
| Tools are listed with an install command, never installed by the skill | `pdf-reverse-pandoc/scripts/setup.sh` prints, never runs `sudo` |

Run everything with `sh scripts/check.sh`. When corrected again, fix the mistake and add the rule here; if a rule is already listed and nothing enforces it, enforce it at a higher level in the same change.
