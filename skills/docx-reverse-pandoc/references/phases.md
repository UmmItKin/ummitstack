# Phases

The workflow is a pipeline of nine phases. Each phase has a command, an artifact that proves it ran, and a
condition that stops it. `scripts/run.py` records the state and refuses to call a run complete without the proof.
The scripts do the mechanical work. A subagent only looks, never edits.

| # | Phase | Command | Artifact | Stop and ask when |
|---|---|---|---|---|
| 0 | setup | `python3 <skill-dir>/scripts/run.py init <out> --input <file> --profile quick` | `run.json` | the input is not a DOCX |
| 1 | fonts | `python3 <skill-dir>/scripts/inventory.py <file> > <out>/inventory-original.txt` | `inventory-original.txt` | the text uses a font that is not installed |
| 2 | coverage | `python3 <skill-dir>/scripts/coverage.py <file> <out>` | `coverage.json` | a unit is `unhandled` and not accepted |
| 3 | reverse | `sh <skill-dir>/scripts/reverse.sh <file> <out>` | `doc.md`, `reference.docx`, `build.sh` and the table files | `reverse.sh` exits non-zero |
| 4 | rebuild | `sh <out>/build.sh` | `rebuilt.docx` | Pandoc or `postprocess.py` fails |
| 5 | verify-structure | `python3 <skill-dir>/scripts/verify.py <file> <out> --no-render` | `gates.json` | structure or fidelity fails after the fix rounds |
| 6 | verify-look | `python3 <skill-dir>/scripts/verify.py <file> <out>` | `gates.json`, a `verify-N` folder with `compare.png` | the page counts differ |
| 7 | fix | edit `doc.md` or the scripts, then repeat phases 4 to 6 | `findings.json` | after 3 rounds, report what is left |
| 8 | report | `run.py gates <out>`, then `run.py report <out>` | `REPORT.md` | `report` lists what stops it from closing |

Record each phase with `run.py phase <out> <phase> done`. A phase that does not apply is `skipped` with a note, and a
phase that stopped the run is `blocked` or `failed` with a note.

Phase ids for `run.py phase`: `setup`, `fonts`, `coverage`, `reverse`, `rebuild`, `verify-structure`, `verify-look`, `fix`, `report`. Mark `fix` as `skipped` with a note when nothing needed fixing.

## When a gate fails
`report` will not close a run with a failed gate. Fix it and rerun `verify.py`. If it cannot be fixed (for example the PDF has a link that is not kept), tell the user what is lost and let them decide. If they accept, add a finding whose area is the gate name (`run.py finding <out> add <phase> med structure "<what is lost>"`) and resolve it as `accepted` with their reason; then `report` closes. If nobody can decide, end the run with `run.py stop <out> "<reason>"`; an incomplete run is a valid end state and is reported as such.

## Closing a run
In this order: `verify.py` writes `gates.json`; `run.py gates <out>` reads it into the run; mark each finished phase with `run.py phase <out> <phase> done` (refused until its artifact exists); then `run.py report <out>` checks everything, writes `REPORT.md`, marks the report phase done and completes the run. `run.py validate <out>` can be run at any time.

## The gates

- **fonts.** The fonts the text uses, and which are missing. A missing font is reported before anything else, because
  every render, line break and page count made here uses a substitute, and Word needs the same fonts. Install them,
  or continue with `--allow-missing-fonts` and say so in the report. Never embedded; the rebuilt file names the same fonts.
- **structure.** `inventory.py` compares headings, styles, page setup, headers and footers, tables, images, fonts and
  page breaks, and `coverage.py` lists every property the document uses and what keeps it. An `unhandled` unit is a
  property nothing keeps. Accept it with `--accept` and a note, or stop.
- **fidelity.** `fidelity.py` compares the effective formatting of every paragraph with text: alignment, spacing,
  indent, font, size, colour, bold, italic, capitals, character spacing and highlight. This is the gate that finds
  layout, font and spacing differences that the structure compare cannot see.
- **look.** The pages are rendered with LibreOffice and scored against the original. The page counts must agree. The
  scores are informational: with missing fonts they say how close the layout is, not how Word will draw it.

## Profiles and subagents

Profiles change how much is checked, never how well. Every subagent is `sonnet` at low effort. Never use another
model or a higher effort. A subagent returns one JSON object, writes no files, and the parent records its findings.

| | quick (default) | standard | deep |
|---|---|---|---|
| Subagent budget | 0 | 2 | 6 |
| Look verifier on the worst pages | no | one call | one call per worst page, up to 4 |
| Coverage critic | no | no | one call |
| Fix rounds | 3 | 3 | 3 |

**Look verifier** (phase 6). A fresh subagent that did not write the fix gets `compare.png` of the worst pages (original
on top, rebuilt below) and returns the visible differences:
`{"pages": [{"page": 14, "differences": ["heading is lower", "box is shorter"]}]}`. It does not suggest fixes.

**Coverage critic** (phase 2, deep). A fresh subagent gets `coverage.json` and `inventory-original.txt` and returns
formatting properties or structures the ledger may have missed: `{"missing": ["w:effect on 4 runs"]}`.

Record the number used with `run.py agents <out> N`. `validate` fails when it exceeds the budget.

## Findings

Every difference that survives the gates is a finding: `run.py finding <out> add <phase> high|med|low <area> <evidence>`.
Resolve it as `fixed`, or as `accepted` with a reason (for example "the renderer cannot lay it out"). A run is
complete only when no high or medium finding is open.

| Finding is about | Fix it in |
|---|---|
| a property a paragraph lost | `postprocess.py`, `transfer_paragraph_formats`, or a `DF`/`DP` style in `extract_parts.py` |
| a table (width, row, cell, border, style) | `extract_parts.py` `table_props` and `postprocess.py` `apply_props` |
| something Pandoc drops when it reads | a marker in `extract_parts.py` `reading_copy` and a rule in `reverse.lua` |
| something Pandoc writes differently | `postprocess.py` or `add_pandoc_styles.py` |
| a font that is missing | the user installs it; nothing in the file changes |

Add the check that would have caught it to `tests/run.sh` in the same change.
