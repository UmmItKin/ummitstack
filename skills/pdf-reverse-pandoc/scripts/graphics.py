#!/usr/bin/env python3
"""Usage: graphics.py file.pdf     print the number of shapes and unsupported items per page
"""
import os, re, subprocess, sys, tempfile
import xml.etree.ElementTree as ET

NS = "{http://www.w3.org/2000/svg}"


def matrix(text):
    m = re.match(r"matrix\(([^)]*)\)", text or "")
    return [float(x) for x in re.split(r"[ ,]+", m.group(1).strip())] if m else [1, 0, 0, 1, 0, 0]


def mul(p, c):
    a, b, cc, d, e, f = c
    pa, pb, pc, pd, pe, pf = p
    return [pa * a + pc * b, pb * a + pd * b, pa * cc + pc * d, pb * cc + pd * d, pa * e + pc * f + pe, pb * e + pd * f + pf]


def color(value):
    m = re.match(r"rgb\(([\d.]+)%, ([\d.]+)%, ([\d.]+)%\)", value or "")
    return None if not m else "#%02x%02x%02x" % tuple(round(float(x) * 2.55) for x in m.groups())


def points(d):
    toks = re.findall(r"[A-Za-z]|-?[\d.]+(?:e-?\d+)?", d)
    pts, i, cmd, closed, cur = [], 0, None, False, (0.0, 0.0)
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
            if cmd in "Zz":
                closed = True
            elif cmd not in "MLHV":
                return None
            continue
        if cmd in ("M", "L"):
            cur = (float(toks[i]), float(toks[i + 1]))
            i += 2
        elif cmd == "H":
            cur = (float(toks[i]), cur[1])
            i += 1
        elif cmd == "V":
            cur = (cur[0], float(toks[i]))
            i += 1
        else:
            return None
        pts.append(cur)
    return pts, closed


def page_shapes(svg):
    root = ET.parse(svg).getroot()
    shapes, unsupported = [], 0

    def walk(e, m):
        nonlocal unsupported
        for c in e:
            if c.tag == NS + "defs" or c.tag == NS + "clipPath":
                continue
            cm = mul(m, matrix(c.get("transform")))
            if c.tag == NS + "image":
                unsupported += 1
            elif c.tag == NS + "path":
                stroke, fill = color(c.get("stroke")), color(c.get("fill"))
                if not stroke and not fill:
                    continue
                got = points(c.get("d", ""))
                if got is None:
                    unsupported += 1
                    continue
                pts, closed = got
                a, b, cc, d, e2, f = cm
                shapes.append({"points": [(round(a * x + cc * y + e2, 2), round(b * x + d * y + f, 2)) for x, y in pts], "closed": closed,
                               "stroke": stroke, "fill": fill, "width": round(float(c.get("stroke-width", 1)) * abs(a), 2) if stroke else 0})
            walk(c, cm)

    walk(root, [1, 0, 0, 1, 0, 0])
    return shapes, unsupported


def glyph_origins(svg):
    root = ET.parse(svg).getroot()
    out = []

    def walk(e, m):
        for c in e:
            if c.tag in (NS + "defs", NS + "clipPath"):
                continue
            cm = mul(m, matrix(c.get("transform")))
            if c.tag == NS + "use" and c.get("x") is not None:
                x, y = float(c.get("x")), float(c.get("y"))
                out.append((cm[0] * x + cm[2] * y + cm[4], cm[1] * x + cm[3] * y + cm[5]))
            walk(c, cm)

    walk(root, [1, 0, 0, 1, 0, 0])
    return out


def attach_baselines(pgs, pdf):
    with tempfile.TemporaryDirectory() as d:
        for n, pg in enumerate(pgs, 1):
            svg = os.path.join(d, f"b{n}.svg")
            r = subprocess.run(["pdftocairo", "-svg", "-f", str(n), "-l", str(n), pdf, svg], capture_output=True, text=True)
            if r.returncode:
                raise SystemExit("pdftocairo failed: " + r.stderr.strip()[:200])
            gl = glyph_origins(svg)
            taken = set()
            for run in sorted(pg["runs"], key=lambda r: r["top"]):
                want = run["top"] + run["height"] * 0.8
                near = [g for g in gl if run["top"] - 3 <= g[1] <= run["top"] + run["height"] + 3 and abs(g[0] - run["left"]) < 4
                        and (round(g[1], 1), round(run["left"])) not in taken]
                if near:
                    g = min(near, key=lambda g: (abs(g[0] - run["left"]) > 1, abs(g[1] - want)))
                    taken.add((round(g[1], 1), round(run["left"])))
                    run["base"] = round(g[1], 2)
                else:
                    run["base"] = round(want, 2)
    return pgs


def pages(pdf, count):
    out = []
    with tempfile.TemporaryDirectory() as d:
        for n in range(1, count + 1):
            svg = os.path.join(d, f"p{n}.svg")
            r = subprocess.run(["pdftocairo", "-svg", "-f", str(n), "-l", str(n), pdf, svg], capture_output=True, text=True)
            if r.returncode:
                raise SystemExit("pdftocairo failed: " + r.stderr.strip()[:200])
            out.append(page_shapes(svg))
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    n = int(re.search(r"^Pages:\s+(\d+)", subprocess.run(["pdfinfo", sys.argv[1]], capture_output=True, text=True).stdout, re.M).group(1))
    for i, (s, u) in enumerate(pages(sys.argv[1], n), 1):
        print(f"page {i}: {len(s)} shapes, {u} unsupported")
