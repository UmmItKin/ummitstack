# Reverse a DOCX

A user turns a DOCX into editable Markdown plus a reference document, rebuilds it with Pandoc, and the skill checks structure, per-paragraph formatting and the rendered look.

## Sub-features

- `docx-fonts` lists the fonts and refuses a text font that is not installed (exit 3).
- `docx-coverage` lists every formatting property and what keeps it, and fails on one nothing keeps.
- `docx-reverse` writes `doc.md`, `reference.docx`, `build.sh` and the table files.
- `docx-verify` runs the fonts, structure, fidelity and look gates and writes `gates.json`.

## How to get to it (user POV)

- Type `/docx-reverse-pandoc <file.docx> [out-dir]` in an agent that has the skill installed.
- Or run its scripts from the skill folder.

## Driving it with the installed scripts

Preconditions:

- `pandoc` is installed. LibreOffice, `pdftoppm` and ImageMagick are needed only for the look gate.
- Work in a scratch folder: `W=$(mktemp -d)`.

- **Make a fixture.** Run `python3 skills/docx-reverse-pandoc/tests/make_fixture.py $W/f.docx`.
- **Fonts and coverage.** Run `python3 skills/docx-reverse-pandoc/scripts/inventory.py $W/f.docx --missing-fonts` and `python3 skills/docx-reverse-pandoc/scripts/coverage.py $W/f.docx`. Both exit 0 for the fixture.
- **Reverse and build.** Run `sh skills/docx-reverse-pandoc/scripts/reverse.sh $W/f.docx $W/out` then `sh $W/out/build.sh`. `$W/out/rebuilt.docx` exists.
- **Verify.** Run `python3 skills/docx-reverse-pandoc/scripts/verify.py $W/f.docx $W/out`. Four gate lines print; structure and fidelity say pass with `0` differences. Exit code 0.
- **Proof.** Keep the transcript and `$W/out/gates.json`. The fidelity line (`matched N of N ... 0 property differences`) is the second view.

## Gotchas

- `reverse.sh` refuses a used out-dir; use a new folder for every run.
- A font named only in styles and not installed is reported in the fonts gate but does not stop the run.
- Without LibreOffice the look gate says `not verified`, which is not a pass.
- Caption numbers become plain text after a rebuild; do not count that as a failure.
