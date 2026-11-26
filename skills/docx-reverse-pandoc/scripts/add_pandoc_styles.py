#!/usr/bin/env python3
"""Usage: add_pandoc_styles.py reference.docx [extra-styles.xml]
"""
import io, os, re, subprocess, sys, zipfile


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    path = sys.argv[1]
    default = subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout
    dstyles = zipfile.ZipFile(io.BytesIO(default)).read("word/styles.xml").decode("utf-8")
    with zipfile.ZipFile(path) as z:
        entries = [(i, z.read(i.filename)) for i in z.infolist()]
    orig = next(d for i, d in entries if i.filename == "word/styles.xml").decode("utf-8")
    have = set(re.findall(r'<w:style [^>]*w:styleId="([^"]+)"', orig))
    add = "".join(m.group(0) for m in re.finditer(r'<w:style [^>]*w:styleId="([^"]+)".*?</w:style>', dstyles, re.S) if m.group(1) not in have)
    if len(sys.argv) == 3 and os.path.exists(sys.argv[2]):
        add += open(sys.argv[2], encoding="utf-8").read()
    if not add:
        return
    new = orig.replace("</w:styles>", add + "</w:styles>")
    tmp = path + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for i, d in entries:
            out.writestr(i, new.encode("utf-8") if i.filename == "word/styles.xml" else d)
    os.replace(tmp, path)
    print(f"added {add.count('<w:style ')} styles")


if __name__ == "__main__":
    main()
