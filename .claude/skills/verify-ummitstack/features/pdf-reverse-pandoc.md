# Reverse a PDF

A user turns a text PDF into an editable Typst file that places every run of text where it was, rebuilds a PDF, and the skill checks the result in four gates.

## Sub-features

- `pdf-recon` reads the text layer, fonts, links, form fields and unsupported shapes.
- `pdf-reverse` writes `layout.json`, `doc.md`, `doc.typ` and `build.sh`, and corrects every run against a trial rebuild.
- `pdf-verify` runs the fonts, structure, fidelity and look gates and writes `gates.json`.
- `pdf-refuse` stops on a scanned PDF (exit 2) and on a text font that is not installed (exit 3).

## How to get to it (user POV)

- Type `/pdf-reverse-pandoc <file.pdf> [out-dir]` in an agent that has the skill installed.
- Or run its scripts from the skill folder.

## Driving it with the installed scripts

Preconditions:

- `sh skills/pdf-reverse-pandoc/scripts/setup.sh` prints `all tools found` (typst, poppler tools, ImageMagick).
- Work in a scratch folder: `W=$(mktemp -d)`.

- **Make a fixture.** Run `python3 skills/pdf-reverse-pandoc/tests/make_fixture.py $W/in.pdf`. A two-page generated PDF appears.
- **Recon.** Run `python3 skills/pdf-reverse-pandoc/scripts/recon.py $W/in.pdf $W/out`. It prints `2 pages, 7 line shapes; not kept: nothing` and `font <name>: installed`, and exits 0.
- **Reverse and build.** Run `python3 skills/pdf-reverse-pandoc/scripts/run.py init $W/out --input in.pdf`, then `python3 skills/pdf-reverse-pandoc/scripts/reverse.py $W/in.pdf $W/out`, then `sh $W/out/build.sh`. `$W/out/rebuilt.pdf` exists.
- **Verify.** Run `python3 skills/pdf-reverse-pandoc/scripts/verify.py $W/in.pdf $W/out`. Four lines print: fonts ok, structure pass, fidelity pass with `0 differences`, look pass with equal page counts. Exit code 0.
- **Refusals.** Run `python3 skills/pdf-reverse-pandoc/tests/make_fixture.py $W/scan.pdf --scan` then `reverse.py $W/scan.pdf $W/scan-out`. It exits 2 and says the pages are pictures.
- **Proof.** Keep the transcript, `$W/out/gates.json` and `$W/out/verify-1/`. The four gate results in `gates.json` are the second view.

## Gotchas

- The fixture uses the system serif font, so run counts can differ a little between machines. Check that all four gates pass, not the exact numbers.
- Look scores are informational. A font that is replaced by a stand-in makes the fonts gate say `substituted` and the look gate say so too.
- `verify.py` fails on links, form fields, curves and pictures in the original unless `--accept-unsupported` is given. Never pass it on your own.
- `run.py report` closes a run only when every phase, gate and finding allows it; a failed gate needs an accepted finding or `run.py stop`.
