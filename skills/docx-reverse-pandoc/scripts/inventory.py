#!/usr/bin/env python3
"""Summarise a DOCX, or compare a rebuild with the original.

Usage: inventory.py A.docx              print a summary of A
       inventory.py --widths A.docx     print the column widths of each table, one line per table
       inventory.py --missing-fonts A.docx   (the flag may come before or after the file) print the fonts the text needs that are not installed; exit 1 if any
       inventory.py A.docx B.docx       compare B (the rebuild) with A (the original)
       --tol 0.05                       relative tolerance for table column widths
The zip is read in memory and nothing is extracted. Exit 1 when a compare finds a difference.
"""
import re, subprocess, sys, zipfile
import xml.etree.ElementTree as ET
from collections import Counter

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
M = "{http://schemas.openxmlformats.org/officeDocument/2006/math}"
LIMIT = 100 * 1024 * 1024
MANAGED = {"Body Text", "First Paragraph", "Compact", "Block Text", "Footnote Text", "Footnote Reference"}


def load(z, name):
    try:
        info = z.getinfo(name)
    except KeyError:
        return None
    if info.file_size > LIMIT:
        sys.exit(f"error: {name} is larger than {LIMIT} bytes")
    data = z.read(name)
    if b"<!ENTITY" in data:
        sys.exit(f"error: {name} declares XML entities; refusing to parse")
    return ET.fromstring(data)


def has_text(el):
    return any((t.text or "").strip() for t in el.iter(W + "t"))


def is_empty(p):
    return not (has_text(p) or p.find(f".//{W}drawing") is not None or p.find(f".//{W}pict") is not None
                or p.find(f".//{W}br") is not None or p.find(f"{W}pPr/{W}sectPr") is not None)


def text_of(el):
    return re.sub(r"\s+", " ", "".join(t.text or "" for t in el.iter(W + "t"))).strip()


def font_usage(z):
    """Font names used by styles, body text, headers and footers, with theme fonts resolved."""
    theme = z.read("word/theme/theme1.xml").decode("utf-8", "replace") if "word/theme/theme1.xml" in z.namelist() else ""
    def theme_font(kind):
        m = re.search(rf"<a:{kind}Font>\s*<a:latin typeface=\"([^\"]*)\"", theme)
        return m.group(1) if m else None
    themes = {"major": theme_font("major"), "minor": theme_font("minor")}
    found = {}
    parts = {"styles": ["word/styles.xml"], "document": ["word/document.xml"],
             "headers and footers": [n for n in z.namelist() if re.fullmatch(r"word/(header|footer)\d*\.xml", n)]}
    for where, names in parts.items():
        for name in names:
            xml = z.read(name).decode("utf-8", "replace")
            for tag in re.findall(r"<w:rFonts\b[^>]*/?>", xml):
                for attr, val in re.findall(r'w:(ascii|hAnsi|cs|eastAsia|asciiTheme|hAnsiTheme|cstheme|eastAsiaTheme)="([^"]*)"', tag):
                    if attr.endswith(("Theme", "theme")):
                        val = themes.get("major" if val.startswith("major") else "minor")
                    for one in re.split(r"[;,]", val or ""):
                        one = one.strip()
                        if one and one.lower() not in ("monospace", "serif", "sans-serif"):
                            found.setdefault(one, set()).add(where)
    body = z.read("word/document.xml").decode("utf-8", "replace")
    sty = z.read("word/styles.xml").decode("utf-8", "replace")
    for sid in set(re.findall(r'<w:rStyle w:val="(DF\d+)"', body)):
        m = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, sty, re.S)
        for tag in re.findall(r"<w:rFonts\b[^>]*/>", m.group(0) if m else ""):
            for val in re.findall(r'w:(?:ascii|hAnsi|cs|eastAsia)="([^"]*)"', tag):
                for one in re.split(r"[;,]", val):
                    one = one.strip()
                    if one and one.lower() not in ("monospace", "serif", "sans-serif"):
                        found.setdefault(one, set()).add("document")
    return found


