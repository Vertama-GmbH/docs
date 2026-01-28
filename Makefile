
.PHONY: setup build publish clean

VENV_DIR := .venv

.PHONY: setup build publish clean

setup:
	@echo "Setting up virtual environment and installing dependencies..."
	python3 -m venv $(VENV_DIR)
	./$(VENV_DIR)/bin/pip install -r requirements.txt

build:
	@echo "Building MkDocs documentation..."
	./$(VENV_DIR)/bin/mkdocs build

pdf:
	@echo "Generating PDF documentation..."
	@ENABLE_PDF_EXPORT=1 ./$(VENV_DIR)/bin/mkdocs build --quiet
	@mkdir -p docs/pdf
	@cp site/pdf/document.pdf docs/pdf/document.pdf
	@echo "PDF generated and copied to docs/pdf/document.pdf"
	@echo "Now run 'make dev' or 'make serve' to view it locally"

serve:
	@echo "Starting MkDocs development server..."
	./$(VENV_DIR)/bin/mkdocs serve

dev:
	@echo "Starting MkDocs development server..."
	./$(VENV_DIR)/bin/mkdocs serve --config-file mkdocs.dev.yml

#preview:
#	@echo "Starting MkDocs development server..."
#	./$(VENV_DIR)/bin/mkdocs serve --config-file mkdocs.prod.yml --dev-addr 0.0.0.0:8001

publish:
	@echo "Publishing MkDocs documentation to GitHub Pages..."
	#./$(VENV_DIR)/bin/mkdocs gh-deploy --remote-name github --config-file mkdocs.prod.yml
	./$(VENV_DIR)/bin/mkdocs gh-deploy --remote-name github

clean:
	@echo "Cleaning up build artifacts and virtual environment..."
	rm -rf site
	rm -rf $(VENV_DIR)
