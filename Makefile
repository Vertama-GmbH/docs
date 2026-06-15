
.PHONY: setup build publish clean downloads

VENV_DIR := .venv

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
	uv run mkdocs serve

dev: uv-sync downloads
	@echo "Starting MkDocs development server..."
	uv run mkdocs serve

publish: downloads
	@echo "Publishing MkDocs documentation to GitHub Pages..."
	uv run mkdocs gh-deploy --remote-name github

clean:
	@echo "Cleaning up build artifacts and virtual environment..."
	rm -rf site
	rm -rf $(VENV_DIR)
