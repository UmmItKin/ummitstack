#!/bin/sh
# Build an existing ppt-master project: final quality gate, notes, SVG preview,
# PPTX export, PDF export, then check that all counts match the SVG count.
# Usage: build.sh <project-dir>
# Env: PPT_MASTER_SCRIPTS  ppt-master scripts dir (default ~/.claude/skills/ppt-master/scripts)
#      PPT_MASTER_PYTHON   interpreter with ppt-master's requirements (default python3)
set -eu

project=${1:?usage: build.sh <project-dir>}
scripts=${PPT_MASTER_SCRIPTS:-$HOME/.claude/skills/ppt-master/scripts}
py=${PPT_MASTER_PYTHON:-python3}

fail() { echo "build: $*" >&2; exit 1; }

[ -d "$project/svg_output" ] || fail "no svg_output/ in $project"
[ -f "$scripts/svg_to_pptx.py" ] || fail "ppt-master scripts not found at $scripts; set PPT_MASTER_SCRIPTS"
svgs=$(find "$project/svg_output" -maxdepth 1 -type f -name '*.svg' | wc -l)
[ "$svgs" -gt 0 ] || fail "no SVGs in $project/svg_output"

echo "[1/4] final quality gate"
"$py" "$scripts/svg_quality_checker.py" "$project" --canonical-authoring --stage final --json

echo "[2/4] notes and preview"
if [ -f "$project/notes/total.md" ]; then
  "$py" "$scripts/total_md_split.py" "$project"
  notes=yes
else
  notes=no
fi
"$py" "$scripts/finalize_svg.py" "$project"

echo "[3/4] export PPTX"
if [ "$notes" = yes ]; then
  "$py" "$scripts/svg_to_pptx.py" "$project"
else
  "$py" "$scripts/svg_to_pptx.py" "$project" --no-notes
fi
pptx=$(ls -t "$project"/exports/*.pptx 2>/dev/null | head -1)
[ -n "$pptx" ] || fail "no PPTX in $project/exports"

echo "[4/4] PDF"
pdf=
if command -v rsvg-convert >/dev/null 2>&1; then
  src=$project/svg_final
  [ -d "$src" ] || src=$project/svg_output
  pdf=$project/$(basename "$project").pdf
  rsvg-convert -f pdf -o "$pdf" "$src"/*.svg
else
  echo "skip: rsvg-convert not installed"
fi

slides=$("$py" -c 'import re,sys,zipfile; x=zipfile.ZipFile(sys.argv[1]).read("ppt/presentation.xml").decode("utf-8","replace"); print(len(re.findall(r"<p:sldId\b", x)))' "$pptx")
[ "$slides" -eq "$svgs" ] || fail "PPTX has $slides slides, expected $svgs"
if [ -n "$pdf" ] && command -v pdfinfo >/dev/null 2>&1; then
  pages=$(pdfinfo "$pdf" | awk '/^Pages:/ {print $2}')
  [ "$pages" -eq "$svgs" ] || fail "PDF has $pages pages, expected $svgs"
fi

echo "ok: $slides slides, $pptx"
