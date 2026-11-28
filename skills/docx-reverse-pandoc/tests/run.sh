#!/bin/sh
# Usage: sh tests/run.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
s=$here/../scripts
command -v pandoc >/dev/null 2>&1 || { echo "skip: pandoc is not installed"; exit 0; }
T=$(mktemp -d)
pass=0
fail=0
ok() { pass=$((pass + 1)); echo "PASS $1"; }
bad() { fail=$((fail + 1)); echo "FAIL $1"; }
expect() {
  name=$1
  want=$2
  shift 2
  "$@" >/dev/null 2>&1
  got=$?
  if [ "$want" = nonzero ]; then
    [ "$got" -ne 0 ] && ok "$name" || bad "$name (exit $got, wanted a failure)"
  else
    [ "$got" -eq "$want" ] && ok "$name" || bad "$name (exit $got, wanted $want)"
  fi
}

python3 "$here/make_fixture.py" "$T/f.docx"
python3 "$here/make_fixture.py" "$T/box.docx" --textbox
python3 "$here/make_fixture.py" "$T/font.docx" --missing-font
python3 "$here/make_fixture.py" "$T/shape.docx" --shape

echo "== the good path =="
expect "reverse accepts a document whose text fonts are installed" 0 sh "$s/reverse.sh" "$T/f.docx" "$T/out"
expect "build runs" 0 sh "$T/out/build.sh"
expect "verify passes structure and fidelity" 0 python3 "$s/verify.py" "$T/f.docx" "$T/out" --no-render
expect "rebuilt XML parses and no cell has two tcPr" 0 python3 "$here/check_xml.py" "$T/out/rebuilt.docx"

python3 -c "import zipfile,sys;d=zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode();sys.exit('SPMK' in d or '>  <' not in d and 'with  two' not in d)" "$T/out/rebuilt.docx" && ok "a run of two spaces survives the round trip" || bad "a run of two spaces was folded into one"

python3 -c "import zipfile,sys,re;d=zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode();sys.exit(not re.search(r'<w:rStyle w:val=\"DF\d+\"\s*/><w:b/><w:bCs/></w:rPr><w:t xml:space=\"preserve\"> </w:t>', d))" "$T/out/rebuilt.docx" && ok "a space-only run keeps its run style and bold (its size sets the line height)" || bad "a space-only run lost its run style"

expect "the --missing-fonts flag works after the file name too (found by a cold-start test)" 0 python3 "$s/inventory.py" "$T/f.docx" --missing-fonts

echo "== mistake: skipping the post-processing (page break, background, rows, shading were lost) =="
( cd "$T/out" && pandoc doc.md -f markdown -o noprocess.docx --reference-doc=reference.docx --lua-filter=build.lua )
expect "the structure compare fails without postprocess.py" nonzero python3 "$s/inventory.py" "$T/f.docx" "$T/out/noprocess.docx"

echo "== mistake: a plain Pandoc build with no reference document or filters =="
pandoc "$T/out/doc.md" -o "$T/plain.docx"
expect "the structure compare fails on a plain build" nonzero python3 "$s/inventory.py" "$T/f.docx" "$T/plain.docx"
expect "the fidelity check fails on a plain build" nonzero python3 "$s/fidelity.py" "$T/f.docx" "$T/plain.docx"

echo "== mistake: formatting dropped from one paragraph =="
python3 "$here/drop_alignment.py" "$T/out/rebuilt.docx" "$T/lost.docx"
expect "the fidelity check fails when an alignment is lost" nonzero python3 "$s/fidelity.py" "$T/f.docx" "$T/lost.docx"
python3 "$s/fidelity.py" "$T/f.docx" "$T/lost.docx" 2>/dev/null | grep -q "jc" && ok "and the report names the property" || bad "the report does not name the property"

echo "== mistake: a property nothing keeps (text box) =="
expect "the coverage ledger flags a text box" 1 python3 "$s/coverage.py" "$T/box.docx"
expect "and accepts it when told to" 0 python3 "$s/coverage.py" "$T/box.docx" --accept "text boxes,legacy pictures and shapes"
expect "and a document without one passes" 0 python3 "$s/coverage.py" "$T/f.docx"

echo "== mistake: a floating shape without text was dropped (lines beside form fields) =="
expect "the coverage ledger carries a floating shape without text" 0 python3 "$s/coverage.py" "$T/shape.docx"
expect "reverse and build keep it" 0 sh -c "sh '$s/reverse.sh' '$T/shape.docx' '$T/shape-out' && sh '$T/shape-out/build.sh'"
python3 -c "import zipfile,sys;d=zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode();sys.exit(not ('<wp:anchor' in d and 'xmlns:mc=' in d and 'SHAPE' not in d))" "$T/shape-out/rebuilt.docx" && ok "and the rebuilt file holds the anchored shape" || bad "the rebuilt file lost the anchored shape"
expect "rebuilt XML with the shape parses" 0 python3 "$here/check_xml.py" "$T/shape-out/rebuilt.docx"

echo "== mistake: working before checking the fonts =="
expect "reverse refuses a missing text font" 3 sh "$s/reverse.sh" "$T/font.docx" "$T/font-out"
[ ! -e "$T/font-out" ] && ok "and creates nothing" || bad "and still created the folder"
cp "$T/font.docx" "$T/a b.docx"
expect "reverse handles a file name with a space and the flag first (found on 'Assignment 2.docx')" 0 sh "$s/reverse.sh" --allow-missing-fonts "$T/a b.docx" "$T/a b-out"
if command -v soffice >/dev/null 2>&1 && command -v magick >/dev/null 2>&1; then
  expect "render works in a folder with a space in its path" 0 sh "$s/render.sh" "$T/f.docx" "$T/out/rebuilt.docx" "$T/sp ace/render" 1 1
  [ -f "$T/sp ace/render/r/rebuilt.pdf" ] && ok "and writes the rebuilt PDF" || bad "the rebuilt PDF is missing"
fi
expect "reverse goes on with --allow-missing-fonts" 0 sh "$s/reverse.sh" "$T/font.docx" "$T/font-out2" --allow-missing-fonts

echo "== mistake: calling a run complete without proof =="
python3 "$here/check_run.py" "$s" "$T" > "$T/run-results.txt" 2>"$T/run-errors.txt" || bad "check_run.py crashed: $(tail -1 "$T/run-errors.txt")"
cat "$T/run-results.txt"
pass=$((pass + $(grep -c '^PASS' "$T/run-results.txt")))
fail=$((fail + $(grep -c '^FAIL' "$T/run-results.txt")))

echo
echo "temporary folder: $T"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
