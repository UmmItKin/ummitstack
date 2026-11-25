# Style reference

The style is the structure below. Copy the nearest file in `templates/`, then replace the content.

## Pick the template

| The slide shows | Copy | Pattern |
|---|---|---|
| Parts of a system and what each one does | `templates/zones.svg` | Equal zones with a numbered kicker, one highlighted zone (4 px bar on top), arrows between zones, a source label at the bottom of each, a full-width strip for outside services |
| Who uses it and what is outside | `templates/boundary.svg` | Actors on the left, a tinted system boundary (amber at 0.06 opacity, 2 px line), plain text inside, external boxes on the right |
| Calls between components over time | `templates/sequence.svg`, or run `scripts/sequence.py` | Lifelines, requests as amber arrows to the right, replies as green arrows to the left, dashed lines between sections |
| A procedure with steps | `templates/chevron-flow.svg` | Chevron steps, the key step filled amber, the route under each step |
| Records and how they relate | `templates/data-model.svg` | Code panel with one highlighted line, entity boxes with a header rule, a curved relation marked `1` and `*`, a big count |

`scripts/sequence.py` does the coordinate maths for sequence diagrams: `python3 scripts/sequence.py spec.json > group.svg`. The docstring has the spec format.

## Vocabulary

- **Frame:** a closed 4-point `path ... Z` whose corners are each 1 to 2 px off, with `stroke-linejoin="round"`. Not a `<rect>`.
- **Line:** `M x1 y Q mx my±1 x2 y` with `stroke-linecap="round"`. Not a `<line>`.
- **Arrowhead:** an open chevron `M x-10 y-6 L x y L x-10 y+6`, stroke only. For a block arrow use a `rightArrow` or `chevron` preset group.
- **State by line, not by colour:** solid frame is built or normal, dashed (`4,4`) is planned, 2 px amber is the key item, a 0.06 to 0.12 amber fill marks an emphasis area.
- **Two text levels:** a 20 px item name, then a 14 px secondary line under it.
- **Layers, bottom to top:** background, grain, header, content groups, footer. Every content group has `data-pptx-bounds`.

## Traps the exporter sets

- A `<g>` preset such as `downArrow` must match the registry's path exactly, or the quality gate fails with "differs from registry output". Draw the shape as a plain `<path>` when unsure.
- The group's `data-pptx-bounds` must contain every child, with at least 5% to spare vertically. An error above 5% overflow stops the build.
- `rsvg-convert` does not load `../images/...` from a stray preview, so an image slot looks empty there. Check images in the PDF or in `svg_final/`.

## Arrows inside text

Never type an arrow character in slide text. The deck fonts have no arrow glyph, so the viewer falls back to another font and the arrow looks tiny and off-style. Draw each one as two paths, a thin `Q` line and an open chevron head, and split the text around it:

```svg
<text x="84" y="556" font-size="20" fill="#B8FFCC">Payments</text>
<path d="M 194 549 Q 208 549.8 222 549" fill="none" stroke-linecap="round" stroke="#88C996" stroke-width="1.5" />
<path d="M 213 544 L 222 549 L 213 554" fill="none" stroke-linecap="round" stroke-linejoin="round" stroke="#88C996" stroke-width="1.5" />
<text x="234" y="556" font-size="20" fill="#88C996">charge a card</text>
```

- Put the arrow's y about 7 px above the baseline for 20 px text, about 5 px for 14 to 15 px text.
- Start the line about 12 px after the previous text ends, make it 22 to 28 px long, and start the next text about 12 px after the head. Measure the previous text with the deck font, for example `ImageFont.truetype(path, size).getlength(text)` from Pillow, instead of guessing.
- Use a 9 x 5 px head for 20 px text and 7.5 x 4 px for 14 to 15 px text. Alternate the line's 0.8 px curve up and down between arrows.
- In code panels do not write an arrow either. Write `ref Drink.drinkId` or draw the arrow the same way.

## Dashes

No em dash (U+2014) and no en dash (U+2013) anywhere. Use a colon, a comma, a period, or the middle dot `·` that the templates use as a separator.

## Fonts

Use the fonts named in `spec_lock.md` and `design_spec.md`, not whatever the renderer falls back to.

1. For each family run `fc-match "<Family>"`. It must print that family. A different family means a fallback.
2. If it is missing, find it: Google Fonts, the foundry's own site, or a distribution package. Check the license (OFL or equally free) before using it.
3. Download the TTF or OTF, put it in `~/.local/share/fonts/`, run `fc-cache -f`, and run `fc-match` again.
4. Check that the font has the characters the slide uses.
5. If you cannot get it, tell the user which font is missing and what it fell back to. Do not call the slide done with a silent fallback.

Install fonts before rendering: `rsvg-convert` and the browser both read the installed fonts.

## Palette

The templates ship in a terminal palette: `#050A06` background, `#0B1D10` panel, `#B8FFCC` text, `#88C996` secondary, `#185E2B` rule, `#FFBF00` accent, with Pixelify Sans and Share Tech Mono. Replace them with the deck's own values from `spec_lock.md`. For a warm dark look, map them to `#1F1D1B`, `#2B2926`, `#E8E4DC`, `#A39E96`, `#4A4642`, `#8FA3B8`, and use `#D9A3A3` for replies. Keep the deck's own font sizes. The same constants sit at the top of `scripts/sequence.py`; change them there once per deck.
