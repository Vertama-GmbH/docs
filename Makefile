
.PHONY: setup build publish clean downloads sync-fremdaufruf-deck sync-all

VENV_DIR := .venv

IP ?= localhost
PORT ?= 7999

# Local checkout paths for the canonical source repos. Override on the
# command line if your working copies live elsewhere:
#   make sync-fremdaufruf-deck V_C=~/somewhere/V.c
V_C  ?= ../V.c
ELIM ?= ../elim

setup: uv-sync

uv-sync:
	uv sync

# Regenerate docs/Downloads/{index.md,index.de.md} from the public
# Vertama-GmbH/releases API. Output is gitignored; run before `serve`
# if you want the Downloads page populated in local preview.
downloads: uv-sync
	@echo "Regenerating Downloads page from Vertama-GmbH/releases..."
	uv run python scripts/generate-downloads.py

build: uv-sync downloads
	@echo "Building MkDocs documentation..."
	.venv/bin/mkdocs build

# PDF generation disabled - mkdocs PDF plugin ecosystem is unreliable
# pdf:
# 	@echo "PDF generation not supported"

serve: uv-sync downloads
	@echo "Starting MkDocs development server..."
	uv run mkdocs serve --dev-addr $(IP):$(PORT)

dev: uv-sync downloads
	@echo "Starting MkDocs development server..."
	uv run mkdocs serve --dev-addr $(IP):$(PORT)

publish: downloads
	@echo "Publishing MkDocs documentation to GitHub Pages..."
	uv run mkdocs gh-deploy --remote-name github

clean:
	@echo "Cleaning up build artifacts and virtual environment..."
	rm -rf site
	rm -rf $(VENV_DIR)

# ---------------------------------------------------------------------------
# Mirror-sync targets — pull authored content from its canonical source repo
# into this docs tree. Each target corresponds to a row in docs-sources.md.
# Makefile is orchestration only; scripts/ contains the per-type processors.
# ---------------------------------------------------------------------------

# Pull the Fremdaufruf presentation deck from V.c, stripping speaker notes
# on the way in (they contain presenter-only guidance not intended for
# the public site).
sync-fremdaufruf-deck: uv-sync
	@scripts/sync-reveal-deck.sh \
		$(V_C)/fremdaufruf/presentation \
		docs/Products/V.connect/Fremdaufruf/presentation

# Aggregator — extend as more sync targets land.
sync-all: sync-fremdaufruf-deck
