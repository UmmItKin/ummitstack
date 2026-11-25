# Diagram style for ppt-master decks

A deck that "uses the style" looks different from one that only follows the palette rules. The first time an agent applied this style by adding 1 px of jitter to lines, nothing visible changed. The style is the structure below. Copy the nearest file in `templates/`, then replace the content. Do not redraw from the rules alone.

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
- `rsvg-convert` does not load `../images/...` from a stray preview, so an image slot looks empty there. Check images in the PDF.

## Palette

The templates use the Group 17 terminal palette: `#050A06` background, `#0B1D10` panel, `#B8FFCC` text, `#88C996` secondary, `#185E2B` rule, `#FFBF00` accent. For the ummit.dev look, map them to `#1F1D1B`, `#2B2926`, `#E8E4DC`, `#A39E96`, `#4A4642`, `#8FA3B8`, and use `#D9A3A3` for replies. Keep the deck's own font sizes.
