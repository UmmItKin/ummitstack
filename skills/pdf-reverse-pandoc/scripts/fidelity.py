#!/usr/bin/env python3
"""Usage: fidelity.py original.pdf rebuilt.pdf [--tol PT] [--json out.json] [--accept-unsupported]
Compares every text run of two PDFs: the text, the font family, the size, bold and italic, the position (left and top
within --tol points, default 3) and the width (which shows letter spacing), and the page count and page size.
Prints one FAIL line per kind of difference and a summary. Exit 1 when anything differs."""
import json, os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graphics
import pdfinfo
from reverse import core, match


SYMBOL_FONTS = {"Symbol", "Wingdings", "Webdings"}  # their glyphs are not in the stand-in fonts, so the family is not compared


def compare(a, b, tol=3.0, width_tol=None, accept_unsupported=False):
    width_tol = width_tol if width_tol is not None else max(1.5, tol / 2)
    out = []
    if len(a) != len(b):
        out.append(("pages", f"original {len(a)}, rebuilt {len(b)}", "document"))
    for n, (pa, pb) in enumerate(zip(a, b), 1):
        if abs(pa["width"] - pb["width"]) > 1 or abs(pa["height"] - pb["height"]) > 1:
            out.append(("page size", f'original {pa["width"]}x{pa["height"]}, rebuilt {pb["width"]}x{pb["height"]}', f"page {n}"))
        pairs = match(pa["runs"], pb["runs"])
        for i, o in enumerate(pa["runs"]):
            if i not in pairs:
                out.append(("text", f'missing or changed in the rebuild: "{o["text"][:40]}"', f"page {n}"))
                continue
            r = pb["runs"][pairs[i]]
            where, sample = f"page {n}", o["text"][:30]
            for key in ("family", "size", "bold", "italic"):
                if key == "family" and o["family"] in SYMBOL_FONTS:
                    continue
                if key == "size" and abs(o[key] - r[key]) <= 0.3:
                    continue
                if key != "size" and o[key] == r[key]:
                    continue
                out.append((key, f'original {o[key]}, rebuilt {r[key]} e.g. "{sample}"', where))
            if abs(o["left"] - r["left"]) > tol or abs(o["base"] - r["base"]) > tol:
                out.append(("position", f'off by {o["left"] - r["left"]:.1f}, {o["base"] - r["base"]:.1f} pt (baseline) e.g. "{sample}"', where))
            spaces = len(o["text"]) - len(o["text"].strip())
            if spaces <= 2 and abs(core(o)[2] - core(r)[2]) > width_tol + spaces * 0.2 * o["size"]:
                out.append(("width", f'original {core(o)[2]:.1f}, rebuilt {core(r)[2]:.1f} e.g. "{sample}"', where))
        sa, sb = pa.get("shapes", []), pb.get("shapes", [])
        if len(sa) != len(sb) or (not accept_unsupported and pa.get("unsupported", 0) != pb.get("unsupported", 0)):
            out.append(("shapes", f"original {len(sa)} shapes and {pa.get('unsupported', 0)} unsupported, rebuilt {len(sb)} and {pb.get('unsupported', 0)}", f"page {n}"))
        else:
            box = lambda s: (min(p[0] for p in s["points"]), min(p[1] for p in s["points"]), max(p[0] for p in s["points"]), max(p[1] for p in s["points"]))
            left = [box(s) for s in sb]
            for s in sa:
                bx = box(s)
                near = min(left, key=lambda c: max(abs(c[k] - bx[k]) for k in range(4)), default=None)
                if near is None or max(abs(near[k] - bx[k]) for k in range(4)) > tol:
                    out.append(("shapes", f"a line or box near {bx[0]:.0f}, {bx[1]:.0f} is not in the rebuild", f"page {n}"))
                else:
                    left.remove(near)
        extra = len(pb["runs"]) - len(pairs)
        if extra > 0:
            out.append(("text", f"{extra} run(s) in the rebuild that are not in the original", f"page {n}"))
    return out


def main():
    args = sys.argv[1:]
    tol, out_json = 3.0, None
    accept = "--accept-unsupported" in args
    args = [x for x in args if x != "--accept-unsupported"]
    for flag in ("--tol", "--json"):
        if flag in args:
            k = args.index(flag)
            if flag == "--tol":
                tol = float(args[k + 1])
            else:
                out_json = args[k + 1]
            args = args[:k] + args[k + 2:]
    if len(args) != 2:
        sys.exit(__doc__)
    a, b = graphics.attach_baselines(pdfinfo.pages(args[0]), args[0]), graphics.attach_baselines(pdfinfo.pages(args[1]), args[1])
    for pdf, pgs in ((args[0], a), (args[1], b)):
        for pg, (s, u) in zip(pgs, graphics.pages(pdf, len(pgs))):
            pg["shapes"], pg["unsupported"] = s, u
    diffs = compare(a, b, tol, accept_unsupported=accept)
    kinds = Counter(d[0] for d in diffs)
    shown = set()
    for kind, detail, where in diffs:
        if (kind, detail.split(" e.g.")[0][:25]) in shown and kinds[kind] > 3:
            continue
        shown.add((kind, detail.split(" e.g.")[0][:25]))
        print(f"FAIL {kind} ({where}): {detail}")
    total = sum(len(p["runs"]) for p in a)
    print(f"{total} runs in {len(a)} pages of the original, {sum(len(p['runs']) for p in b)} in {len(b)} of the rebuild; {len(diffs)} differences in {len(kinds)} kinds")
    if out_json:
        json.dump({"differences": len(diffs), "kinds": dict(kinds)}, open(out_json, "w"))
    sys.exit(1 if diffs else 0)


if __name__ == "__main__":
    main()
