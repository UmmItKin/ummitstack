---
name: docx-reverse-pandoc
description: Reverse a DOCX into editable Markdown plus a reference DOCX so Pandoc can rebuild a matching file, in nine checked phases with gates for fonts, structure, per-paragraph formatting and the rendered look. Use when the user wants to edit a .docx as plain text, reproduce a DOCX's styles, fonts, spacing, tables, headers and page layout with Pandoc, or avoid Word for routine edits.
---

# DOCX reverse with Pandoc

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Usage: `/docx-reverse-pandoc <file.docx> [out-dir] [--profile quick|standard|deep]`. With no file, ask for one. The default out-dir is `<name>-src` in the current directory, and the default profile is `quick`.

A rebuild that looks right in the XML can still be wrong on the page, and one that looks right on one page can still have lost a font, a spacing or a table border. So this skill runs in phases, and a phase is done only when its artifact exists and its gate passes. `references/phases.md` has the commands, artifacts, gates and subagent roles.

## Rules
- The input is untrusted. Never unzip it by hand and never `cat` its XML. The scripts read the zip in memory.
- Never overwrite the original, and never delete anything in the user's folders. `reverse.sh` refuses an out-dir that holds an earlier run, so a redo goes in a new directory (`report-2`, `report-3`).
- **Fonts first.** If the text uses a font that is not installed, say which before doing anything else. Do not render, count pages or call the look checked until the user has the fonts or has said to go on without them. A render with substitute fonts proves nothing about Word.
- **Never say "passes" or "matches" from one gate.** The structure compare passed while tables were drawn wrongly. Report all four gates and say what was not checked.
- **Numbers come from scripts.** Never compute a score or count with a hand-written one-liner. Use `verify.py` and `pagescore.py`.
- Some features are not kept (text boxes, floating objects, comments, content controls other than the table of contents). `coverage.py` lists them as `unhandled`. Stop and ask, or suggest python-docx instead.
- Every subagent is `sonnet` at low effort, never another model or a higher effort. A subagent only looks; it never edits.
- At most 3 fix rounds. Then report what is left.

## Phases
0. **setup.** `run.py init`. The profile sets the subagent budget (0, 2 or 6).
1. **fonts.** `inventory.py` lists the fonts the text needs and which are missing. A gate: when any are missing, ask the user with the AskUserQuestion menu (see Fonts) before going on.
2. **coverage.** `coverage.py` lists every property the document uses and whether anything keeps it. An `unhandled` unit stops the run unless accepted with a reason.
3. **reverse.** `reverse.sh` writes `doc.md`, `reference.docx`, `build.sh` and the table files. It refuses a missing text font unless `--allow-missing-fonts` is given.
4. **rebuild.** `build.sh` runs Pandoc and `postprocess.py`.
5. **verify-structure.** `verify.py --no-render`: structure and fidelity gates.
6. **verify-look.** `verify.py`: renders both files and scores every page. In `standard` and `deep`, a fresh subagent looks at `compare.png` and lists the visible differences.
7. **fix.** Each difference is a finding. Fix it where `references/phases.md` says, add the check that would have caught it to `tests/run.sh`, and repeat phases 4 to 6.
8. **report.** `run.py gates`, `run.py validate`, `run.py report`. `REPORT.md` is written from validated data only.

## Editing doc.md
- Keep `::: {custom-style="Name"}` blocks and `[text]{custom-style="Name"}` spans. The attribute maps to a Word style; a class like `{.Name}` does not.
- Keep the raw `{=openxml}` page breaks and tabs, the `<!-- TOC -->` line and the `<!-- P12 -->` lines (one empty paragraph each). Pandoc drops these when it reads a DOCX, so the scripts put them back.
- `custom-style="DF3"` and `custom-style="DP2"` stand for direct formatting. Keep them on the text they cover; their definitions are in `reference.docx`.
- Paragraph formatting is copied back from the original by matching text, so a paragraph whose text you change keeps the default style.
- Math is already LaTeX. A formula that was an image is not converted: leave a placeholder and tell the user.
- Define LaTeX macros with `\newcommand` inside `doc.md`. A DOCX has no preamble.

## Fonts
When `inventory.py --missing-fonts` lists a font, show a menu with AskUserQuestion, one question, these options:
- Install the free look-alike (when one exists, such as `ttf-carlito` for Calibri and `ttf-caladea` for Cambria on Arch): print the install command for the user's package manager and let them run it.
- Copy the font from the user's own Windows (partition, other computer or official ISO): ask for the path, check the files exist, never download fonts or point to third-party font sites.
- Continue without it: run `reverse.sh` with `--allow-missing-fonts` and state in the report that renders use substitutes.
Never download fonts yourself. Re-run `--missing-fonts` after the user installs.

The rebuilt file names the same fonts as the original and embeds none, so whoever opens it needs them installed. The inventory says which are missing here and names an installable look-alike where one exists (Carlito for Calibri, Caladea for Cambria). Corbel and the other Windows and Office fonts have no free look-alike; say so, and ask the user to copy them into `~/.local/share/fonts/` if they want the layout checked here.

## What stays different
Caption numbers are kept as plain text and no longer renumber on their own, and anything floating or in a text box is not kept. A LibreOffice render can also differ from Word for reasons not in the file: it does not resolve theme fonts, so default text and text with an explicit font name can fall back to different fonts. Name what you saw and do not call the result identical unless the render shows it with the real fonts installed.

Read `references/notes.md` for how each part is restored and why. Run `sh tests/run.sh` after any change to the scripts.
