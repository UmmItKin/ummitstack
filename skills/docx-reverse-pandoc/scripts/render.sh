#!/bin/sh
# Usage: render.sh original.docx rebuilt.docx out-dir [first-page last-page]
set -eu
a=${1:?usage: render.sh original.docx rebuilt.docx out-dir [first last]}
b=${2:?usage: render.sh original.docx rebuilt.docx out-dir [first last]}
out=${3:?usage: render.sh original.docx rebuilt.docx out-dir [first last]}
first=${4:-1}
last=${5:-4}
for t in soffice pdftoppm pdfinfo magick; do
  command -v "$t" >/dev/null 2>&1 || { echo "$t not found" >&2; exit 1; }
done
[ ! -e "$out" ] || { echo "$out already exists; choose a new directory" >&2; exit 1; }
mkdir -p "$out/o" "$out/r" "$out/profile"
out=$(cd "$out" && pwd)
cp "$a" "$out/o/original.docx"
cp "$b" "$out/r/rebuilt.docx"
for d in o r; do
  soffice "-env:UserInstallation=file://$out/profile" --headless --convert-to pdf --outdir "$out/$d" "$out/$d/$(ls "$out/$d" | head -1)" >/dev/null 2>&1
done
echo "pages  original: $(pdfinfo "$out/o/original.pdf" | awk '/^Pages/{print $2}')   rebuilt: $(pdfinfo "$out/r/rebuilt.pdf" | awk '/^Pages/{print $2}')"
pdftoppm -r 38 -png -f "$first" -l "$last" "$out/o/original.pdf" "$out/o/p"
pdftoppm -r 38 -png -f "$first" -l "$last" "$out/r/rebuilt.pdf" "$out/r/p"
magick "$out"/o/p-*.png +append "$out/o/row.png"
magick "$out"/r/p-*.png +append "$out/r/row.png"
magick "$out/o/row.png" "$out/r/row.png" -append -bordercolor '#888' -border 2 "$out/compare.png"
echo "$out/compare.png"
