#!/usr/bin/env python3
"""Usage: check_xml.py file.docx
Exits 1 when any XML part does not parse, or a table cell has more than one tcPr (both were real mistakes)."""
import re, sys, xml.dom.minidom as minidom, zipfile

z = zipfile.ZipFile(sys.argv[1])
for name in z.namelist():
    if name.endswith((".xml", ".rels")):
        minidom.parseString(z.read(name))
doc = z.read("word/document.xml").decode()
for cell in re.findall(r"<w:tc>.*?</w:tc>", doc, re.S):
    if len(re.findall(r"<w:tcPr[ >/]", cell)) > 1:
        sys.exit("a table cell has two tcPr")
