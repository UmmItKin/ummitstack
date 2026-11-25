# Notes

Marked "tested" were run with Pandoc 3.11 and LibreOffice while writing this skill. The rest comes from the Pandoc manual and was not tested here.

## The reference document

- `--reference-doc=original.docx` takes the styles, page size, margins, headers and footers from the original and ignores its body text. Tested.
- `pandoc input.docx -o reference.docx` does not extract a reference. It writes a new file with Pandoc's own styles and loses the custom ones. Tested. For the default reference, run `pandoc -o reference.docx --print-default-data-file reference.docx`.
- Pandoc copies the media files from the reference document into its output even when the text no longer uses them. Tested. This is why the compare counts images used in the document, not media files in the package.
- If the original lacks styles Pandoc writes, LibreOffice can lay out the result wrongly. Tested: a Word document without the `Compact` style rendered every Pandoc table with its cell text pushed out of the table, while the XML and the compare looked correct. Adding the missing definition fixed it. `add_pandoc_styles.py` copies every style Pandoc defines that the original lacks into `reference.docx`. Existing styles are never changed.
- Pandoc does not write the page background colour. `postprocess.py` copies `w:background` from the reference. Tested.

## Custom styles

- Read with `-f docx+styles`. The extension is off by default; without it every custom style is flattened. Tested.
- Write a style with `::: {custom-style="My Style"}` or `[text]{custom-style="My Style"}`. A class such as `{.MyStyle}` produced no style at all. Tested.
- `reverse.lua` removes the wrappers for styles Pandoc assigns by itself (Body Text, First Paragraph, Compact, captions, footnote text), so the Markdown stays readable. It also strips the style from figures, because Markdown cannot carry it and Pandoc would otherwise write raw HTML, which rebuilds without the caption. Tested.
- A paragraph style named `TOC Heading` is read as a level 1 heading. `reverse.lua` turns it back into a `custom-style` block so the heading count stays right.

## Page breaks

Pandoc drops page breaks when it reads a DOCX. Tested: 9 in the original, 0 in the rebuild. `extract_parts.py` makes a reading copy where each break is the text `PAGEBREAKMARK`, and `reverse.lua` turns that into a raw `<w:br w:type="page"/>` run in `doc.md`. The rebuild then has the same number. Tested.

## Table of contents

A table of contents is a content control holding a field. Pandoc reads its entries as plain paragraphs and the rebuild loses the field. `extract_parts.py` saves the original block to `toc.xml`, with the namespace declarations it uses. Without them the rebuilt `document.xml` is not valid XML and Word will not open it. Tested. `reverse.lua` replaces the entries with `<!-- TOC -->` and `build.lua` puts `toc.xml` back. The page numbers are the cached ones until the field is updated in Word.

## Tables

- Column widths follow the number of dashes in the separator line of a multiline or grid table, not the original widths. Tested.
- Mixed table markup (grid and multiline) makes editing the dashes by hand impractical. `extract_parts.py` saves the original widths to `table-widths.txt`, `build.lua` sets the relative widths from it, and `postprocess.py` writes the exact table, column and cell widths. Both apply by table order, and both refuse to apply if the number of tables changed.
- Pandoc writes table cells without a width. The exact widths fix the proportions; the compare checks only the proportions.

## Empty paragraphs, tabs and direct formatting

- Pandoc drops empty paragraphs, tab characters, text colours, sizes, fonts, paragraph alignment and spacing. Tested: the first rebuild had 4 of 115 empty paragraphs, no colours, and a different page count.
- Empty body paragraphs are saved verbatim in `empty-paragraphs.txt`. The reading copy replaces each with a marker, `reverse.lua` turns the marker into a `<!-- P12 -->` line, and `build.lua` puts the saved XML back. Tested: 20 pages against 20.
- Tabs are marked like page breaks and come back as raw `<w:tab/>` runs.
- Direct formatting of a run (colour, size, font, shading, highlight, character spacing) and of a body paragraph (alignment, indent, spacing, tab stops, borders, keep-with-next) becomes a named style, `DF1`, `DP1` and so on, added to the reading copy and to `reference.docx`. Pandoc reads a named style as `custom-style`, so it survives. Tested: the red, orange and green severity labels came back.
- Paragraphs in tables are not given `DP` styles. Their alignment, shading, row heights and look flags come from `table-cells.txt` and `table-props.json` in `postprocess.py`.
- Pandoc follows the `basedOn` chain when it looks for captions, so a style based on `Caption` is still a caption. The caption `DP` style copies the caption formatting instead of inheriting it. Tested.
- A caption next to a table is turned into the table's title by Pandoc and moved above it, and the table style is attached to that title. Without the title the table loses its style, so `table-styles.txt` keeps each table's style and `build.lua` sets it. Tested.
- `SEQ` fields are replaced by their current number, so captions read "Table 2: ..." as plain text and do not renumber.
- Empty rows in a table are dropped by Pandoc. `table-cells.txt` marks each original row `R` or `E` and `postprocess.py` puts the empty ones back when the counts allow it. Tested: it brought back the blank page the original had.

## Math

- Pandoc reads Word equations (OMML) as LaTeX and writes LaTeX back as native Word math.
- Complex equations (matrices, equation arrays, unusual accents) can degrade. Compare the rendered equations by eye.
- A formula stored as an image is not converted. Do not guess it.
- Macros: Pandoc expands `\newcommand` definitions it finds in the Markdown (the `latex_macros` extension). A separate `.tex` file is not read unless it is passed as an input file.

## Will not round trip

- Text boxes, shapes, charts, SmartArt.
- Content controls other than the table of contents, and form fields.
- Fields other than the table of contents, such as cross-references and `SEQ` numbers.
- Comments and tracked changes. By default Pandoc accepts tracked changes; `--track-changes=all` keeps them as spans.
- Custom list numbering definitions, merged or nested table cells, multi-column and multi-section layouts.
- Macros, embedded fonts and anything that runs code.

## Fonts

- `inventory.py` lists the fonts named in styles, in body runs (including the fonts of the `DF` styles the text uses), in headers and footers, and the theme fonts, and checks each with `fc-match`. Tested on a document whose theme font was not installed: that font and others were reported missing.
- The rebuild names the same fonts, because the styles and the theme come from the original. Nothing is embedded.
- LibreOffice does not resolve theme font references. Tested: text that only had the theme font fell back to a CJK font, while text with an explicit font name fell back to a different one, so cell headers and line spacing looked different in the render although the XML was the same. Judge the look with the real fonts installed.

## Why the compare is not enough

`inventory.py` checks structure from the XML. It cannot see layout. Tested: a rebuild passed the compare while LibreOffice drew every table wrongly. Always render and look (`render.sh`) when a renderer is available.

## Paths

Keep `--reference-doc` and image paths relative to the out-dir, and run `build.sh`, which changes into its own directory first, so the build works from anywhere.

## Paragraph format transfer and fidelity

`postprocess.py` `transfer_paragraph_formats` aligns the original and rebuilt paragraphs by text and copies the original paragraph properties (style, direct formatting, paragraph-mark run properties), keeping the rebuilt numbering. `fidelity.py` resolves the effective formatting of every paragraph (docDefaults, style chain, direct) in both files and prints each difference. `coverage.py` is the property ledger, `verify.py` runs all gates, `run.py` holds the phase state. See `phases.md`.
