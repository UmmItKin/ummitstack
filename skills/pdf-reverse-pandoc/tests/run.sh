#!/bin/sh
# Usage: sh tests/run.sh
# Reproduces the mistakes this skill and its sibling once made and checks that each one is caught.
# Works in a new temporary folder and uses only generated PDFs.
set -u
here=$(cd "$(dirname "$0")" && pwd)
s=$here/../scripts
for t in typst pdftohtml pdftocairo pdftoppm magick; do
  command -v "$t" >/dev/null 2>&1 || { echo "skip: $t is not installed (run sh scripts/setup.sh)"; exit 0; }
done
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

python3 "$here/make_fixture.py" "$T/f.pdf"
python3 "$here/make_fixture.py" "$T/scan.pdf" --scan
python3 "$here/make_fixture.py" "$T/curve.pdf" --curve
python3 "$here/make_fixture.py" "$T/link.pdf" --link

echo "== the good path =="
expect "reverse accepts a text PDF whose fonts are installed" 0 python3 "$s/reverse.py" "$T/f.pdf" "$T/out"
expect "build.sh rebuilds it" 0 sh "$T/out/build.sh"
expect "verify passes all gates" 0 python3 "$s/verify.py" "$T/f.pdf" "$T/out"

echo "== mistake: calling it the same from the text alone =="
for kind in size word move shape spacing; do
  python3 "$here/mutate.py" "$T/out/doc.typ" "$T/m-$kind.typ" "$kind"
  typst compile "$T/m-$kind.typ" "$T/m-$kind.pdf" >/dev/null 2>&1
  expect "fidelity fails when $kind is wrong" nonzero python3 "$s/fidelity.py" "$T/f.pdf" "$T/m-$kind.pdf"
done

echo "== mistake: a plain rebuild with no layout (text only) =="
pdftotext "$T/f.pdf" "$T/plain.txt"
printf '#set page(paper: "a4")\n#raw(read("plain.txt"))\n' > "$T/plain.typ"
typst compile "$T/plain.typ" "$T/plain.pdf" >/dev/null 2>&1
expect "fidelity fails on a text-only rebuild" nonzero python3 "$s/fidelity.py" "$T/f.pdf" "$T/plain.pdf"

echo "== mistake: starting before checking the input =="
expect "reverse refuses a PDF with no text layer" 2 python3 "$s/reverse.py" "$T/scan.pdf" "$T/scan-out"
mkdir "$T/bin" && printf '#!/bin/sh\necho "Fake Stand In"\n' > "$T/bin/fc-match" && chmod +x "$T/bin/fc-match"
expect "reverse refuses a font that is not installed" 3 env PATH="$T/bin:$PATH" python3 "$s/reverse.py" "$T/f.pdf" "$T/font-out"
expect "and goes on with --allow-substitute-fonts" 0 env PATH="$T/bin:$PATH" python3 "$s/reverse.py" "$T/f.pdf" "$T/font-out2" --allow-substitute-fonts
expect "and verify reports the stand-in font in the fonts gate" 0 sh -c "env PATH=\"$T/bin:\$PATH\" python3 $s/verify.py $T/f.pdf $T/font-out2 --no-render | grep -q substituted"

echo "== mistake: ignoring what is not redrawn (curves, pictures) =="
expect "reverse notes the curve and verify fails" nonzero python3 "$s/verify.py" "$T/curve.pdf" "$T/out" --no-render
python3 "$s/reverse.py" "$T/curve.pdf" "$T/curve-out" >/dev/null 2>&1
expect "and verify passes the structure gate when it is accepted" 0 python3 "$s/verify.py" "$T/curve.pdf" "$T/curve-out" --no-render --accept-unsupported

echo "== mistake: losing links without saying so =="
python3 "$s/reverse.py" "$T/link.pdf" "$T/link-out" >/dev/null 2>&1
expect "verify fails when the original has a link" nonzero python3 "$s/verify.py" "$T/link.pdf" "$T/link-out" --no-render
expect "and passes when the loss is accepted" 0 python3 "$s/verify.py" "$T/link.pdf" "$T/link-out" --no-render --accept-unsupported

echo "== mistake: calling a run complete without proof =="
python3 "$here/check_run.py" "$s" "$T" > "$T/run-results.txt"
python3 "$here/check_random.py" "$s" "$T" >> "$T/run-results.txt"
cat "$T/run-results.txt"
pass=$((pass + $(grep -c '^PASS' "$T/run-results.txt")))
fail=$((fail + $(grep -c '^FAIL' "$T/run-results.txt")))

echo
echo "temporary folder: $T"
echo "passed $pass, failed $fail"
[ "$fail" -eq 0 ]
