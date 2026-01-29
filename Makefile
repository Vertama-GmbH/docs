
.PHONY: setup build publish clean

VENV_DIR := .venv

setup:
	@echo "Setting up virtual environment and installing dependencies..."
	uv sync

build:
	@echo "Building MkDocs documentation..."
	uv run mkdocs build

# PDF generation disabled - mkdocs PDF plugin ecosystem is unreliable
# pdf:
# 	@echo "PDF generation not supported"

serve:
	@echo "Starting MkDocs development server..."
	uv run mkdocs serve

publish:
	@echo "Publishing MkDocs documentation to GitHub Pages..."
	uv run mkdocs gh-deploy --remote-name github

clean:
	@echo "Cleaning up build artifacts and virtual environment..."
	rm -rf site
	rm -rf $(VENV_DIR)
