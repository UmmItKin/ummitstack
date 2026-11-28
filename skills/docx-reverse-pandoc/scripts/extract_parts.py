#!/usr/bin/env python3
"""Usage: extract_parts.py original.docx out-dir
"""
import json, re, sys, zipfile, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import inventory

DF_TAGS = ("rFonts", "color", "sz", "szCs", "highlight", "shd", "caps", "smallCaps", "spacing", "kern", "position")
DP_TAGS = ("jc", "ind", "spacing", "keepNext", "keepLines", "pageBreakBefore", "pBdr", "shd", "tabs", "contextualSpacing")
CELL_TAGS = ("tcBorders", "shd", "noWrap", "tcMar", "textDirection", "tcFitText", "vAlign", "hideMark")
TOKEN = re.compile(r"<(/?)w:(tbl|sdt|p)(?=[\s>/])[^>]*?(/?)>")
KEEP = re.compile(r"<w:t(?: [^>]*)?>[^<]*\S|<w:drawing|<w:pict|<w:br\b|<w:sectPr|<w:fldChar|<w:fldSimple|<w:object|<w:instrText")


def tag_re(tags):
    return r"<w:(?P<t>%s)\b(?:[^>]*?/>|[^>]*?>.*?</w:(?P=t)>)" % "|".join(tags)


def declare(block, doc):
    root = re.search(r"<w:document\b[^>]*>", doc).group()
    known = dict(re.findall(r'xmlns:(\w+)="([^"]+)"', root))
    used = set(re.findall(r"</?(\w+):", block)) | set(re.findall(r"\s(\w+):\w+=", block))
    extra = "".join(f' xmlns:{p}="{known[p]}"' for p in sorted(used) if p in known)
    return re.sub(r"^<w:(sdt|p)\b", lambda m: m.group() + extra, block, count=1)


def toc_block(s):
    k = s.find('w:docPartGallery w:val="Table of Contents"')
    if k < 0:
        return None
    start = s.rfind("<w:sdt>", 0, k)
    if start < 0:
        start = s.rfind("<w:sdt ", 0, k)
    depth = 0
    for m in re.finditer(r"<w:sdt[ >]|</w:sdt>", s[start:]):
        depth += -1 if m.group().startswith("</") else 1
        if depth == 0:
            return declare(s[start:start + m.end()], s)
    return None


