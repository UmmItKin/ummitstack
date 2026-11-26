#!/usr/bin/env python3
"""Usage: pdfinfo.py file.pdf
"""
import json, re, subprocess, sys
import xml.etree.ElementTree as ET


ZOOM = 3  # pdftohtml stops scaling above 3


def run(*args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"{args[0]} failed: {r.stderr.strip()[:200]}")
    return r.stdout


def clean_family(name):
    name = re.sub(r"^[A-Z]{6}\+", "", name).split("-")[0].split(",")[0]
    name = re.sub(r"(PSMT|MT|PS)$", "", name)
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name).strip()


def fonts(pdf):
    out, seen = [], set()
    for line in run("pdffonts", pdf).splitlines()[2:]:
        m = re.match(r"(\S+)\s+.*?\s(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$", line)
        if m and (fam := clean_family(m.group(1))) not in seen:
            seen.add(fam)
            out.append({"family": fam, "embedded": m.group(2) == "yes"})
    return out


def installed(family):
    got = run("fc-match", "-f", "%{family}", family).split(",")[0].strip()
    return None if got.lower() == family.lower() else got


def pages(pdf):
    root = ET.fromstring(run("pdftohtml", "-xml", "-i", "-zoom", str(ZOOM), "-stdout", pdf).split("?>", 1)[1].replace("<!DOCTYPE pdf2xml SYSTEM \"pdf2xml.dtd\">", ""))
    spec = {f.get("id"): (clean_family(f.get("family")), round(float(f.get("size")) / ZOOM, 2), f.get("color")) for f in root.iter("fontspec")}
    sizes = [(float(a), float(b)) for a, b in re.findall(r"Page\s+\d+ size:\s+([\d.]+) x ([\d.]+) pts", run("pdfinfo", "-f", "1", "-l", "100000", pdf))]
    result = []
    for k, pg in enumerate(root.iter("page")):
        runs = []
        for t in pg.iter("text"):
            text = "".join(t.itertext())
            if not text.strip():
                continue
            fam, size, color = spec[t.get("font")]
            z = lambda k: round(float(t.get(k)) / ZOOM, 2)
            runs.append({"text": text, "left": z("left"), "top": z("top"), "width": z("width"), "height": z("height"), "family": fam, "size": size, "color": color,
                         "bold": t.find(".//b") is not None, "italic": t.find(".//i") is not None})
        w, h = sizes[k] if k < len(sizes) else (float(pg.get("width")) / ZOOM, float(pg.get("height")) / ZOOM)
        result.append({"width": round(w, 2), "height": round(h, 2), "runs": runs})
    return result


def links(pdf):
    return len(re.findall(r"<a href=", run("pdftohtml", "-xml", "-i", "-zoom", "1", "-stdout", pdf)))


def facts(pdf):
    info = run("pdfinfo", pdf)
    get = lambda k: (re.search(rf"^{k}:\s*(.*)$", info, re.M) or [None, ""])[1].strip()
    pg = pages(pdf)
    return {"pages": len(pg), "tagged": get("Tagged") == "yes", "encrypted": get("Encrypted").startswith("yes"), "form": get("Form") not in ("", "none"), "links": links(pdf),
            "runs_per_page": [len(p["runs"]) for p in pg], "fonts": [dict(f, stand_in=installed(f["family"]) or "") for f in fonts(pdf)], "images": max(0, len(run("pdfimages", "-list", pdf).splitlines()) - 2)}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    print(json.dumps(facts(sys.argv[1]), indent=1))