SUBSTITUTES = {"Calibri": "Carlito", "Cambria": "Caladea", "Arial": "Liberation Sans", "Times New Roman": "Liberation Serif",
               "Courier New": "Liberation Mono", "Helvetica": "Liberation Sans", "Consolas": "Inconsolata (similar, not the same widths)"}


def font_available(name):
    try:
        out = subprocess.run(["fc-match", "-f", "%{family}", name], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None
    return name.lower() in [f.strip().lower() for f in out.split(",")]


def summarise(path):
    z = zipfile.ZipFile(path)
    styles = load(z, "word/styles.xml")
    names, custom, default, based = {}, set(), "Normal", {}
    if styles is not None:
        for s in styles.findall(W + "style"):
            n = s.find(W + "name")
            sid = s.get(W + "styleId")
            names[sid] = n.get(W + "val") if n is not None else sid
            b = s.find(W + "basedOn")
            if b is not None:
                based[sid] = b.get(W + "val")
            if s.get(W + "customStyle") in ("1", "true"):
                custom.add(names[sid])
            if s.get(W + "type") == "paragraph" and s.get(W + "default") in ("1", "true"):
                default = names[sid]
    doc = load(z, "word/document.xml")
    if doc is None:
        sys.exit("error: not a DOCX (no word/document.xml)")
    for sid in list(names):
        base = sid
        while re.fullmatch(r"D[FP]\d+", base) and base in based:
            base = based[base]
        names[sid] = names.get(base, names[sid]) if base != sid else names[sid]

    para, char, num_ids, numbered, empty = Counter(), Counter(), set(), 0, 0
    for p in doc.iter(W + "p"):
        if is_empty(p):
            empty += 1
            continue
        ppr = p.find(W + "pPr")
        ps = ppr.find(W + "pStyle") if ppr is not None else None
        sid = ps.get(W + "val") if ps is not None else None
        para[names.get(sid, sid) if sid else default] += 1
        nid = ppr.find(f"{W}numPr/{W}numId") if ppr is not None else None
        if nid is not None and nid.get(W + "val") not in (None, "0"):
            num_ids.add(nid.get(W + "val"))
            numbered += 1
    for r in doc.iter(W + "r"):
        if not has_text(r):
            continue
        rpr = r.find(W + "rPr")
        rs = rpr.find(W + "rStyle") if rpr is not None else None
        if rs is not None:
            char[names.get(rs.get(W + "val"), rs.get(W + "val"))] += 1

    sections, table_rows = [], []
    for sp in doc.iter(W + "sectPr"):
        sz, mar = sp.find(W + "pgSz"), sp.find(W + "pgMar")
        if sz is None or mar is None:
            continue
        sections.append((sz.get(W + "w"), sz.get(W + "h"), sz.get(W + "orient") or "portrait",
                         mar.get(W + "top"), mar.get(W + "right"), mar.get(W + "bottom"), mar.get(W + "left")))
    tables = []
    for t in doc.iter(W + "tbl"):
        tables.append([int(g.get(W + "w") or 0) for g in t.findall(f"{W}tblGrid/{W}gridCol")])
        table_rows.append(len(t.findall(W + "tr")))
    fields = Counter()
    for it in doc.iter(W + "instrText"):
        tok = (it.text or "").split()
        if tok:
            fields[tok[0].upper()] += 1
    for fs in doc.iter(W + "fldSimple"):
        tok = (fs.get(W + "instr") or "").split()
        if tok:
            fields[tok[0].upper()] += 1

    hf = []
    for name in sorted(n for n in z.namelist() if re.fullmatch(r"word/(header|footer)\d*\.xml", n)):
        t = text_of(load(z, name))
        if t:
            hf.append(t)


    used = {n for n in custom if para.get(n) or char.get(n)}
    return {
        "para": para, "char": char, "custom": used,
        "headings": Counter({k: v for k, v in para.items() if re.match(r"(?i)heading \d", k) or k in ("Title", "Subtitle")}),
        "empty": empty, "numbered": numbered, "num_ids": len(num_ids), "sections": sections, "tables": tables, "table_rows": table_rows,
        "math": sum(1 for _ in doc.iter(M + "oMath")),
        "footnotes": sum(1 for _ in doc.iter(W + "footnoteReference")) + sum(1 for _ in doc.iter(W + "endnoteReference")),
        "comments": sum(1 for _ in doc.iter(W + "commentReference")),
        "revisions": sum(1 for _ in doc.iter(W + "ins")) + sum(1 for _ in doc.iter(W + "del")),
        "textboxes": sum(1 for _ in doc.iter(W + "txbxContent")),
        "controls": sum(1 for _ in doc.iter(W + "sdt")),
        "fields": fields, "header_footer": hf,
        "fonts": font_usage(z),
        "embedded_fonts": sum(1 for n in z.namelist() if n.startswith("word/fonts/") and not n.endswith("/")),
        "images": sum(1 for _ in doc.iter(W + "drawing")) + sum(1 for _ in doc.iter(W + "pict")),
        "page_breaks": sum(1 for b in doc.iter(W + "br") if b.get(W + "type") == "page") + sum(1 for _ in doc.iter(W + "pageBreakBefore")),
        "background": 1 if doc.find(W + "background") is not None else 0,
        "media": sum(1 for n in z.namelist() if n.startswith("word/media/") and not n.endswith("/")),
    }


def show(s):
    print("paragraph styles:", ", ".join(f"{k} {v}" for k, v in s["para"].most_common()))
    print("character styles:", ", ".join(f"{k} {v}" for k, v in s["char"].most_common()) or "none")
    print("custom styles:", ", ".join(sorted(s["custom"])) or "none")
    print("headings:", ", ".join(f"{k} {v}" for k, v in sorted(s["headings"].items())) or "none")
    print(f"numbering: {s['numbered']} numbered paragraphs, {s['num_ids']} lists; empty paragraphs: {s['empty']}")
    for i, sec in enumerate(s["sections"], 1):
        print(f"section {i}: {sec[0]}x{sec[1]} {sec[2]}, margins top {sec[3]} right {sec[4]} bottom {sec[5]} left {sec[6]} (twips)")
    for i, t in enumerate(s["tables"], 1):
        print(f"table {i}: {len(t)} columns, {s['table_rows'][i - 1]} rows, widths {t}")
    fonts = []
    for name in sorted(s["fonts"]):
        ok = font_available(name)
        fonts.append(f"{name} ({', '.join(sorted(s['fonts'][name]))}) {'installed' if ok else 'MISSING' if ok is False else 'unknown'}")
    print("fonts:", "; ".join(fonts) or "none named (the document uses its defaults)")
    missing = [n for n in s["fonts"] if font_available(n) is False]
    in_text = sorted(n for n in missing if "document" in s["fonts"][n] or "headers and footers" in s["fonts"][n])
    if in_text:
        print(f"MISSING FONTS used by the text: {', '.join(in_text)}. A render here uses a substitute, so spacing and page breaks can differ, and Word needs these fonts too.")
    other = sorted(set(missing) - set(in_text))
    if other:
        print(f"missing fonts defined only in styles: {', '.join(other)}")
    hints = [f"{n} -> {SUBSTITUTES[n]}" for n in sorted(missing) if n in SUBSTITUTES]
    if hints:
        print("closest installable substitutes for a render:", "; ".join(hints))
    if s["embedded_fonts"]:
        print(f"embedded fonts in the package: {s['embedded_fonts']}")
    print(f"page breaks: {s['page_breaks']}, page background colour: {'yes' if s['background'] else 'no'}")
    print(f"math: {s['math']}, footnotes: {s['footnotes']}, images used: {s['images']}, media files in the package: {s['media']}")
    print("headers and footers:", " | ".join(s["header_footer"]) or "none")
    risk = [f"{k} {s[k]}" for k in ("textboxes", "controls", "comments", "revisions") if s[k]]
    risk += [f"field {k} {v}" for k, v in s["fields"].items()]
    print("at risk in a Pandoc round trip:", ", ".join(risk) or "none")


def compare(a, b, tol):
    diffs, info = [], []

    def same(label, x, y):
        if x != y:
            diffs.append(f"{label}: original {x}, rebuilt {y}")

    same("headings", dict(a["headings"]), dict(b["headings"]))
    for name in sorted(a["custom"] - MANAGED):
        same(f"custom style {name!r} paragraphs", a["para"].get(name, 0), b["para"].get(name, 0))
        same(f"custom style {name!r} runs", a["char"].get(name, 0), b["char"].get(name, 0))
    same("sections", a["sections"], b["sections"])
    same("headers and footers", sorted(a["header_footer"]), sorted(b["header_footer"]))
    fa = {n for n, w in a["fonts"].items() if "document" in w}
    fb = {n for n, w in b["fonts"].items() if "document" in w}
    if fa - fb:
        diffs.append(f"fonts used by the text and lost: {', '.join(sorted(fa - fb))}")
    same("page breaks", a["page_breaks"], b["page_breaks"])
    same("page background colour", a["background"], b["background"])
    same("math", a["math"], b["math"])
    same("footnotes", a["footnotes"], b["footnotes"])
    same("tables", len(a["tables"]), len(b["tables"]))
    if len(a["tables"]) == len(b["tables"]) and a["table_rows"] != b["table_rows"]:
        diffs.append(f"table rows: original {a['table_rows']}, rebuilt {b['table_rows']}")
    for i, (ta, tb) in enumerate(zip(a["tables"], b["tables"]), 1):
        if len(ta) != len(tb):
            diffs.append(f"table {i} columns: original {len(ta)}, rebuilt {len(tb)}")
        elif sum(ta) and not sum(tb):
            diffs.append(f"table {i} widths: original fixed, rebuilt automatic (use relative widths in the Markdown table)")
        elif sum(ta) and any(abs(x / sum(ta) - y / sum(tb)) > tol for x, y in zip(ta, tb)):
            dashes = " ".join(str(max(3, round(x / sum(ta) * 60))) for x in ta)
            diffs.append(f"table {i} widths differ by more than {tol:.0%}: original {ta}, rebuilt {tb}. Set the separator line to dashes of {dashes}")
    if b["images"] < a["images"]:
        diffs.append(f"images lost: original {a['images']}, rebuilt {b['images']}")
    for k in ("textboxes", "controls", "comments", "revisions"):
        if b[k] < a[k]:
            diffs.append(f"{k} lost: original {a[k]}, rebuilt {b[k]}")
    for k, v in a["fields"].items():
        if b["fields"].get(k, 0) < v:
            info.append(f"field {k} not kept: original {v}, rebuilt {b['fields'].get(k, 0)} (a TOC can be regenerated with --toc)")
    if a["empty"] != b["empty"]:
        info.append(f"empty paragraphs: original {a['empty']}, rebuilt {b['empty']} (Pandoc drops empty paragraphs)")
    if a["para"] != b["para"]:
        info.append("paragraph style counts differ, which is expected because Pandoc writes Body Text and First Paragraph")
    return diffs, info


def main():
    args, tol = sys.argv[1:], 0.05
    if "--missing-fonts" in args and len(args) == 2:
        fonts = summarise([a for a in args if a != "--missing-fonts"][0])["fonts"]
        missing = sorted(n for n, w in fonts.items() if ("document" in w or "headers and footers" in w) and font_available(n) is False)
        print("\n".join(missing))
        sys.exit(1 if missing else 0)
    if len(args) == 2 and args[0] == "--widths":
        for t in summarise(args[1])["tables"]:
            print(" ".join(map(str, t)))
        return
    if "--tol" in args:
        k = args.index("--tol")
        tol = float(args[k + 1])
        args = args[:k] + args[k + 2:]
    if len(args) not in (1, 2):
        sys.exit(__doc__)
    try:
        a = summarise(args[0])
        b = summarise(args[1]) if len(args) == 2 else None
    except (OSError, zipfile.BadZipFile, ET.ParseError) as e:
        sys.exit(f"error: {e}")
    if b is None:
        show(a)
        return
    diffs, info = compare(a, b, tol)
    for d in diffs:
        print("FAIL", d)
    for i in info:
        print("info", i)
    print("result:", "pass" if not diffs else f"fail ({len(diffs)} differences)")
    print("not checked: pagination, line breaks, fonts and anything visual")
    sys.exit(1 if diffs else 0)


if __name__ == "__main__":
    main()
