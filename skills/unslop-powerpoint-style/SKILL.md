---
name: unslop-powerpoint-style
description: Make a ppt-master deck look designed instead of generated. Phase 1 applies the structural style (zones, boundaries, sequence diagrams, chevron flows, code panels, hand-drawn frames and lines), phase 2 copies the nearest slide template and replaces its content, and both end by rendering and viewing every touched slide. Use when drawing or restyling slides or diagrams in a ppt-master SVG deck, or when a deck looks generated.
---

# Unslop a PowerPoint deck

Arguments: $ARGUMENTS
(Claude Code fills these in. In Codex, or if the line above still shows a placeholder, read them from the user's message.)

Accepted: a project directory, or slide names or numbers inside it. With no argument, use the current directory and ask which slides.

## Why this exists
Applying "the style" from colour and line rules alone changes nothing a person can see. Once, 1 px of jitter was added to every line and nobody noticed. The style is the structure: how a slide is divided and what shapes carry the meaning. Colours and jitter only finish it, so copy a template instead of restyling from the rules.

## Hard rules
- **No arrow characters in slide text.** Never type the right arrow (U+2192), a hyphen plus greater-than, an equals plus greater-than, or any other arrow glyph. The deck fonts have no arrow glyph, so the viewer falls back to another font and the arrow renders tiny and off-style. Draw every arrow as two `<path>` elements: a thin `Q` line and an open chevron head. The snippet is in `references/style.md`.
- **No em dash or en dash** (U+2014, U+2013). Use a colon, a comma, a period, or the middle dot `·` for separators.
- **Use the deck's own fonts, and make sure they are installed.** Check each family with `fc-match`. If it falls back to another family, find the font, download it and install it before rendering. See "Fonts" in `references/style.md`. If you cannot get it, tell the user which font is missing and do not call the slide done.

## Phase 1: style pass
1. Read `references/style.md` once: the pattern table, the vocabulary and the exporter traps.
2. For each slide, name what it shows (parts of a system, who is outside, calls over time, steps, records) and pick the matching pattern from the table. A slide of plain bullets or boxes in a row is the thing to replace.
3. Change the structure first: zones, boundary, dividers, step shapes, highlighted item. Then apply the vocabulary: jittered 4-point frames, `Q` curve lines, open chevron arrowheads, state by line style.
4. Keep the deck's own palette, fonts and sizes from `design_spec.md` and `spec_lock.md`. Never invent facts, numbers or labels; reuse the slide's existing content.

## Phase 2: slide template
1. Copy the nearest file from `templates/` to the slide's `svg_output/NN_name.svg`. Do not redraw it.
2. Replace the content only: text, labels, counts, section names. Keep the structure, the layer order and each group's `data-pptx-bounds`.
3. Swap the template's palette and font for the deck's own (see the palette note in `references/style.md`).
4. Sequence diagrams: run `python3 <skill-dir>/scripts/sequence.py spec.json > group.svg` and paste the group in, instead of placing arrows by hand. The docstring has the spec format.
5. Remove template content that is not about this slide.

## Look at every slide (mandatory)
A slide is not done until you have seen it, including after a small change.
1. Run the deck's quality gate and fix its errors: `svg_quality_checker.py <project> --canonical-authoring --stage final --json` (ppt-master's scripts; see the `presentation-deck` skill). Then run `LC_ALL=C.UTF-8 grep -nP '\x{2192}|-[>]|-&g[t];|=[>]|=&g[t];|\x{2014}|\x{2013}' <project>/svg_output/*.svg`; it must print nothing.
2. Render each touched slide: `rsvg-convert -f png -w 1280 -o <scratch>/NN.png svg_output/NN_name.svg`. Use `svg_final/` once images are embedded, because `rsvg-convert` does not resolve `../images/...` from a stray preview and an image slot looks empty.
3. Open each PNG with the Read tool and look at it. Check: is the structure visible at a glance (zones, boundary, dividers, highlighted item), is text clipped or overlapping, is the key item obvious, does it look like the neighbouring slides. Also check that every arrow is a drawn thin line with an open chevron head (never a glyph), that no dash or arrow character appears, and that the text is in the deck's font and not a fallback.
4. Fix and re-render until it passes. Reply with the slide list and what you saw, not "should look fine".

Rebuild with the `presentation-deck` skill when the SVGs are done.
