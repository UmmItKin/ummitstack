#!/bin/sh
# Usage: sh scripts/tla-check.sh
# Model checks specs/pipeline.tla with TLC. The pinned tla2tools.jar is fetched once into ~/.cache/ummitstack (never into
# this repo) and its SHA-256 is compared with the pin below. The pin was taken from the v1.7.4 release asset when this
# script was written; the release publishes no checksum, so it guards against change, not against a bad first download.
# Skips (exit 0, says so) when java or the network is missing.
set -u
cd "$(dirname "$0")/.."
VERSION=v1.7.4
SHA=936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88
JAR=${XDG_CACHE_HOME:-$HOME/.cache}/ummitstack/tla2tools-$VERSION.jar
command -v java >/dev/null 2>&1 || { echo "skip: java is not installed (Arch: sudo pacman -S jre-openjdk-headless)"; exit 0; }
if [ ! -f "$JAR" ]; then
  mkdir -p "$(dirname "$JAR")"
  curl -fsSL -o "$JAR.part" "https://github.com/tlaplus/tlaplus/releases/download/$VERSION/tla2tools.jar" || { rm -f "$JAR.part"; echo "skip: could not download tla2tools.jar"; exit 0; }
  mv "$JAR.part" "$JAR"
fi
echo "$SHA  $JAR" | sha256sum -c - >/dev/null 2>&1 || { echo "FAIL tla2tools.jar does not match the pinned SHA-256"; exit 1; }
out=$(cd specs && java -cp "$JAR" tlc2.TLC -config pipeline.cfg pipeline.tla 2>&1)
echo "$out" | grep -q "No error has been found" && { echo "PASS TLC: no error in specs/pipeline.tla ($(echo "$out" | grep -o '[0-9][0-9,]* distinct states' | head -1))"; exit 0; }
echo "FAIL TLC found an error:"; echo "$out" | tail -25; exit 1
