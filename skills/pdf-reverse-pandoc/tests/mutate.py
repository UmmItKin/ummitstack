#!/usr/bin/env python3
"""Usage: mutate.py doc.typ out.typ KIND
KIND: size, word, move, shape, spacing
"""
import re, sys

src, dst, kind = sys.argv[1:]
s = open(src, encoding="utf-8").read()
lines = s.split("\n")
idx = [i for i, l in enumerate(lines) if l.startswith("#place(top + left, dx") and "text(" in l]
shapes = [i for i, l in enumerate(lines) if "curve(" in l]
if kind == "size":
    lines[idx[3]] = re.sub(r"size: [\d.]+pt", "size: 13pt", lines[idx[3]], count=1)
elif kind == "word":
    lines[idx[3]] = lines[idx[3]].replace("bold", "BOLD", count=1) if "bold" in lines[idx[3]] and "weight" not in lines[idx[3]] else re.sub(r'\[#"([^"]*)"\]', lambda m: '[#"' + m.group(1)[::-1] + '"]', lines[idx[3]], count=1)
elif kind == "move":
    lines[idx[3]] = re.sub(r"dy: ([\d.]+)pt", lambda m: f"dy: {float(m.group(1)) + 12}pt", lines[idx[3]], count=1)
elif kind == "shape":
    del lines[shapes[0]]
elif kind == "spacing":
    lines[idx[3]] = re.sub(r"\)\[#", "), tracking: 1.5pt)[#", lines[idx[3]], count=1).replace("), tracking: 1.5pt)[#", ", tracking: 1.5pt)[#", count=1)
else:
    sys.exit("unknown kind")
open(dst, "w", encoding="utf-8").write("\n".join(lines))
