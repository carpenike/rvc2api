# Contributing to Documentation

This guide explains how to contribute to the CoachIQ documentation.

## Documentation Structure

The documentation is built using [MkDocs](https://www.mkdocs.org/) with the [Material theme](https://squidfunk.github.io/mkdocs-material/).

The documentation files are located in the following directories:

- `/docs/`: Main project documentation (markdown files)
- `/frontend/docs/`: Frontend-specific documentation

## Setting Up the Documentation Environment

To work on the documentation, you'll need to have the project dependencies installed:

```bash
poetry install
```

This will install MkDocs and all required plugins.

## Previewing the Documentation Locally

To preview the documentation while you're working on it:

```bash
cd docs
mkdocs serve
```

This will start a local web server at <http://localhost:8000/> that automatically updates when you save changes to the markdown files.

You can also use the VS Code task "Server: Serve Documentation" to launch the docs server.

## Directory Organization

The documentation is organized into several sections:

- **API Reference**: Documentation for the REST and WebSocket APIs
- **Architecture**: System design and component organization
- **Development Guides**: How to set up and develop the project
- **Contributing**: Guidelines for contributing to the project

## Adding New Documentation

To add new documentation:

1. Create a new markdown file in the appropriate directory
2. Add a reference to it in `docs/mkdocs.yml` under the `nav` section
3. Follow the existing style and formatting

## Documentation Standards

### Formatting

- Use ATX-style headers (`#`, `##`, `###`, etc.)
- Use fenced code blocks with language specifiers
- Use relative links to other pages within the documentation
- Include alt text for images

### Code Examples

- Include language specifiers for code blocks (e.g., ```python)
- Use meaningful variable names in examples
- Add comments to explain complex code
- Ensure code examples are tested and working

### API Documentation

- Document all parameters and return values
- Include example requests and responses
- Specify required permissions or authentication
- Note any limitations or restrictions

## Generating API Documentation

The API documentation is partially generated from the OpenAPI schema produced by FastAPI. To update the OpenAPI schema:

```bash
poetry run python scripts/export_openapi.py
```

This will generate `docs/api/openapi.json` and `docs/api/openapi.yaml`.

You can also use the VS Code task "API: Export OpenAPI Schema" to generate the schema.

## Building the Documentation for Production

To build the documentation for production:

```bash
cd docs
mkdocs build
```

This will generate a static site in the `site` directory that can be deployed to a web server.

You can also use the VS Code task "Build: Documentation" to build the documentation.

## Extending the Documentation

### Adding New Sections

To add a new section to the documentation:

1. Create a new directory in `/docs/`
2. Add markdown files to the directory
3. Update `docs/mkdocs.yml` to include the new section and files

### Adding plugins

To add a new plugin to the documentation:

1. Add the plugin to `pyproject.toml` in the `[tool.poetry.dev-dependencies]` section
2. Run `poetry install` to install the plugin
3. Update `docs/mkdocs.yml` to configure the plugin
