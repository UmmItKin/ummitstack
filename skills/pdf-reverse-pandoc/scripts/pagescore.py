#!/usr/bin/env python3
"""Usage: pagescore.py original.pdf rebuilt.pdf work-dir
Scores each page of two PDFs against each other (RMSE, 0 is identical, 1 is completely different) and prints
a JSON object: page counts, how many pages are identical, mean, median and worst score, and the worst pages."""
import glob, json, os, re, subprocess, sys


def pages(pdf, prefix):
    subprocess.run(["pdftoppm", "-r", "30", "-png", pdf, prefix], check=True)
    return {int(re.search(r"-(\d+)\.png$", f).group(1)): f for f in glob.glob(prefix + "-*.png")}


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    a, b, work = sys.argv[1:]
    os.makedirs(work, exist_ok=True)
    pa, pb = pages(a, f"{work}/o"), pages(b, f"{work}/r")
    scores = {}
    for n in sorted(set(pa) & set(pb)):
        err = subprocess.run(["magick", "compare", "-metric", "RMSE", pa[n], pb[n], "null:"], capture_output=True, text=True).stderr
        m = re.search(r"\(([0-9.eE+-]+)\)", err)
        scores[n] = float(m.group(1)) if m else 1.0
    vals = sorted(scores.values())
    print(json.dumps({"pages_original": len(pa), "pages_rebuilt": len(pb), "scored": len(vals), "identical": sum(1 for v in vals if v == 0),
                      "mean": round(sum(vals) / len(vals), 3) if vals else None, "median": round(vals[len(vals) // 2], 3) if vals else None,
                      "worst": round(vals[-1], 3) if vals else None,
                      "worst_pages": [n for n, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:4]]}))


if __name__ == "__main__":
    main()
