#!/bin/sh
# Usage: reverse.sh input.docx [out-dir] [--allow-missing-fonts]
# Exit 3: a text font is not installed and --allow-missing-fonts was not given.
set -eu
allow=no
for a in "$@"; do [ "$a" = "--allow-missing-fonts" ] && allow=yes; done
set -- $(for a in "$@"; do [ "$a" = "--allow-missing-fonts" ] || printf '%s\n' "$a"; done)
in=${1:?usage: reverse.sh input.docx [out-dir] [--allow-missing-fonts]}
command -v pandoc >/dev/null 2>&1 || { echo "pandoc not found" >&2; exit 1; }
[ -f "$in" ] || { echo "no such file: $in" >&2; exit 1; }
out=${2:-$(basename "$in" .docx)-src}
if [ -e "$out" ] && [ -n "$(ls "$out" | grep -v -e '^run.json$' -e '^findings.json$' -e '^inventory-original.txt$' -e '^coverage.json$')" ]; then
  echo "$out already holds files from an earlier run; choose a new directory" >&2
  exit 1
fi
here=$(cd "$(dirname "$0")" && pwd)
if missing=$(python3 "$here/inventory.py" --missing-fonts "$in"); then :; else
  echo "the text uses fonts that are not installed:" >&2
  echo "$missing" | sed 's/^/  /' >&2
  [ "$allow" = yes ] || { echo "stopping: install them, or run again with --allow-missing-fonts" >&2; exit 3; }
  echo "continuing with --allow-missing-fonts; renders here use substitutes" >&2
fi
mkdir -p "$out"
cp "$in" "$out/reference.docx"
python3 "$here/inventory.py" "$in" > "$out/inventory-original.txt"
python3 "$here/extract_parts.py" "$in" "$out" >/dev/null
python3 "$here/add_pandoc_styles.py" "$out/reference.docx" "$out/extra-styles.xml" >/dev/null
cp "$here/build.lua" "$out/build.lua"
cp "$here/postprocess.py" "$out/postprocess.py"
(cd "$out" && pandoc -f docx+styles --lua-filter="$here/reverse.lua" --extract-media=. --wrap=none source.docx -t markdown -o doc.md && rm source.docx)
cat > "$out/build.sh" <<'EOF'
#!/bin/sh
cd "$(dirname "$0")" && pandoc doc.md -f markdown -o rebuilt.docx --reference-doc=reference.docx --lua-filter=build.lua && python3 postprocess.py reference.docx rebuilt.docx table-widths.txt
EOF
echo "$out"
