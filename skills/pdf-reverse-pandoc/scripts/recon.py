#!/usr/bin/env python3
"""Usage: recon.py original.pdf out-dir
Exit 2: no text layer. Exit 1: encrypted. Exit 0: it can be reversed.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graphics
import pdfinfo


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    pdf, out = sys.argv[1:]
    f = pdfinfo.facts(pdf)
    shapes = graphics.pages(pdf, f["pages"])
    rec = {"pages": f["pages"], "text_layer": bool(sum(f["runs_per_page"])), "encrypted": f["encrypted"], "links": f["links"], "form": f["form"],
           "line_shapes": sum(len(s) for s, _ in shapes), "unsupported_curves_or_pictures": sum(u for _, u in shapes),
           "fonts": f["fonts"]}
    os.makedirs(out, exist_ok=True)
    json.dump(rec, open(os.path.join(out, "recon.json"), "w"), indent=1)
    notes = [f"{rec[k]} {label}" for k, label in (("links", "links"), ("unsupported_curves_or_pictures", "curves or pictures")) if rec[k]] + (["form fields"] if rec["form"] else [])
    print(f"{rec['pages']} pages, {rec['line_shapes']} line shapes; not kept: {', '.join(notes) or 'nothing'}")
    for font in rec["fonts"]:
        print(f"font {font['family']}: " + (f"stand-in {font['stand_in']}" if font["stand_in"] else "installed"))
    if not rec["text_layer"]:
        print("no text layer: the pages are pictures, which this skill does not read", file=sys.stderr)
        sys.exit(2)
    if rec["encrypted"]:
        print("encrypted", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
