#!/usr/bin/env python3
"""Usage: make_fixture.py out.pdf [--font NAME] [--scan] [--curve]
Builds a small fictional A4 PDF with Typst: a title, bold and italic words, two sizes, a table and a second page.
--font picks the font (default: the system serif). --scan makes a PDF whose pages are pictures with no text layer. --curve adds a circle, which this workflow cannot redraw."""
import os, shutil, subprocess, sys, tempfile

BODY = """#set page(paper: "a4", margin: (x: 56pt, y: 60pt))
#set text(font: "{font}", size: 11pt)
#set par(justify: false, leading: 7pt)
#align(center)[#text(size: 20pt, weight: "bold")[Sample Document]]
#v(8pt)
Left label #h(120pt) Right label
#v(10pt)
This paragraph has *bold words* and _italic words_ in the middle of the sentence, and it is long enough to wrap onto a second line of the page.
#v(6pt)
#text(size: 14pt, weight: "bold")[Part One]
#v(4pt)
#table(columns: (30pt, 300pt, 60pt), stroke: 0.5pt, [1], [First item text.], [Yes], [2], [Second item text.], [No])
#pagebreak()
#text(size: 14pt, weight: "bold")[Part Two]
#v(4pt)
Second page text, plain and short.
"""


def main():
    out = sys.argv[1]
    font = sys.argv[sys.argv.index("--font") + 1] if "--font" in sys.argv else subprocess.run(["fc-match", "-f", "%{family}", "serif"], capture_output=True, text=True).stdout.split(",")[0]
    with tempfile.TemporaryDirectory() as d:
        src = os.path.join(d, "f.typ")
        open(src, "w").write(BODY.format(font=font) + ("#place(top + left, dx: 300pt, dy: 300pt, circle(radius: 20pt, stroke: 1pt))\n" if "--curve" in sys.argv else ""))
        if "--scan" not in sys.argv:
            subprocess.run(["typst", "compile", src, out], check=True)
            return
        subprocess.run(["typst", "compile", src, os.path.join(d, "p{n}.png"), "--ppi", "100"], check=True)
        pngs = sorted(f for f in os.listdir(d) if f.endswith(".png"))
        wrap = os.path.join(d, "w.typ")
        open(wrap, "w").write("#set page(paper: \"a4\", margin: 0pt)\n" + "\n#pagebreak()\n".join(f'#image("{p}", width: 100%)' for p in pngs))
        subprocess.run(["typst", "compile", wrap, out], check=True)


if __name__ == "__main__":
    main()
