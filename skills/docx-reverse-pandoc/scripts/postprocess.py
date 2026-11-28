#!/usr/bin/env python3
"""Usage: postprocess.py reference.docx rebuilt.docx [table-widths.txt]
"""
import difflib, html, json, os, re, sys, zipfile


def background(ref):
    m = re.search(r"<w:background\b[^>]*?(/>|>.*?</w:background>)", zipfile.ZipFile(ref).read("word/document.xml").decode("utf-8"), re.S)
    return m.group() if m else None


def fit_table(tbl, widths):
    total = sum(widths)
    grid = "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{w}"/>' for w in widths) + "</w:tblGrid>"
    tbl = re.sub(r"<w:tblGrid>.*?</w:tblGrid>", grid, tbl, count=1, flags=re.S)

    def row(m):
        col = 0

        def cell(c):
            nonlocal col
            span = re.search(r'<w:gridSpan w:val="(\d+)"', c.group())
            span = int(span.group(1)) if span else 1
            w = sum(widths[col:col + span])
            col += span
            tcw = f'<w:tcW w:w="{w}" w:type="dxa"/>'
            body = c.group()
            body = re.sub(r"^<w:tc>\s*<w:tcPr\s*/>", "<w:tc>", body, count=1)
            if re.match(r"<w:tc>\s*<w:tcPr>", body):
                return re.sub(r"<w:tcPr>", "<w:tcPr>" + tcw, body, count=1)
            return re.sub(r"^<w:tc>", "<w:tc><w:tcPr>" + tcw + "</w:tcPr>", body, count=1)

        return re.sub(r"<w:tc>.*?</w:tc>", cell, m.group(), flags=re.S)

    return re.sub(r"<w:tr\b.*?</w:tr>", row, tbl, flags=re.S)


def set_jc(p, val):
    p = re.sub(r"<w:jc\b[^>]*/>", "", p)
    if val == "-":
        return p
    jc = f'<w:jc w:val="{val}"/>'
    if re.search(r"<w:pPr\s*/>", p):
        return re.sub(r"<w:pPr\s*/>", f"<w:pPr>{jc}</w:pPr>", p, count=1)
    if "<w:pPr>" in p:
        return re.sub(r"(<w:rPr>|</w:pPr>)", lambda m: jc + m.group(1), p, count=1) if "<w:rPr>" in p.split("</w:pPr>")[0] else p.replace("</w:pPr>", jc + "</w:pPr>", 1)
    return re.sub(r"^(<w:p(?: [^>]*)?>)", lambda m: m.group(1) + f"<w:pPr>{jc}</w:pPr>", p, count=1)


def blank_row(row):
    row = re.sub(r"<w:trPr>.*?</w:trPr>", "", row, flags=re.S)
    return re.sub(r"<w:r(?: [^>]*)?>.*?</w:r>", "", row, flags=re.S)


def restore_rows(tbl, rows):
    trs = list(re.finditer(r"<w:tr\b.*?</w:tr>", tbl, re.S))
    real = [r for r in rows if r[0] == "R"]
    if len(trs) == len(rows) or len(trs) != len(real) or not trs:
        return tbl
    out, k, last = [], 0, trs[0].group()
    for flag, _ in rows:
        if flag == "R":
            last = trs[k].group()
            out.append(last)
            k += 1
        else:
            out.append(blank_row(last))
    return tbl[:trs[0].start()] + "".join(out) + tbl[trs[-1].end():]


def align_table(tbl, rows):
    rows = [vals for _, vals in rows]
    trs = list(re.finditer(r"<w:tr\b.*?</w:tr>", tbl, re.S))
    if len(trs) != len(rows) or any(len(re.findall(r"<w:tc>", t.group())) != len(r) for t, r in zip(trs, rows)):
        return tbl
    it = iter(rows)

    def row(m):
        vals = iter(next(it))
        return re.sub(r"<w:tc>.*?</w:tc>", lambda c: re.sub(r"<w:p(?= |>).*?</w:p>", lambda p, v=next(vals): set_jc(p.group(), v), c.group(), flags=re.S), m.group(), flags=re.S)

    return re.sub(r"<w:tr\b.*?</w:tr>", row, tbl, flags=re.S)


