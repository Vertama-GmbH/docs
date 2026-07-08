#!/usr/bin/env bash
#
# Sync a self-contained reveal.js deck from its canonical source
# into the docs tree. Called by `make sync-*-deck` targets; not
# usually invoked directly.
#
# Removes `<aside class="notes">` speaker-note blocks from the copied
# HTML (they contain presenter guidance not intended for the public
# site). Other assets (SVG, images/) are copied unchanged.
#
# Usage: scripts/sync-reveal-deck.sh <source-dir> <destination-dir>

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <source-dir> <destination-dir>" >&2
  exit 2
fi

SRC="$1"
DST="$2"

if [[ ! -f "$SRC/index.html" ]]; then
  echo "error: $SRC/index.html not found" >&2
  exit 1
fi

mkdir -p "$DST"

# HTML with speaker notes stripped
uv run python scripts/strip-notes.py < "$SRC/index.html" > "$DST/index.html"

# Brand assets, copied unchanged
cp "$SRC"/Vertama-*.svg "$DST/" 2>/dev/null || true

# Any images/ subfolder, copied unchanged
if [[ -d "$SRC/images" ]]; then
  mkdir -p "$DST/images"
  cp -r "$SRC/images/." "$DST/images/"
fi

echo "→ synced deck: $SRC → $DST (speaker notes stripped)"
