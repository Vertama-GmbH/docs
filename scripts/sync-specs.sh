#!/usr/bin/env bash
#
# Sync V.ap's OpenAPI specs into the docs tree (docs-sources.md, the
# "OpenAPI spec" rows). Called by `make sync-specs`; not usually invoked
# directly.
#
# The specs come from a commit of the V.ap repo, never from its working
# tree: by default the newest prod-* tag, so the site shows exactly what
# production runs, and work that is merged but not promoted stays off the
# site. Each copy is its source unchanged, with one exception: DUBA's spec
# sits one level above the others in V.ap, so its $ref to web/api.yml is
# re-based to this tree, where every spec sits in Products/<product>/.
# The XÖV code lists the synced specs reference come along, and no others.
#
# Usage: scripts/sync-specs.sh <V.ap repo> [<tag or commit>]

set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: $0 <V.ap repo> [<tag or commit>]" >&2
  exit 2
fi

VAP="$1"
cd "$(dirname "$0")/.."
DST=docs/Products
RES=src/main/resources/de/vertama

git -C "$VAP" fetch --quiet --tags origin
REF="${2:-$(git -C "$VAP" tag -l 'prod-*' --sort=-creatordate | head -1)}"
if [[ -z "$REF" ]]; then
  echo "no prod-* tag in $VAP" >&2
  exit 1
fi
SHA=$(git -C "$VAP" rev-parse --short "$REF^{commit}")
echo "V.ap specs from $REF ($SHA)"

# copy <path below de/vertama in V.ap> <path below docs/Products here>
copy() {
  git -C "$VAP" show "$REF:$RES/$1" > "$DST/$2"
  echo "  $2 <- $1"
}

copy belim/api.yml    BELIM/api.yml
copy digg/api.yml     DIGG/api.yml
copy digt/api.yml     DIGT/api.yml
copy divi/api.yml     DIVI/api.yml
copy elim/api.yml     ELIM/api.yml
copy elimplus/api.yml ELIMPLUS/api.yml
copy web/api.yml      web/api.yml
copy zeag/api.yml     ZEAG/api.yml

git -C "$VAP" show "$REF:$RES/duba-v1.yml" \
  | sed "s#\$ref: 'web/api.yml#\$ref: '../web/api.yml#" > "$DST/DUBA/api.yml"
echo "  DUBA/api.yml <- duba-v1.yml, \$ref to web/api.yml re-based"

mkdir -p "$DST/xoev/codelists"
for list in $(grep -h -o -E "\.\./xoev/codelists/[A-Za-z]+\.yml" "$DST"/*/api.yml | sort -u | sed 's#.*/##'); do
  copy "xoev/codelists/$list" "xoev/codelists/$list"
done