def apply_props(tbl, props):
    trs = list(re.finditer(r"<w:tr\b.*?</w:tr>", tbl, re.S))
    rows = props["rows"]
    if len(trs) != len(rows) or any(len(re.findall(r"<w:tc>", t.group())) != len(r["cells"]) for t, r in zip(trs, rows)):
        return tbl
    tbl = re.sub(r"<w:tblPr>.*?</w:tblPr>", lambda _: f"<w:tblPr>{props['extra']}</w:tblPr>", tbl, count=1, flags=re.S)
    it = iter(rows)

    def row(m):
        info = next(it)
        r = re.sub(r"<w:trPr>.*?</w:trPr>", "", m.group(), count=1, flags=re.S)
        if info["trPr"]:
            r = re.sub(r"^(<w:tr(?: [^>]*)?>)", lambda x: x.group(1) + f"<w:trPr>{info['trPr']}</w:trPr>", r, count=1)
        cells = iter(info["cells"])

        def cell(c):
            # Pandoc writes an empty <w:tcPr />; open it, or the borders and fills have nowhere to go
            body = re.sub(r"^<w:tc>\s*<w:tcPr\s*/>", "<w:tc><w:tcPr></w:tcPr>", c.group(), count=1)
            if not re.match(r"<w:tc>\s*<w:tcPr>", body):
                body = body.replace("<w:tc>", "<w:tc><w:tcPr></w:tcPr>", 1)
            return re.sub(r"</w:tcPr>", lambda _, e=next(cells): e + "</w:tcPr>", body, count=1)

        return re.sub(r"<w:tc>.*?</w:tc>", cell, r, flags=re.S)

    return re.sub(r"<w:tr\b.*?</w:tr>", row, tbl, flags=re.S)


def read_cells(path):
    tables, rows = [], []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line == "---":
            tables.append(rows)
            rows = []
        elif line:
            tokens = line.split()
            rows.append((tokens[0], tokens[1:]))
    return tables


PPR_AFTER_NUMPR = ("suppressLineNumbers|pBdr|shd|tabs|suppressAutoHyphens|kinsoku|wordWrap|overflowPunct|topLinePunct|autoSpaceDE|"
                   "autoSpaceDN|bidi|adjustRightInd|snapToGrid|spacing|ind|contextualSpacing|mirrorIndents|suppressOverlap|jc|"
                   "textDirection|textAlignment|textboxTightWrap|outlineLvl|divId|cnfStyle|rPr|sectPr")


