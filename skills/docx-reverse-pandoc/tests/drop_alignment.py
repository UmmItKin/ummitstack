#!/usr/bin/env python3
"""Usage: drop_alignment.py in.docx out.docx
"""
import sys, zipfile

src = zipfile.ZipFile(sys.argv[1])
with zipfile.ZipFile(sys.argv[2], "w") as out:
    for item in src.infolist():
        data = src.read(item.filename)
        if item.filename == "word/document.xml":
            data = data.replace(b'<w:jc w:val="center"/>', b"", 1)
        out.writestr(item, data)
