#!/usr/bin/env python3
"""Usage: reverse.py input.pdf out-dir [--allow-substitute-fonts]
Turns a text PDF into out-dir/layout.json (every text run with its place, font and size), out-dir/doc.md (the text
in reading order) and out-dir/doc.typ (a Typst file that puts every run back where it was). The runs are then
measured in a trial rebuild and doc.typ gets a small correction for each run (position and letter spacing), so the
rebuild lands on the original. Exit 2: the PDF has no text layer. Exit 3: a font used by the text is not installed
and --allow-substitute-fonts was not given."""
import json, os, shutil, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import graphics
import pdfinfo

TRACK_MAX = 0.6
SPACE = 0.25  # width of a space, in em, for text that has leading or trailing spaces


def core(r):
    """The text without leading and trailing spaces, and the width and left edge of just that text."""
    t = r["text"].strip()
    lead, trail = len(r["text"]) - len(r["text"].lstrip()), len(r["text"]) - len(r["text"].rstrip())
    return t, r["left"] + lead * SPACE * r["size"], r["width"] - (lead + trail) * SPACE * r["size"]


def q(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def typ(layout, adj):
    out = ['#set text(top-edge: "bounds", bottom-edge: "bounds")']
    for n, pg in enumerate(layout):
        if n == 0:
            out.append(f'#set page(width: {pg["width"]}pt, height: {pg["height"]}pt, margin: 0pt)')
        else:
            out.append("#pagebreak()")
        for s in pg.get("shapes", []):
            segs = [f"curve.move(({s['points'][0][0]}pt, {s['points'][0][1]}pt))"] + [f"curve.line(({x}pt, {y}pt))" for x, y in s["points"][1:]]
            if s["closed"]:
                segs.append("curve.close()")
            stroke = f'{s["width"]}pt + rgb("{s["stroke"]}")' if s["stroke"] else "none"
            fill = f'rgb("{s["fill"]}")' if s["fill"] else "none"
            out.append(f'#place(top + left, curve(stroke: {stroke}, fill: {fill}, {", ".join(segs)}))')
        for i, r in enumerate(pg["runs"]):
            dx, dy, tr = adj.get((n, i), (0, 0, 0))
            fam = [q(r["family"])] + ([q(r["stand_in"])] if r.get("stand_in") else [])
            color = f'rgb("{r["color"]}")' if r.get("color") and r["color"] != "#000000" else "black"
            args = f'font: ({", ".join(fam)}), size: {r["size"]}pt, fill: {color}'
            if r["bold"]:
                args += ', weight: "bold"'
            if r["italic"]:
                args += ', style: "italic"'
            if tr:
                args += f", tracking: {tr:.3f}pt"
            out.append(f'#place(top + left, dx: {core(r)[1] + dx:.2f}pt, dy: {r["top"] + dy:.2f}pt, text({args})[#{q(r["text"].strip())}])')
    return "\n".join(out) + "\n"


def compile_typ(src, pdf):
    r = subprocess.run(["typst", "compile", src, pdf], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("typst failed: " + r.stderr.strip()[:400])


def match(orig, rebuilt):
    """Pair each original run with the nearest unused rebuilt run that has the same text."""
    used, pairs = set(), {}
    for i, o in enumerate(orig):
        best = None
        for j, r in enumerate(rebuilt):
            if j in used or r["text"].strip() != o["text"].strip():
                continue
            d = abs(r["left"] - o["left"]) + abs(r["top"] - o["top"])
            if best is None or d < best[0]:
                best = (d, j)
        if best:
            used.add(best[1])
            pairs[i] = best[1]
    return pairs


def calibrate(layout, out, rounds=3):
    adj = {}
    src, pdf = os.path.join(out, "doc.typ"), os.path.join(out, "rebuilt.pdf")
    for _ in range(rounds):
        open(src, "w", encoding="utf-8").write(typ(layout, adj))
        compile_typ(src, pdf)
        rebuilt = graphics.attach_baselines(pdfinfo.pages(pdf), pdf)
        moved = False
        for n, pg in enumerate(layout):
            if n >= len(rebuilt):
                break
            for i, j in match(pg["runs"], rebuilt[n]["runs"]).items():
                o, r = pg["runs"][i], rebuilt[n]["runs"][j]
                dx, dy, tr = adj.get((n, i), (0, 0, 0))
                _, ol, ow = core(o)
                _, rl, rw = core(r)
                ndx, ndy = dx + (ol - rl), dy + (o["base"] - r["base"])
                chars = len(o["text"].strip()) - 1
                ntr = max(-TRACK_MAX, min(TRACK_MAX, tr + (ow - rw) / chars)) if chars >= 2 else 0
                if abs(ndx - dx) > 0.05 or abs(ndy - dy) > 0.05 or abs(ntr - tr) > 0.02:
                    moved = True
                adj[(n, i)] = (ndx, ndy, ntr)
        if not moved:
            break
    open(src, "w", encoding="utf-8").write(typ(layout, adj))
    compile_typ(src, pdf)


def reading_order(runs):
    lines = []
    for r in sorted(runs, key=lambda r: (round(r["top"] / 3), r["left"])):
        if lines and abs(lines[-1][0] - r["top"]) <= 3:
            lines[-1][1].append(r)
        else:
            lines.append([r["top"], [r]])
    return ["".join(x["text"] for x in sorted(ln[1], key=lambda x: x["left"])).rstrip() for ln in lines]


def main():
    args = [a for a in sys.argv[1:] if a != "--allow-substitute-fonts"]
    allow = len(args) != len(sys.argv) - 1
    if len(args) != 2:
        sys.exit(__doc__)
    pdf, out = args
    layout = graphics.attach_baselines(pdfinfo.pages(pdf), pdf)
    if not any(p["runs"] for p in layout):
        print("the PDF has no text layer (pages are pictures); this skill does not read those", file=sys.stderr)
        sys.exit(2)
    stand = {f: pdfinfo.installed(f) for f in {r["family"] for p in layout for r in p["runs"]}}
    changed = {f: s for f, s in stand.items() if s}
    if changed:
        print("fonts used by the text that are not installed (the stand-in is what would be used):", file=sys.stderr)
        for f, s in sorted(changed.items()):
            print(f"  {f} -> {s}", file=sys.stderr)
        if not allow:
            print("stopping: install them, or run again with --allow-substitute-fonts", file=sys.stderr)
            sys.exit(3)
    for p in layout:
        for r in p["runs"]:
            r["stand_in"] = changed.get(r["family"], "")
    shapes = graphics.pages(pdf, len(layout))
    for pg, (s, unsupported) in zip(layout, shapes):
        pg["shapes"], pg["unsupported"] = s, unsupported
    if any(u for _, u in shapes):
        print(f"note: {sum(u for _, u in shapes)} curves or pictures are not redrawn (see unsupported in layout.json)", file=sys.stderr)
    os.makedirs(out, exist_ok=True)
    json.dump(layout, open(os.path.join(out, "layout.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(out, "doc.md"), "w", encoding="utf-8") as f:
        for n, pg in enumerate(layout, 1):
            f.write(f"<!-- page {n} -->\n\n" + "\n".join(reading_order(pg["runs"])) + "\n\n")
    calibrate(layout, out)
    with open(os.path.join(out, "build.sh"), "w") as f:
        f.write('#!/bin/sh\n# Rebuilds rebuilt.pdf from doc.typ. Edit the text inside the quotes of doc.typ, then run this.\ncd "$(dirname "$0")" && typst compile doc.typ rebuilt.pdf\n')
    print(f"wrote {out}/layout.json, doc.md, doc.typ, build.sh and rebuilt.pdf")


if __name__ == "__main__":
    main()
