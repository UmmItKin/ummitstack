#!/usr/bin/env python3
"""Usage: fidelity.py original.docx rebuilt.docx [--json out.json]
Exit 1 when any difference is found.
"""
import difflib, json, re, sys, zipfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
LEFT, RIGHT = {"start": "left", "left": "left"}, {"end": "right", "right": "right"}


def theme_fonts(z):
    t = z.read("word/theme/theme1.xml").decode("utf-8", "replace") if "word/theme/theme1.xml" in z.namelist() else ""
    pick = lambda k: (re.search(rf'<a:{k}Font>\s*<a:latin typeface="([^"]*)"', t) or [None, None])[1]
    return {"major": pick("major"), "minor": pick("minor")}


def read_ppr(el):
    out = {}
    if el is None:
        return out
    jc = el.find(W + "jc")
    if jc is not None:
        v = jc.get(W + "val")
        out["jc"] = LEFT.get(v) or RIGHT.get(v) or v
    sp = el.find(W + "spacing")
    if sp is not None:
        for k in ("before", "after", "line", "lineRule"):
            if sp.get(W + k) is not None:
                out[k] = sp.get(W + k)
    ind = el.find(W + "ind")
    if ind is not None:
        for k, names in (("left", ("left", "start")), ("right", ("right", "end")), ("firstLine", ("firstLine",)), ("hanging", ("hanging",))):
            for n in names:
                if ind.get(W + n) is not None:
                    out[k] = ind.get(W + n)
    return out


def read_rpr(el, themes):
    out = {}
    if el is None:
        return out
    for tag, key in (("sz", "sz"), ("highlight", "highlight"), ("spacing", "charspacing")):
        e = el.find(W + tag)
        if e is not None:
            out[key] = e.get(W + "val")
    c = el.find(W + "color")
    if c is not None:
        out["color"] = (c.get(W + "val") or "").lower()
    f = el.find(W + "rFonts")
    if f is not None:
        theme = f.get(W + "asciiTheme") or f.get(W + "hAnsiTheme")
        name = f.get(W + "ascii") or f.get(W + "hAnsi")
        if theme:
            name = themes.get("major" if theme.startswith("major") else "minor")
        if name:
            out["font"] = name.lower()
    for tag in ("b", "i", "caps", "smallCaps"):
        e = el.find(W + tag)
        if e is not None:
            out[tag] = e.get(W + "val") not in ("0", "false")
    sh = el.find(W + "shd")
    if sh is not None and sh.get(W + "fill") not in (None, "auto"):
        out["shade"] = sh.get(W + "fill").lower()
    return out


class Styles:
    def __init__(self, z):
        themes = theme_fonts(z)
        root = ET.fromstring(z.read("word/styles.xml"))
        dd = root.find(W + "docDefaults")
        self.pdef = read_ppr(dd.find(f"{W}pPrDefault/{W}pPr")) if dd is not None else {}
        self.rdef = read_rpr(dd.find(f"{W}rPrDefault/{W}rPr"), themes) if dd is not None else {}
        self.s, self.default_p, self.themes = {}, None, themes
        for s in root.findall(W + "style"):
            b = s.find(W + "basedOn")
            self.s[s.get(W + "styleId")] = {"based": b.get(W + "val") if b is not None else None,
                                            "p": read_ppr(s.find(W + "pPr")), "r": read_rpr(s.find(W + "rPr"), themes)}
            if s.get(W + "type") == "paragraph" and s.get(W + "default") in ("1", "true"):
                self.default_p = s.get(W + "styleId")

    def chain(self, sid, key):
        out, seen, order = {}, set(), []
        while sid and sid in self.s and sid not in seen:
            seen.add(sid)
            order.append(self.s[sid][key])
            sid = self.s[sid]["based"]
        for d in reversed(order):
            out.update(d)
        return out


def paragraphs(path):
    z = zipfile.ZipFile(path)
    st = Styles(z)
    root = ET.fromstring(z.read("word/document.xml"))
    out = []
    for p in root.iter(W + "p"):
        text = re.sub(r"\s+", " ", "".join(t.text or "" for t in p.iter(W + "t"))).strip()
        if not text:
            continue
        ppr = p.find(W + "pPr")
        ps = ppr.find(W + "pStyle") if ppr is not None else None
        sid = ps.get(W + "val") if ps is not None else st.default_p
        pe = dict(st.pdef)
        pe.update(st.chain(sid, "p"))
        pe.update(read_ppr(ppr))
        weight = Counter()
        base = dict(st.rdef)
        base.update(st.chain(sid, "r"))
        for r in p.iter(W + "r"):
            t = "".join(x.text or "" for x in r.findall(W + "t"))
            if not t.strip():
                continue
            rpr = r.find(W + "rPr")
            rs = rpr.find(W + "rStyle") if rpr is not None else None
            re_ = dict(base)
            if rs is not None:
                re_.update(st.chain(rs.get(W + "val"), "r"))
            re_.update(read_rpr(rpr, st.themes))
            weight[tuple(sorted(re_.items()))] += len(t)
        run = dict(weight.most_common(1)[0][0]) if weight else {}
        out.append((text, pe, run))
    return out


def compare(a, b):
    ta, tb = [x[0] for x in a], [x[0] for x in b]
    groups = defaultdict(list)
    matched = 0
    for blk in difflib.SequenceMatcher(None, ta, tb, autojunk=False).get_matching_blocks():
        for k in range(blk.size):
            (text, pa, ra), (_, pb, rb) = a[blk.a + k], b[blk.b + k]
            matched += 1
            for kind, x, y in (("paragraph", pa, pb), ("text", ra, rb)):
                for key in sorted(set(x) | set(y)):
                    keep = {"before": "0", "after": "0", "left": "0", "right": "0", "firstLine": "0", "hanging": "0", "line": "240", "lineRule": "auto", "jc": "left"}
                    va, vb = x.get(key, keep.get(key)), y.get(key, keep.get(key))
                    if key in ("b", "i", "caps", "smallCaps"):
                        va, vb = bool(x.get(key)), bool(y.get(key))
                    if va != vb:
                        groups[(kind, key, str(va), str(vb))].append(text[:48])
    return matched, len(ta), len(tb), groups


def main():
    args = sys.argv[1:]
    out = None
    if "--json" in args:
        k = args.index("--json")
        out = args[k + 1]
        args = args[:k] + args[k + 2:]
    if len(args) != 2:
        sys.exit(__doc__)
    a, b = paragraphs(args[0]), paragraphs(args[1])
    matched, na, nb, groups = compare(a, b)
    rows = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    for (kind, key, va, vb), texts in rows[:14]:
        print(f'FAIL {kind} {key}: original {va}, rebuilt {vb} in {len(texts)} paragraph(s), e.g. "{texts[0]}"')
    if len(rows) > 14:
        print(f"... {len(rows) - 14} more kinds of difference")
    total = sum(len(t) for t in groups.values())
    print(f"matched {matched} of {na} original and {nb} rebuilt paragraphs with text; {total} property differences in {len(rows)} kinds")
    if out:
        json.dump({"matched": matched, "original": na, "rebuilt": nb, "differences": total, "kinds": [
            {"kind": k, "property": p, "original": va, "rebuilt": vb, "paragraphs": len(t), "sample": t[0]} for (k, p, va, vb), t in rows]},
            open(out, "w", encoding="utf-8"), indent=1)
    sys.exit(1 if groups else 0)


if __name__ == "__main__":
    main()