def style_maps(styles):
    names, default_p, default_c = {}, "Normal", None
    for m in re.finditer(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>.*?</w:style>', styles, re.S):
        n = re.search(r'<w:name w:val="([^"]*)"', m.group())
        names[m.group(1)] = n.group(1) if n else m.group(1)
        head = m.group().split(">", 1)[0]
        if 'w:type="paragraph"' in head and 'w:default="1"' in head:
            default_p = m.group(1)
    if "DefaultParagraphFont" in names:
        default_c = "DefaultParagraphFont"
    return names, default_p, default_c


def direct_run_styles(doc, default_c):
    registry = {}

    def run(m):
        r = m.group(0)
        pr = re.search(r"<w:rPr>(.*?)</w:rPr>", r, re.S)
        if "<w:t" not in r or not pr:
            return r
        inner = pr.group(1)
        props = [x.group(0) for x in re.finditer(tag_re(DF_TAGS), inner)]
        if not props:
            return r
        rs = re.search(r'<w:rStyle w:val="([^"]*)"\s*/>', inner)
        sid = registry.setdefault((rs.group(1) if rs else default_c, tuple(props)), f"DF{len(registry) + 1}")
        rest = re.sub(r'<w:rStyle w:val="[^"]*"\s*/>', "", re.sub(tag_re(DF_TAGS), "", inner))
        return r.replace(pr.group(0), f'<w:rPr><w:rStyle w:val="{sid}"/>{rest}</w:rPr>', 1)

    doc = re.sub(r"<w:r(?= |>)[^>]*>.*?</w:r>", run, doc, flags=re.S)
    defs = []
    for (base, props), sid in registry.items():
        based = f'<w:basedOn w:val="{base}"/>' if base else ""
        defs.append(f'<w:style w:type="character" w:customStyle="1" w:styleId="{sid}"><w:name w:val="{sid}"/>{based}<w:rPr>{"".join(props)}</w:rPr></w:style>')
    return doc, defs


def top_level_paragraphs(s):
    spans, depth, start = [], 0, None
    for m in TOKEN.finditer(s, s.find("<w:body")):
        closing, name, selfclose = m.group(1) == "/", m.group(2), m.group(3) == "/"
        if name in ("tbl", "sdt"):
            depth += -1 if closing else (0 if selfclose else 1)
        elif not depth:
            if selfclose and not closing:
                spans.append((m.start(), m.end()))
            elif not closing:
                start = m.start()
            else:
                spans.append((start, m.end()))
    return spans


def empty_paragraphs(doc):
    kept = []
    for a, b in reversed(top_level_paragraphs(doc)):
        p = doc[a:b]
        if not KEEP.search(p):
            kept.append((a, b, declare(re.sub(r"\s+", " ", p), doc)))
    kept.reverse()
    for n, (a, b, _) in reversed(list(enumerate(kept, 1))):
        doc = doc[:a] + f"<w:p><w:r><w:t>EMPTYPARAMARK{n}END</w:t></w:r></w:p>" + doc[b:]
    return doc, [x[2] for x in kept]


def direct_paragraph_styles(doc, names, default_p, styles):
    registry = {}
    for a, b in reversed(top_level_paragraphs(doc)):
        p = doc[a:b]
        pr = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
        if not pr or "<w:numPr>" in pr.group(1) or "<w:sectPr" in pr.group(1):
            continue
        mark = re.search(r"<w:rPr>.*?</w:rPr>", pr.group(1), re.S)
        inner = pr.group(1).replace(mark.group(0), "") if mark else pr.group(1)
        st = re.search(r'<w:pStyle w:val="([^"]*)"', inner)
        sid = st.group(1) if st else default_p
        label = names.get(sid, sid).lower()
        if label.startswith(("heading", "title", "subtitle", "toc")):
            continue
        props = [x.group(0) for x in re.finditer(tag_re(DP_TAGS), inner)]
        if not props and label != "caption":
            continue
        base = f"@caption:{sid}" if label == "caption" else sid
        new = registry.setdefault((base, tuple(props)), f"DP{len(registry) + 1}")
        rest = re.sub(r'<w:pStyle w:val="[^"]*"\s*/>', "", re.sub(tag_re(DP_TAGS), "", inner))
        newp = p.replace(pr.group(0), f'<w:pPr><w:pStyle w:val="{new}"/>{rest}{mark.group(0) if mark else ""}</w:pPr>', 1)
        doc = doc[:a] + newp + doc[b:]
    defs = []
    for (base, props), sid in registry.items():
        ppr, rpr, parent = "", "", base
        if base.startswith("@caption:"):
            parent = default_p
            src = re.search(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % re.escape(base.split(":", 1)[1]), styles, re.S).group()
            ppr = (re.search(r"<w:pPr>(.*?)</w:pPr>", src, re.S) or [None, ""])[1]
            rpr = (re.search(r"<w:rPr>(.*?)</w:rPr>", src, re.S) or [None, ""])[1]
            for tag in re.findall(r"<w:(\w+)\b", "".join(props)):
                ppr = re.sub(tag_re((tag,)), "", ppr)
        defs.append(f'<w:style w:type="paragraph" w:customStyle="1" w:styleId="{sid}"><w:name w:val="{sid}"/><w:basedOn w:val="{parent}"/><w:qFormat/>'
                    f'<w:pPr>{ppr}{"".join(props)}</w:pPr>{f"<w:rPr>{rpr}</w:rPr>" if rpr else ""}</w:style>')
    return doc, defs


SHAPE_RE = r"<mc:AlternateContent\b[^>]*>(?:(?!<w:txbxContent).)*?</mc:AlternateContent>"


def keep_shapes(doc, out):
    """Floating shapes without text (lines, boxes) leave as raw XML in shapes/N.xml; postprocess.py puts them back.
    A shape holding a text box stays unhandled, because its text would be hidden from editing."""
    shapes = []

    def mark(m):
        shapes.append(m.group())
        return f"<w:t>SHPMK{len(shapes)}SHPMK</w:t>"

    doc = re.sub(SHAPE_RE, mark, doc, flags=re.S)
    if shapes:
        (out / "shapes").mkdir(exist_ok=True)
        for n, x in enumerate(shapes, 1):
            (out / "shapes" / f"{n}.xml").write_text(x, encoding="utf-8")
    return doc


def reading_copy(src, out):
    z = zipfile.ZipFile(src)
    doc = z.read("word/document.xml").decode("utf-8")
    styles = z.read("word/styles.xml").decode("utf-8")
    names, default_p, default_c = style_maps(styles)
    toc = toc_block(doc)
    doc = re.sub(r'<w:br\b[^>]*w:type="page"[^>]*/>', '<w:t xml:space="preserve"> PAGEBREAKMARK </w:t>', doc)
    doc = re.sub(r"<w:tab\s*/>", '<w:t xml:space="preserve"> TABMARK </w:t>', doc)
    doc = keep_shapes(doc, out)
    # Markdown folds a run of spaces into one, and Pandoc moves a space-only run out of its span; carry the count as SPMKnSPMK and reverse.lua writes it back as a raw run
    doc = re.sub(r"(<w:t(?: [^>]*)?>)([^<]*)(</w:t>)", lambda m: m.group(1) + re.sub(r" {2,}|^ +$", lambda s: f"SPMK{len(s.group())}SPMK", m.group(2)) + m.group(3), doc)
    doc = re.sub(r'<w:fldSimple\b[^>]*w:instr="[^"]*SEQ[^"]*"[^>]*>(.*?)</w:fldSimple>', r"\1", doc, flags=re.S)
    doc, run_defs = direct_run_styles(doc, default_c)
    doc, empties = empty_paragraphs(doc)
    doc, para_defs = direct_paragraph_styles(doc, names, default_p, styles)
    extra = "".join(run_defs + para_defs)
    with zipfile.ZipFile(out / "source.docx", "w", zipfile.ZIP_DEFLATED) as zout:
        for item in z.infolist():
            data = z.read(item.filename)
            if item.filename == "word/document.xml":
                data = doc.encode("utf-8")
            elif item.filename == "word/styles.xml":
                data = styles.replace("</w:styles>", extra + "</w:styles>").encode("utf-8")
            zout.writestr(item, data)
    (out / "extra-styles.xml").write_text(extra, encoding="utf-8")
    (out / "empty-paragraphs.txt").write_text("".join(e + "\n" for e in empties), encoding="utf-8")
    return toc, len(run_defs), len(para_defs), len(empties)


def table_styles(doc):
    out = []
    for m in re.finditer(r"<w:tbl>.*?</w:tbl>", doc, re.S):
        s = re.search(r'<w:tblStyle w:val="([^"]*)"', m.group(0))
        out.append(s.group(1) if s else "")
    return out


def table_props(doc):
    out = []
    for t in re.finditer(r"<w:tbl>.*?</w:tbl>", doc, re.S):
        pr = re.search(r"<w:tblPr>(.*?)</w:tblPr>", t.group(0), re.S)
        extra = pr.group(1) if pr else ""
        rows = []
        for r in re.finditer(r"<w:tr\b.*?</w:tr>", t.group(0), re.S):
            trpr = re.search(r"<w:trPr>(.*?)</w:trPr>", r.group(0), re.S)
            cells = []
            for c in re.finditer(r"<w:tc>.*?</w:tc>", r.group(0), re.S):
                tcpr = re.search(r"<w:tcPr>(.*?)</w:tcPr>", c.group(0), re.S)
                cells.append("".join(m.group(0) for m in re.finditer(tag_re(CELL_TAGS), tcpr.group(1))) if tcpr else "")
            rows.append({"trPr": trpr.group(1) if trpr else "", "cells": cells})
        out.append({"extra": extra, "rows": rows})
    return out


def cell_alignment(doc):
    lines = []
    for t in re.finditer(r"<w:tbl>.*?</w:tbl>", doc, re.S):
        for row in re.finditer(r"<w:tr\b.*?</w:tr>", t.group(0), re.S):
            vals = []
            for cell in re.finditer(r"<w:tc>.*?</w:tc>", row.group(0), re.S):
                j = re.search(r'<w:jc w:val="([^"]*)"', cell.group(0))
                vals.append(j.group(1) if j else "-")
            empty = not re.search(r"<w:t(?: [^>]*)?>[^<]*\S|<w:drawing", row.group(0))
            lines.append(("E " if empty else "R ") + " ".join(vals))
        lines.append("---")
    return lines


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], pathlib.Path(sys.argv[2])
    tables = inventory.summarise(src)["tables"]
    (out / "table-widths.txt").write_text("".join(" ".join(map(str, t)) + "\n" for t in tables), encoding="utf-8")
    (out / "table-styles.txt").write_text("".join(s + "\n" for s in table_styles(zipfile.ZipFile(src).read("word/document.xml").decode("utf-8"))), encoding="utf-8")
    (out / "table-props.json").write_text(json.dumps(table_props(zipfile.ZipFile(src).read("word/document.xml").decode("utf-8")), ensure_ascii=False), encoding="utf-8")
    (out / "table-cells.txt").write_text("".join(l + "\n" for l in cell_alignment(zipfile.ZipFile(src).read("word/document.xml").decode("utf-8"))), encoding="utf-8")
    toc, runs, paras, empties = reading_copy(src, out)
    if toc:
        (out / "toc.xml").write_text(toc, encoding="utf-8")
    print(f"tables: {len(tables)}, table of contents: {'yes' if toc else 'no'}, run styles: {runs}, paragraph styles: {paras}, empty paragraphs kept: {empties}")


if __name__ == "__main__":
    main()
