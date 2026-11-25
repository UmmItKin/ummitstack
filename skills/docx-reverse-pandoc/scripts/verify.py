#!/usr/bin/env python3
"""Usage: verify.py original.docx out-dir [--no-render]
Runs the gates against out-dir/rebuilt.docx and writes out-dir/gates.json:
  fonts      the fonts the text uses and which are missing here
  structure  inventory.py compare plus coverage.py (unhandled units)
  fidelity   fidelity.py, the effective formatting of every paragraph
  look       the rendered pages, scored against the original (needs LibreOffice, pdftoppm and ImageMagick)
Exit 0 when structure and fidelity pass and the page counts agree, otherwise 1. A missing renderer is not a
failure; the look gate then says it was not verified."""
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import inventory


def run(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def main():
    args = sys.argv[1:]
    render = "--no-render" not in args
    args = [x for x in args if x != "--no-render"]
    if len(args) != 2:
        sys.exit(__doc__)
    orig, out = args
    rebuilt = os.path.join(out, "rebuilt.docx")
    gates = {}

    fonts = inventory.summarise(orig)["fonts"]
    missing = sorted(n for n, w in fonts.items() if ("document" in w or "headers and footers" in w) and inventory.font_available(n) is False)
    gates["fonts"] = {"result": "missing" if missing else "ok", "detail": ("missing for the text: " + ", ".join(missing)) if missing else f"{len(fonts)} fonts named, all installed"}

    code, text = run(sys.executable, os.path.join(HERE, "inventory.py"), orig, rebuilt)
    fails = [l for l in text.splitlines() if l.startswith("FAIL")]
    code2, text2 = run(sys.executable, os.path.join(HERE, "coverage.py"), orig)
    unhandled = [l for l in text2.splitlines() if l.startswith("UNHANDLED")]
    gates["structure"] = {"result": "pass" if code == 0 and code2 == 0 else "fail", "detail": f"{len(fails)} differences, {len(unhandled)} unhandled units", "lines": fails + unhandled}

    code, text = run(sys.executable, os.path.join(HERE, "fidelity.py"), orig, rebuilt)
    last = text.splitlines()[-1] if text else ""
    gates["fidelity"] = {"result": "pass" if code == 0 else "fail", "detail": last, "lines": [l for l in text.splitlines() if l.startswith("FAIL")]}

    look = {"result": "not verified", "detail": "no renderer or --no-render"}
    if render and all(shutil.which(t) for t in ("soffice", "pdftoppm", "magick")):
        n = 1
        while os.path.exists(os.path.join(out, f"verify-{n}")):
            n += 1
        d = os.path.join(out, f"verify-{n}")
        code, text = run("sh", os.path.join(HERE, "render.sh"), orig, rebuilt, d, "1", "2")
        if code == 0:
            code, text = run(sys.executable, os.path.join(HERE, "pagescore.py"), os.path.join(d, "o", "original.pdf"), os.path.join(d, "r", "rebuilt.pdf"), os.path.join(d, "score"))
            s = json.loads(text.splitlines()[-1])
            same = s["pages_original"] == s["pages_rebuilt"]
            look = {"result": "pass" if same else "fail", "scores": s, "folder": f"verify-{n}",
                    "detail": f"pages {s['pages_original']} and {s['pages_rebuilt']}, identical {s['identical']}, mean {s['mean']}, median {s['median']}, worst {s['worst']} (pages {s['worst_pages']})"}
            if missing:
                look["detail"] += "; rendered with substitute fonts"
    gates["look"] = look

    with open(os.path.join(out, "gates.json"), "w", encoding="utf-8") as f:
        json.dump(gates, f, indent=1)
    for k, v in gates.items():
        print(f"{k:10s} {v['result']:12s} {v.get('detail', '')}")
    sys.exit(0 if gates["structure"]["result"] == "pass" and gates["fidelity"]["result"] == "pass" and gates["look"]["result"] != "fail" else 1)


if __name__ == "__main__":
    main()
