#!/usr/bin/env python3
"""Usage: make_fixture.py out.docx [--textbox] [--shape] [--wps-textbox] [--missing-font]
"""
import re, subprocess, sys, zipfile

NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
TEXTBOX = '<w:p><w:r><w:pict><v:shape xmlns:v="urn:schemas-microsoft-com:vml"><v:textbox><w:txbxContent><w:p><w:r><w:t>boxed</w:t></w:r></w:p></w:txbxContent></v:textbox></v:shape></w:pict></w:r></w:p>'

SHAPE = ('<w:p><w:r><mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:Choice Requires="wps">'
         '<w:drawing><wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" simplePos="0" relativeHeight="1" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1" distT="0" distB="0" distL="0" distR="0">'
         '<wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="column"><wp:posOffset>0</wp:posOffset></wp:positionH><wp:positionV relativeFrom="paragraph"><wp:posOffset>0</wp:posOffset></wp:positionV>'
         '<wp:extent cx="900000" cy="0"/><wp:wrapNone/><wp:docPr id="1" name="line"/></wp:anchor></w:drawing></mc:Choice>'
         '<mc:Fallback><w:pict><v:line xmlns:v="urn:schemas-microsoft-com:vml" from="0,0" to="70pt,0"/></w:pict></mc:Fallback></mc:AlternateContent></w:r></w:p>')

# a Word text box: the same paragraphs in the wps Choice and the VML Fallback, one with a tab and a pPr textDirection
BOXPARAS = ('<w:p><w:pPr><w:textDirection w:val="btLr"/></w:pPr><w:r><w:t>Label one:</w:t></w:r><w:r><w:tab/><w:t>____</w:t></w:r></w:p>'
            '<w:p><w:r><w:t>boxed one</w:t></w:r></w:p>')
WPS_BOX = ('<w:p><w:r><mc:AlternateContent xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006"><mc:Choice Requires="wps">'
           '<w:drawing><wp:anchor xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" simplePos="0" relativeHeight="2" behindDoc="0" locked="0" layoutInCell="1" allowOverlap="1" distT="0" distB="0" distL="0" distR="0">'
           '<wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="column"><wp:posOffset>0</wp:posOffset></wp:positionH><wp:positionV relativeFrom="paragraph"><wp:posOffset>0</wp:posOffset></wp:positionV>'
           '<wp:extent cx="3000000" cy="1500000"/><wp:wrapTopAndBottom/><wp:docPr id="7" name="box"/>'
           '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.microsoft.com/office/word/2010/wordprocessingShape">'
           '<wps:wsp xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape"><wps:cNvSpPr txBox="1"/><wps:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="3000000" cy="1500000"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></wps:spPr>'
           f'<wps:txbx><w:txbxContent>{BOXPARAS}</w:txbxContent></wps:txbx><wps:bodyPr/></wps:wsp></a:graphicData></a:graphic></wp:anchor></w:drawing></mc:Choice>'
           '<mc:Fallback><w:pict><v:rect xmlns:v="urn:schemas-microsoft-com:vml" style="width:236pt;height:118pt"><v:textbox>'
           f'<w:txbxContent>{BOXPARAS}</w:txbxContent></v:textbox></v:rect></w:pict></mc:Fallback></mc:AlternateContent></w:r></w:p>')


def body(missing, textbox, shape=False, wps=False):
    font = "Zzz Missing Font" if missing else "Arial"
    cell = lambda t, extra="", jc="": f'<w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/>{extra}</w:tcPr><w:p><w:pPr>{jc}</w:pPr><w:r><w:t>{t}</w:t></w:r></w:p></w:tc>'
    return f"""<w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Chapter one</w:t></w:r></w:p>
<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="240" w:after="60" w:line="360" w:lineRule="auto"/></w:pPr><w:r><w:t xml:space="preserve">A centred paragraph </w:t></w:r><w:r><w:tab/></w:r><w:r><w:rPr><w:rFonts w:ascii="{font}" w:hAnsi="{font}"/><w:color w:val="FF0000"/><w:sz w:val="28"/><w:spacing w:val="20"/></w:rPr><w:t>red text</w:t></w:r></w:p>
<w:p/>
<w:p><w:r><w:rPr><w:b/><w:sz w:val="40"/></w:rPr><w:t xml:space="preserve"> </w:t></w:r></w:p>
<w:p><w:r><w:t>A plain paragraph with  two spaces and the default style.</w:t></w:r></w:p>
{TEXTBOX if textbox else ""}{SHAPE if shape else ""}{WPS_BOX if wps else ""}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Chapter two</w:t></w:r></w:p>
<w:tbl><w:tblPr><w:tblStyle w:val="Table"/><w:tblW w:w="9000" w:type="dxa"/><w:tblInd w:w="100" w:type="dxa"/><w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="0000FF"/></w:tblBorders><w:tblLayout w:type="fixed"/><w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>
<w:tblGrid><w:gridCol w:w="3000"/><w:gridCol w:w="3000"/><w:gridCol w:w="3000"/></w:tblGrid>
<w:tr><w:trPr><w:trHeight w:val="500"/></w:trPr>{cell("A", '<w:shd w:val="clear" w:color="auto" w:fill="AAFFAA"/>', '<w:jc w:val="center"/>')}{cell("B", '<w:tcBorders><w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/></w:tcBorders>')}{cell("C")}</w:tr>
<w:tr>{cell("1")}{cell("2")}{cell("3")}</w:tr>
<w:tr><w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p/></w:tc><w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p/></w:tc><w:tc><w:tcPr><w:tcW w:w="3000" w:type="dxa"/></w:tcPr><w:p/></w:tc></w:tr></w:tbl>
<w:p><w:pPr><w:pStyle w:val="Caption"/></w:pPr><w:r><w:t xml:space="preserve">Table </w:t></w:r><w:fldSimple w:instr=" SEQ Table \\* ARABIC "><w:r><w:t>1</w:t></w:r></w:fldSimple><w:r><w:t>: Fixture table</w:t></w:r></w:p>
<w:sectPr><w:headerReference w:type="default" r:id="rIdHdr1"/><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1000" w:right="900" w:bottom="1000" w:left="900" w:header="500" w:footer="500" w:gutter="0"/></w:sectPr></w:body>"""


def main():
    out = sys.argv[1]
    base = zipfile.ZipFile(__import__("io").BytesIO(subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"], capture_output=True, check=True).stdout))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for item in base.infolist():
            data = base.read(item.filename)
            if item.filename == "word/document.xml":
                data = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:background w:color="112233"/>{body("--missing-font" in sys.argv, "--textbox" in sys.argv, "--shape" in sys.argv, "--wps-textbox" in sys.argv)}</w:document>'.encode()
            elif item.filename == "word/styles.xml":
                s = data.decode()
                for sid in ("Compact", "TableCaption", "FirstParagraph"):
                    s = re.sub(r'<w:style [^>]*w:styleId="%s".*?</w:style>' % sid, "", s, flags=re.S)
                data = s.encode()
            elif item.filename == "word/_rels/document.xml.rels":
                data = data.decode().replace("</Relationships>", '<Relationship Id="rIdHdr1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/header" Target="header1.xml"/></Relationships>').encode()
            elif item.filename == "[Content_Types].xml":
                data = data.decode().replace("</Types>", '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/></Types>').encode()
            z.writestr(item, data)
        z.writestr("word/header1.xml", f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {NS}><w:p><w:r><w:t>Fixture header</w:t></w:r></w:p></w:hdr>')


if __name__ == "__main__":
    main()
