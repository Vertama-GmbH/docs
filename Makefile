
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

serve:
	@echo "Starting MkDocs development server..."
	./$(VENV_DIR)/bin/mkdocs serve

preview:
	@echo "Starting MkDocs development server..."
	./$(VENV_DIR)/bin/mkdocs serve --config-file mkdocs.prod.yml --dev-addr 0.0.0.0:8001

publish:
	@echo "Publishing MkDocs documentation to GitHub Pages..."
	./$(VENV_DIR)/bin/mkdocs gh-deploy --config-file mkdocs.prod.yml

clean:
	@echo "Cleaning up build artifacts and virtual environment..."
	rm -rf site
	rm -rf $(VENV_DIR)
