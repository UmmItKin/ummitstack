#!/usr/bin/env python3
"""Usage: verify.py original.pdf out-dir [--no-render] [--accept-unsupported]
Runs the gates against out-dir/rebuilt.pdf and writes out-dir/gates.json:
  fonts      the fonts the text uses and which are not installed here (a stand-in is used for those)
  structure  the text layer exists, and no curves or pictures that this workflow cannot redraw
  fidelity   fidelity.py: text, font, size, bold, italic, baseline, width, shapes, page count and size of every run
  look       the pages rendered and scored against the original (needs pdftoppm and ImageMagick)
Exit 0 when structure and fidelity pass and the look gate did not fail."""
import json, os, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import graphics
import pdfinfo


def main():
    args = sys.argv[1:]
    render, accept = "--no-render" not in args, "--accept-unsupported" in args
    args = [a for a in args if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    orig, out = args
    rebuilt = os.path.join(out, "rebuilt.pdf")
    gates = {}
    facts = pdfinfo.facts(orig)
    swapped = {f["family"]: s for f in facts["fonts"] if (s := pdfinfo.installed(f["family"]))}
    gates["fonts"] = {"result": "substituted" if swapped else "ok",
                      "detail": ("not installed, stand-in used: " + ", ".join(f"{k} -> {v}" for k, v in sorted(swapped.items()))) if swapped else f"{len(facts['fonts'])} fonts, all installed"}

    shapes = graphics.pages(orig, facts["pages"])
    unsupported = sum(u for _, u in shapes)
    notes = []
    if not sum(facts["runs_per_page"]):
        notes.append("no text layer")
    if unsupported and not accept:
        notes.append(f"{unsupported} curves or pictures that are not redrawn")
    if facts["encrypted"]:
        notes.append("encrypted")
    gates["structure"] = {"result": "fail" if notes else "pass", "detail": "; ".join(notes) or f"{facts['pages']} pages, text layer present, {sum(len(s) for s, _ in shapes)} line shapes", "lines": notes}

    r = subprocess.run([sys.executable, os.path.join(HERE, "fidelity.py"), orig, rebuilt] + (["--accept-unsupported"] if accept else []), capture_output=True, text=True)
    lines = r.stdout.strip().splitlines()
    gates["fidelity"] = {"result": "pass" if r.returncode == 0 else "fail", "detail": lines[-1] if lines else r.stderr.strip()[:200], "lines": [l for l in lines if l.startswith("FAIL")]}

    look = {"result": "not verified", "detail": "no renderer or --no-render"}
    if render and shutil.which("pdftoppm") and shutil.which("magick"):
        n = 1
        while os.path.exists(os.path.join(out, f"verify-{n}")):
            n += 1
        d = os.path.join(out, f"verify-{n}")
        os.makedirs(d)
        r = subprocess.run([sys.executable, os.path.join(HERE, "pagescore.py"), orig, rebuilt, os.path.join(d, "score")], capture_output=True, text=True)
        if r.returncode == 0:
            s = json.loads(r.stdout.splitlines()[-1])
            look = {"result": "pass" if s["pages_original"] == s["pages_rebuilt"] else "fail", "scores": s, "folder": f"verify-{n}",
                    "detail": f"pages {s['pages_original']} and {s['pages_rebuilt']}, identical {s['identical']}, mean {s['mean']}, median {s['median']}, worst {s['worst']} (pages {s['worst_pages']})"}
            if swapped:
                look["detail"] += "; rendered with stand-in fonts"
    gates["look"] = look
    gates["env"] = {t: (subprocess.run([t, "--version"], capture_output=True, text=True).stdout.splitlines() or ["?"])[0] for t in ("typst",) if shutil.which(t)}
    gates["env"]["pdftotext"] = (subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr.splitlines() or ["?"])[0]
    json.dump(gates, open(os.path.join(out, "gates.json"), "w"), indent=1)
    for k in ("fonts", "structure", "fidelity", "look"):
        print(f"{k:10s} {gates[k]['result']:12s} {gates[k].get('detail', '')}")
    sys.exit(0 if gates["structure"]["result"] == "pass" and gates["fidelity"]["result"] == "pass" and gates["look"]["result"] != "fail" else 1)


if __name__ == "__main__":
    main()
