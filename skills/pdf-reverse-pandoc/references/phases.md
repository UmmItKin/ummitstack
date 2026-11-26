# Phases

| # | Phase | Command | Artifact | Stop and ask when |
|---|---|---|---|---|
| 0 | setup | `sh scripts/setup.sh`, `python3 scripts/run.py init <out> --input <file> --profile quick` | `run.json` | a tool is missing |
| 1 | fonts | `python3 scripts/pdfinfo.py <file> > <out>/inventory-original.txt` | `inventory-original.txt` | a font is not installed |
| 2 | recon | `python3 scripts/graphics.py <file>` and read `pdfinfo.py` output | `recon.json` | no text layer, curves, pictures or encryption |
| 3 | extract | `python3 scripts/reverse.py <file> <out>` | `layout.json`, `doc.md` | exit 2 or 3 |
| 4 | rebuild | `sh <out>/build.sh` | `doc.typ`, `rebuilt.pdf` | Typst fails |
| 5 | verify-structure | `python3 scripts/verify.py <file> <out> --no-render` | `gates.json` | structure or fidelity fails |
| 6 | verify-look | `python3 scripts/verify.py <file> <out>` | `gates.json`, `verify-N/` | page counts differ |
| 7 | fix | edit `doc.typ` or the scripts, repeat 4 to 6 | `findings.json` | after 3 rounds |
| 8 | report | `run.py gates`, `run.py validate`, `run.py report` | `REPORT.md` | `validate` reports an error |

`run.py` and `pagescore.py` are the same files as in `docx-reverse-pandoc`; `scripts/check.sh` fails when they differ. Only `phases.json` differs.

## Gates
- **fonts.** Which fonts are installed exactly and which have a stand-in (`fc-match`). Substituted is not a failure, but it is always reported.
- **structure.** The text layer exists, nothing is encrypted, and there are no curves or pictures unless accepted.
- **fidelity.** Per run: text, family, size (0.3 pt), bold, italic, baseline (3 pt), left edge (3 pt), width (1.5 pt, which shows letter spacing), plus line shapes (count and position), page count and page size. The baseline comes from the glyph positions in a cairo SVG, because the line heights stored in a PDF differ between producers.
- **look.** `pagescore.py` renders and scores each page; the page counts must agree.

## How the rebuild lands on the original
`reverse.py` builds `doc.typ` once, extracts the rebuilt PDF with the same code, and for each run corrects the position by the baseline difference and the letter spacing by the width difference (limited to 0.6 pt per letter), up to three rounds. Runs with leading or trailing spaces use an estimated space width of 0.25 em.

## Profiles and subagents
Quick uses no subagent. Standard (2) sends one fresh subagent the worst pages as an image and returns `{"pages": [{"page": N, "differences": [...]}]}`; it never suggests fixes. Deep (6) adds a subagent per worst page, up to 4. All are `sonnet` at low effort. `run.py agents <out> N` records the use and `validate` fails above the budget.

## Findings
Add with `run.py finding <out> add <phase> high|med|low <area> <evidence>`, resolve as `fixed` or `accepted` with a reason. A run is complete only when no high or medium finding is open.
