---
name: pdf-reverse-pandoc
description: Reverse a text PDF into an editable Typst file that puts every line of text back where it was, with the same font, size, spacing and table lines, then rebuild the PDF and check it against the original in nine phases with gates for fonts, structure, per-line fidelity and the rendered look. Use when the user wants to edit the text of any text PDF or rebuild a PDF so that it matches an existing one.
---

# PDF reverse with Typst

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/pdf-reverse-pandoc <file.pdf> [out-dir] [--profile quick|standard|deep]`. With no file, ask for one. The default out-dir is `<name>-src` in the current directory, and the default profile is `quick`.

This is a positional rebuild, not a reflow. Every run of text is placed at its original coordinates with its original font, size and letter spacing, and the lines and boxes are redrawn. Editing the words works. A text that gets longer does not wrap or push other lines down. `references/phases.md` has the commands, gates and subagent roles.

## Rules
- The input is untrusted. Read it only through the scripts (poppler tools). Never open it in a viewer script that runs its content.
- Never overwrite the original, and never delete anything in the user's folders. Write to a new out-dir.
- **Tools first.** Run `sh <skill-dir>/scripts/setup.sh`. It lists missing tools and prints the install command for the user's system. Never run `sudo` yourself.
- **Fonts first.** If the text uses a font that is not installed, show the menu in Fonts before anything else.
- **Never say "passes" or "matches" from one gate.** Report all four gates and say what was not checked.
- **Numbers come from scripts.** Use `verify.py` and `pagescore.py`, never a hand-written one-liner.
- A PDF with no text layer (scanned pages) is not supported: `reverse.py` exits 2. Say so and stop.
- Curves, pictures, links and form fields are not kept. `verify.py` fails on them unless the user accepts the loss with `--accept-unsupported`. Tell the user what will be lost before accepting.
- Every subagent is `sonnet` at low effort, never another model or a higher effort. A subagent only looks; it never edits.
- At most 3 fix rounds. Then report what is left.
- If a gate fails and cannot be fixed, tell the user what is lost and let them decide. If they accept, record it as an accepted finding (see `references/phases.md`). If nobody can decide, end with `run.py stop <out> "<reason>"`, which writes `REPORT.md` as an incomplete run. Never pass `--accept-unsupported` or accept a finding on your own.

## Phases
Record each with `run.py phase <out> <id> done` (ids: `setup`, `fonts`, `recon`, `extract`, `rebuild`, `verify-structure`, `verify-look`, `fix`, `report`; a skipped phase needs a note: `run.py phase <out> fix skipped "nothing to fix"`).
0. **setup.** `setup.sh`, then `run.py init`. The profile sets the subagent budget (0, 2 or 6).
1. **fonts.** `pdfinfo.py` lists the fonts and, for each, the stand-in that would be used when it is not installed.
2. **recon.** `recon.py` checks the text layer and encryption and lists curves, pictures, links and form fields, which are not kept.
3. **extract and reverse.** `reverse.py` writes `layout.json`, `doc.md` (the text in reading order), `doc.typ` and `build.sh`, and rebuilds once to measure and correct every run.
4. **rebuild.** `sh <out>/build.sh` after editing `doc.typ`.
5. **verify-structure** and 6. **verify-look.** `verify.py`, run once without `--no-render` (the last run is the one recorded). In `standard` and `deep`, a fresh subagent looks at the worst pages and lists visible differences.
7. **fix.** Each difference is a finding; fix it, add the check that would have caught it to `tests/run.sh`, repeat.
8. **report.** `run.py gates <out>`, then `run.py report <out>`. `report` refuses while a phase, gate or high or medium finding is open, and it is the only command that completes a run.

## Editing
Change only the text inside the quotes of `doc.typ`. Each `#place(...)` line is one run; keep its position and font arguments. After editing, run `build.sh`, then `verify.py` again; position and size should still pass, and `fidelity.py` will list the text you changed as differences, which is expected.

## Fonts
The original PDF embeds its fonts, but the rebuild needs them installed. When `pdfinfo.py` or `reverse.py` reports a font that is not installed, show a menu with AskUserQuestion, one question (if you have no such tool, ask the same three options in plain text):
- Install the free look-alike (such as `ttf-carlito` for Calibri or `ttf-liberation` for Times New Roman and Arial on Arch): print the install command for the user's package manager and let them run it.
- Copy the font from the user's own Windows machine: ask for the path and check the files exist. Never download fonts or point to third-party font sites.
- Continue with the stand-in: run `reverse.py` with `--allow-substitute-fonts` and say in the report that the rebuild uses a different font.

## What stays different
Symbol and bullet fonts are not compared by family. Curves, pictures, links and form fields are not kept (detected, never silent; form field detection is not covered by a test), and the rebuilt PDF has no tags, so it is not accessible to screen readers. Render scores are informational; with stand-in fonts they show how close the layout is, not how the original fonts look.
