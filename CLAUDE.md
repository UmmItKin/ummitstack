# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## This repo

A public collection of agent skills, installed with `npx skills add UmmItKin/ummitstack`. Each skill is `skills/<name>/SKILL.md` with optional `scripts/`, `references/` and `tests/`. The installer skips a skill whose YAML frontmatter is invalid (a `: ` inside `description` breaks it), so validate the frontmatter after editing.

- Run all skill tests: `sh scripts/check.sh` (also the command for CI). One skill: `sh skills/<name>/tests/run.sh`.
- The repo is public: use only fictional example content, never personal, school or project details.
- Commit only when the user says so (or `commit-regular` is on), and run `check-commit-info` and `leak_scan.py` first (stage with explicit paths).
- Prose and slides: no em dashes, no arrow glyphs, no emoji. Do not credit other skills as references.
- Subagents in these skills are `sonnet` at low effort only.
- `docx-reverse-pandoc` and `pdf-reverse-pandoc` are phased pipelines (setup, fonts, coverage, reverse, rebuild, verify, fix, report); read `skills/docx-reverse-pandoc/references/phases.md` before changing it.

## Never add to a commit

`check-commit-info` checks the staged files and the message. These must not go into a commit, its message or its author line, because the repo is public:

- Secrets: `.env` files, key files, tokens, passwords and credentials.
- Email addresses (placeholders such as `you@example.com` are fine) and phone numbers.
- Home directory paths such as `/home/<name>` or `C:\Users\<name>` (use `/home/user`).
- The user's own name or login, and private hostnames.
- The name of a school, an employer or a private project, and wording or layout copied from a document the user gave. `leak_scan.py` checks the last one against the user's source files.
- Files the user owns: their PDFs, Word or Office documents, and generated output such as `__pycache__`.
- A different author: never pass `--author` or `-c user.name=...`; the author is whatever git is configured with.
- In the message: one short line, no `Co-Authored-By` or other trailer.

If a match is public information the project means to publish, name the file and ask the user once. Never amend, reset or rewrite published history, and never push unless the user asks.

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
| Fixtures, examples and tests use generic placeholder text, never wording or layout copied from a document the user gave | `skills/verify-skill/scripts/leak_scan.py` against the user's source files (not stored in the repo), on the staged diff before each commit and on the history |
| A commit happens only when `check-commit-info` prints exactly `ok` and `leak_scan.py` reports 0 hits, judged from the output and never through a pipe | agent routine; `verify-skill/tests/run.sh` tests the scanner |
| A hook toggle changes only its own entry in the user settings and never damages the file | `auto-find-best-skill/tests/run.sh` (temporary settings files only) |
| Moving project memory copies only, never deletes or overwrites, and previews before it applies | `update-repo-directory-path/tests/run.sh` (temporary Claude folder only, with a checksum of the old folder) |
| The star list reader pages through every item, sorts by stars, and reports a missing or logged-out gh instead of failing silently | `starred-list-summary/tests/run.sh` (fake `gh`, no network) |
| Listing Claude Code projects reads only titles and working directories and never prints conversation text | `list-claude-projects/tests/run.sh` (fake Claude folder with a secret word in a message) |
| The browser opener builds the exact command per browser, keeps Brave on its own profile and passes the URL as one argument | `open-ag/tests/run.sh` (fake `agent-browser`, isolated PATH and HOME) |
| A change to a skill is proven on the installed copy in a throwaway HOME, never against the real `~/.claude` | `.claude/skills/verify-ummitstack` (`doctor.sh`, `prove-install.sh`, `features/`) |
| The auto-find-best-skill toggle never loses or damages the user's settings, checked on every settings file in a stated space; known findings are listed, a new violation fails | `.claude/skills/verify-settings-toggle` (`check.py`, `prove-catches.py`, `sync.sh`), run by `scripts/check.sh` |
| The Proton skill never changes the mailbox (only `list`, `get` and `count` run, everything else is refused without running proton), previews and asks before other changes, and never prints account data in its checks | `use-proton-cli/scripts/mail-read.sh`; `tests/mail.sh` and `tests/run.sh` (fake `proton`, isolated PATH) |
| Tools are listed with an install command, never installed by the skill | `pdf-reverse-pandoc/scripts/setup.sh` prints, never runs `sudo` |

Run everything with `sh scripts/check.sh`. When corrected again, fix the mistake and add the rule here; if a rule is already listed and nothing enforces it, enforce it at a higher level in the same change.
