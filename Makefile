
.PHONY: setup build publish clean

VENV_DIR := .venv

setup: uv-sync

uv-sync:
	uv sync

build: uv-sync
	@echo "Building MkDocs documentation..."
	.venv/bin/mkdocs build

# PDF generation disabled - mkdocs PDF plugin ecosystem is unreliable
# pdf:
# 	@echo "PDF generation not supported"

serve: uv-sync
	@echo "Starting MkDocs development server..."
	uv run mkdocs serve

dev: uv-sync
	@echo "Starting MkDocs development server..."
	uv run mkdocs serve

publish:
	@echo "Publishing MkDocs documentation to GitHub Pages..."
	uv run mkdocs gh-deploy --remote-name github

clean:
	@echo "Cleaning up build artifacts and virtual environment..."
	rm -rf site
	rm -rf $(VENV_DIR)
