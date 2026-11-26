#!/usr/bin/env python3
"""Usage: coverage.py original.docx [out-dir] [--accept unit,unit]
Exit 1 when an unhandled unit is present and not accepted.
"""
import json, re, sys, zipfile
from collections import Counter

STATE = {
    "rPr": ({"rFonts", "color", "sz", "szCs", "highlight", "shd", "caps", "smallCaps", "spacing", "kern", "position", "rStyle"},
            {"b", "bCs", "i", "iCs", "u", "strike", "dstrike", "vertAlign"}, {"lang", "noProof", "webHidden", "rtl", "cs", "rsid"}),
    "pPr": ({"pStyle", "jc", "ind", "spacing", "keepNext", "keepLines", "pageBreakBefore", "pBdr", "shd", "tabs", "contextualSpacing",
             "widowControl", "outlineLvl", "textAlignment", "suppressAutoHyphens", "snapToGrid", "autoSpaceDE", "autoSpaceDN", "adjustRightInd",
             "rPr", "wordWrap", "overflowPunct", "bidi", "mirrorIndents", "cnfStyle"}, {"numPr"}, {"rsid"}),
    "tblPr": ({"tblStyle", "tblW", "tblInd", "tblLayout", "tblLook", "shd", "tblBorders", "tblCellMar", "jc", "tblCellSpacing",
               "tblStyleRowBandSize", "tblStyleColBandSize"}, set(), {"tblCaption", "tblDescription"}),
    "trPr": ({"trHeight", "cnfStyle", "cantSplit", "tblHeader", "gridBefore", "gridAfter", "wBefore", "wAfter", "jc"}, set(), set()),
    "tcPr": ({"tcW", "shd", "vAlign", "noWrap", "tcBorders", "tcMar", "textDirection", "tcFitText", "hideMark", "cnfStyle"}, {"gridSpan", "vMerge", "hMerge"}, set()),
}
HOW = {"carried": "put back from the original by postprocess.py, extract_parts.py or the reference document",
       "native": "kept by Pandoc", "ignorable": "does not change how the document looks", "unhandled": "nothing keeps it"}
STRUCTURE = [
    ("section breaks inside paragraphs", r"<w:pPr>(?:(?!</w:pPr>).)*?<w:sectPr", "unhandled"),
    ("floating drawings", r"<wp:anchor\b", "unhandled"),
    ("text boxes", r"<w:txbxContent\b", "unhandled"),
    ("legacy pictures and shapes", r"<w:pict\b|<v:shape\b|<w:object\b", "unhandled"),
    ("alternate content", r"<mc:AlternateContent\b", "unhandled"),
    ("comments", r"<w:commentReference\b", "unhandled"),
    ("tracked changes", r"<w:ins\b|<w:del\b", "native"),
    ("inline pictures", r"<wp:inline\b", "native"),
    ("equations", r"<m:oMath\b", "native"),
    ("footnotes", r"<w:footnoteReference\b", "native"),
    ("hyperlinks", r"<w:hyperlink\b", "native"),
    ("page breaks", r'<w:br\b[^>]*w:type="page"', "carried"),
    ("tabs in text", r"<w:tab\s*/>", "carried"),
    ("empty body paragraphs", r"<w:p(?: [^>]*)?/>", "carried"),
    ("bookmarks", r"<w:bookmarkStart\b", "ignorable"),
]
FIELD_STATE = {"TOC": "carried", "SEQ": "carried", "PAGEREF": "carried", "HYPERLINK": "native", "PAGE": "ignorable", "NUMPAGES": "ignorable"}


def children(inner, flatten):
    for tag in flatten:
        inner = re.sub(rf"<w:{tag}\b(?:[^>]*/>|[^>]*>.*?</w:{tag}>)", f"<w:{tag}/>", inner, flags=re.S)
    return re.findall(r"<w:(\w+)\b", inner)


def ledger(path):
    z = zipfile.ZipFile(path)
    doc = z.read("word/document.xml").decode("utf-8")
    rows = Counter()
    for ctx, flat in (("rPr", ("rFonts",)), ("pPr", ("rPr", "tabs", "pBdr", "numPr", "sectPr")), ("tblPr", ("tblBorders", "tblCellMar")),
                      ("trPr", ()), ("tcPr", ("tcBorders", "tcMar"))):
        for m in re.finditer(rf"<w:{ctx}>(.*?)</w:{ctx}>", doc, re.S):
            for tag in children(m.group(1), flat):
                rows[(ctx, tag)] += 1
    out = []
    for (ctx, tag), n in sorted(rows.items()):
        carried, native, ignorable = STATE[ctx]
        state = "carried" if tag in carried else "native" if tag in native else "ignorable" if tag in ignorable or tag.startswith("rsid") else "unhandled"
        out.append({"unit": f"{ctx}/{tag}", "count": n, "state": state})
    for name, pattern, state in STRUCTURE:
        n = len(re.findall(pattern, doc, re.S))
        if n:
            out.append({"unit": name, "count": n, "state": state})
    fields = Counter(f.split()[0].upper() for f in re.findall(r'<w:instrText[^>]*>([^<]*)</w:instrText>|<w:fldSimple[^>]*w:instr="([^"]*)"', doc) for f in f if f.strip())
    for name, n in sorted(fields.items()):
        out.append({"unit": f"field {name}", "count": n, "state": FIELD_STATE.get(name, "unhandled")})
    for row in out:
        row["how"] = HOW[row["state"]]
    return out


def main():
    args = sys.argv[1:]
    accept = set()
    if "--accept" in args:
        k = args.index("--accept")
        accept = set(args[k + 1].split(","))
        args = args[:k] + args[k + 2:]
    if len(args) not in (1, 2):
        sys.exit(__doc__)
    rows = ledger(args[0])
    for r in rows:
        if r["state"] == "unhandled":
            r["accepted"] = r["unit"] in accept
    if len(args) == 2:
        with open(f"{args[1]}/coverage.json", "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=1)
    counts = Counter(r["state"] for r in rows)
    print("units:", ", ".join(f"{counts[s]} {s}" for s in ("carried", "native", "ignorable", "unhandled")))
    bad = [r for r in rows if r["state"] == "unhandled" and not r.get("accepted")]
    for r in bad:
        print(f"UNHANDLED {r['unit']}: {r['count']} in the original, and nothing keeps it")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