def para_list(xml):
    out = []
    for m in re.finditer(r"<w:p(?: [^>]*)?>.*?</w:p>", xml, re.S):
        # a shape marker counts as its SHPMKnSHPMK text in original-flat.xml, so a paragraph holding only a shape still gets its format
        text = "".join(t or f"SHPMK{n}SHPMK" for t, n in re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>|<!--SHAPE (\d+)-->", m.group()))
        text = re.sub(r"\s+", " ", html.unescape(text)).strip()
        if text:
            out.append((text, m))
    return out


def own_ppr(p):
    m = re.search(r"<w:pPr>(.*?)</w:pPr>", p, re.S)
    return m.group(1) if m else ""


def transfer_paragraph_formats(original_xml, rebuilt_xml):
    a, b = para_list(original_xml), para_list(rebuilt_xml)
    edits = []
    for blk in difflib.SequenceMatcher(None, [x[0] for x in a], [x[0] for x in b], autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            src, dst = a[blk.a + k][1].group(), b[blk.b + k][1]
            inner = re.sub(r"<w:numPr>.*?</w:numPr>|<w:sectPr\b.*?</w:sectPr>", "", own_ppr(src), flags=re.S)
            num = re.search(r"<w:numPr>.*?</w:numPr>", own_ppr(dst.group()), re.S)
            if num:
                at = re.search(r"<w:(?:%s)\b" % PPR_AFTER_NUMPR, inner)
                inner = inner[:at.start()] + num.group() + inner[at.start():] if at else inner + num.group()
            edits.append((dst.start(), dst.end(), dst.group(), inner))
    for start, end, p, inner in reversed(edits):
        if re.search(r"<w:pPr>.*?</w:pPr>|<w:pPr\s*/>", p, re.S):
            new = re.sub(r"<w:pPr>.*?</w:pPr>|<w:pPr\s*/>", lambda _: f"<w:pPr>{inner}</w:pPr>", p, count=1, flags=re.S)
        else:
            new = re.sub(r"^(<w:p(?: [^>]*)?>)", lambda m: m.group(1) + f"<w:pPr>{inner}</w:pPr>", p, count=1)
        rebuilt_xml = rebuilt_xml[:start] + new + rebuilt_xml[end:]
    return rebuilt_xml


# the marker paragraphs come back indented and with a pPr from the format transfer, so match any paragraph holding the marker
TXBX_BLOCK = r"<w:p\b(?:(?!</w:p>).)*?TXBXBEGIN(\d+)END(?:(?!</w:p>).)*</w:p>(.*?)<w:p\b(?:(?!</w:p>).)*?TXBXEND\1END(?:(?!</w:p>).)*</w:p>"


def restore_shapes(s, original, folder):
    """Put back the raw floating shapes kept by extract_parts.py, with the namespaces they need, and move each text box's paragraphs
    from between its marker paragraphs back into every txbxContent copy of the shape."""
    boxes = {}

    def cut(m):
        boxes[m.group(1)] = m.group(2).strip() if "<w:p" in m.group(2) else "<w:p/>"
        return ""

    s = re.sub(TXBX_BLOCK, cut, s, flags=re.S)
    marks = re.findall(r"<w:r><!--SHAPE (\d+)--></w:r>", s)
    if not marks:
        return s

    def shape(m):
        x = open(os.path.join(folder, "shapes", m.group(1) + ".xml"), encoding="utf-8").read()
        x = re.sub(r'(<wp:docPr\b[^>]*?\bid=")\d+', lambda d: d.group(1) + str(90000 + int(m.group(1)) * 10), x)
        x = re.sub(r'(<v:shape\b[^>]*?\bo:spid=")[^"]*', lambda d: d.group(1) + "_x0000_s" + str(9000 + int(m.group(1))), x)
        if m.group(1) in boxes:
            # each copy (Choice, Fallback) gets its own picture ids, or Word reports unreadable content
            parts = x.split("<!--TXBX-->")
            x = parts[0] + "".join(re.sub(r'(<wp:docPr\b[^>]*?\bid=")(\d+)', lambda d, k=k: d.group(1) + str(int(d.group(2)) + 100000 * k), boxes[m.group(1)]) + p
                                   for k, p in enumerate(parts[1:]))
        return "<w:r>" + x + "</w:r>"

    s = re.sub(r"<w:r><!--SHAPE (\d+)--></w:r>", shape, s)
    root = re.search(r"<w:document\b[^>]*>", s).group()
    have = dict(re.findall(r'xmlns:(\w+)="([^"]*)"', root))
    orig = re.search(r"<w:document\b[^>]*>", original).group()
    add = "".join(f' xmlns:{k}="{v}"' for k, v in re.findall(r'xmlns:(\w+)="([^"]*)"', orig) if k not in have)
    ign = re.search(r'mc:Ignorable="[^"]*"', orig)
    if ign and "mc:Ignorable" not in root:
        add += " " + ign.group()
    return s.replace(root, root[:-1] + add + ">", 1)


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    ref, out = sys.argv[1:3]
    widths = []
    if len(sys.argv) == 4 and os.path.exists(sys.argv[3]):
        widths = [[int(n) for n in line.split()] for line in open(sys.argv[3], encoding="utf-8") if line.strip()]
    cells_path = os.path.join(os.path.dirname(os.path.abspath(out)), "table-cells.txt")
    cells = read_cells(cells_path) if os.path.exists(cells_path) else []
    props_path = os.path.join(os.path.dirname(os.path.abspath(out)), "table-props.json")
    props = json.load(open(props_path, encoding="utf-8")) if os.path.exists(props_path) else []
    bg = background(ref)
    tmp = out + ".tmp"
    with zipfile.ZipFile(out) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                s = data.decode("utf-8")
                if bg and "<w:background" not in s:
                    s = re.sub(r"<w:body\b", lambda m: bg + m.group(), s, count=1)
                s = re.sub(r"<w:tc>.*?</w:tc>", lambda c: re.sub(r'<w:pStyle w:val="Compact"\s*/>', "", c.group()), s, flags=re.S)
                if cells and len(cells) == len(re.findall(r"<w:tbl>", s)):
                    ci = iter(cells)
                    s = re.sub(r"<w:tbl>.*?</w:tbl>", lambda m: (lambda rows: align_table(restore_rows(m.group(), rows), rows))(next(ci)), s, flags=re.S)
                if props and len(props) == len(re.findall(r"<w:tbl>", s)):
                    pi = iter(props)
                    s = re.sub(r"<w:tbl>.*?</w:tbl>", lambda m: apply_props(m.group(), next(pi)), s, flags=re.S)
                tables = re.findall(r"<w:tbl>.*?</w:tbl>", s, flags=re.S)
                if widths and len(tables) == len(widths):
                    it = iter(widths)
                    s = re.sub(r"<w:tbl>.*?</w:tbl>", lambda m: fit_table(m.group(), next(it)), s, flags=re.S)
                elif widths:
                    print(f"postprocess.py: {len(tables)} tables but {len(widths)} widths listed; table widths not applied", file=sys.stderr)
                original = zipfile.ZipFile(ref).read("word/document.xml").decode("utf-8")
                flat = os.path.join(os.path.dirname(os.path.abspath(out)), "original-flat.xml")
                s = transfer_paragraph_formats(open(flat, encoding="utf-8").read() if os.path.exists(flat) else original, s)
                s = restore_shapes(s, original, os.path.dirname(os.path.abspath(out)))
                data = s.encode("utf-8")
            zout.writestr(item, data)
    os.replace(tmp, out)


if __name__ == "__main__":
    main()
