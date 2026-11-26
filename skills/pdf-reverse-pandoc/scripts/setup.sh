#!/bin/sh
# Usage: sh setup.sh
# Checks the tools this skill needs and prints the command that installs what is missing. It never installs anything
# and never runs sudo: copy the command yourself.
need=""
for t in pdftotext pdftohtml pdftocairo pdftoppm pdfinfo pdffonts pdfimages fc-match typst magick python3; do
  command -v "$t" >/dev/null 2>&1 || need="$need $t"
done
if [ -z "$need" ]; then
  echo "all tools found"
  printf 'typst: '; typst --version
  printf 'poppler: '; pdftotext -v 2>&1 | head -1
  exit 0
fi
echo "missing tools:$need"
. /etc/os-release 2>/dev/null
case "${ID:-} ${ID_LIKE:-}" in
  *arch*)           echo "install:  sudo pacman -S poppler typst imagemagick fontconfig python" ;;
  *debian*|*ubuntu*) echo "install:  sudo apt install poppler-utils imagemagick fontconfig python3"
                     echo "          and typst: sudo apt install typst (if your release has it), otherwise get a release from https://github.com/typst/typst/releases" ;;
  *fedora*|*rhel*)  echo "install:  sudo dnf install poppler-utils typst ImageMagick fontconfig python3" ;;
  *)                echo "install the packages that provide: poppler tools, typst, ImageMagick, fontconfig, python3" ;;
esac
echo "(package names are not verified on every release; if one is not found, search your package manager for the tool name)"
exit 1
