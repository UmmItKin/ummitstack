# Build a ppt-master deck

## Source layout
- `design_spec.md` and `spec_lock.md` lock the palette, fonts and text sizes. Do not change them unless asked.
- `svg_output/NN_name.svg` is one slide each, named in slide order. This is the source.
- `notes/total.md` holds all speaker notes. Per-slide `notes/*.md` files are generated from it.
- `images/` and `fonts/` are inputs. `exports/`, `svg_final/` and `validation/` are generated.

For planning and authoring slides, read the installed ppt-master skill's `workflows/generate-pptx.md`; it owns templates, confirmation gates and SVG authoring rules.

## Pipeline
Run from the project directory. `S` is ppt-master's `scripts/` directory, `P` the Python interpreter with its requirements installed.

1. Final quality gate, only after every planned SVG exists:
   `$P $S/svg_quality_checker.py <project> --canonical-authoring --stage final --json`
   - Keep `--json`: it writes `validation/svg_quality_report.json`, which `svg_to_pptx.py` fingerprints. Without a current report the exporter refuses; on some versions it silently reuses the previous export instead.
   - On failure, read only `categories.blocking.issues` from the report. Never cat the whole JSON into context.
2. Speaker notes, only when `notes/total.md` exists: `$P $S/total_md_split.py <project>`.
3. Self-contained preview: `$P $S/finalize_svg.py <project>` writes `svg_final/`. Its absence never blocks export.
4. PPTX: `$P $S/svg_to_pptx.py <project>`, adding `--no-notes` when the deck has no notes. The exporter needs the current final quality report and exits nonzero on a missing, stale or blocking one. It prints a `[POSTFLIGHT]` receipt with the slide count and report path; read the receipt, not the full report.
5. PDF: `rsvg-convert -f pdf -o <project>/<name>.pdf "$svg_final"/*.svg`, falling back to `svg_output/` when there is no preview.
6. Counts: PPTX slides, PDF pages and SVGs must all match.

Other export flags: `--native-charts-and-tables` when charts or tables must stay editable, `--image-sizing display` when the checker reports oversized images, `-a none` or `--no-animations` to disable motion. An `animations.json` sidecar is picked up automatically.

## Traps
- The final quality gate feeds the export. Rerun it after any SVG change, because a stale report blocks the exporter or misleads it.
- Split notes only when `total.md` exists; exporting notes that do not exist fails.
- Install the deck's fonts locally before the PDF (`cp fonts/*.ttf ~/.local/share/fonts && fc-cache -f`), or it falls back to other fonts. Package names and nerd-font variants often differ; check the family name with `fc-scan`.
- Preview with `rsvg-convert`, not LibreOffice: its rendering differs from PowerPoint.
- If the project embeds fonts into the PPTX by widening `wrap="none"` text boxes, run that step exactly once. A second run widens them again.
- Inserting, dropping or moving a slide renumbers the roster: clear the stale per-slide notes and `svg_final/` files, and update footers, contents-page numbers and hyperlink targets.
