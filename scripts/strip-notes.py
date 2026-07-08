#!/usr/bin/env python
"""Strip `<aside class="notes">` blocks from a reveal.js deck.

Reads HTML from stdin, writes stripped HTML to stdout. Uses BeautifulSoup
so it's robust to any formatting the source deck happens to use — inline
notes, notes on their own lines, notes containing nested markup, notes
before or after the slide body content. Sed-based stripping was
considered and rejected: any `range delete` pattern is fragile against
single-line notes and against future reformatting of the source.

Invoked from `scripts/sync-reveal-deck.sh` as part of the pull-based
mirror flow (see `Makefile` `sync-*-deck` targets and `docs-sources.md`).
"""

import sys
from bs4 import BeautifulSoup

soup = BeautifulSoup(sys.stdin.read(), "html.parser")
for note in soup.find_all("aside", class_="notes"):
    note.decompose()
sys.stdout.write(str(soup))
