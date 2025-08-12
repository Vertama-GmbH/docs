# README

**to be written**

## Local Development

This project uses `Makefile` to orchestrate common tasks. Ensure you have `make` installed.

### Setup

To set up the development environment and install dependencies, run:

```sh
make setup
```

This will create a Python virtual environment (`.venv/`) and install all necessary packages.

### Running the Development Server

To start a local development server with live reloading, run:

```sh
make serve
```

This will typically serve the documentation at `http://127.0.0.1:8000`.

### Building the Documentation

To build the static documentation site, run:

```sh
make build
```

The generated site will be located in the `site/` directory.

### Publishing to GitHub Pages

To publish the documentation to GitHub Pages, run:

```sh
make publish
```

### Cleaning Up

To remove the generated `site/` directory and the virtual environment, run:

```sh
make clean
```
