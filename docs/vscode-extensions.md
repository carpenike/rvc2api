# VS Code Extensions for CoachIQ Development

This document provides details about the recommended VS Code extensions for developing the CoachIQ project. These extensions are tailored to support the project's technology stack and improve the development experience.

## Installing the Extensions

To install the recommended extensions:

1. Open VS Code with the CoachIQ project
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Type and select "Extensions: Show Recommended Extensions"
4. Install the extensions from the recommendations list

Alternatively, you can install them one by one using the VS Code Extensions view (`Cmd+Shift+X` or `Ctrl+Shift+X`).

## Python Development Extensions

### Core Python Support

- **[Python (ms-python.python)](https://marketplace.visualstudio.com/items?itemName=ms-python.python)**: Essential Python language support with IntelliSense, linting, and debugging
- **[Pylance (ms-python.vscode-pylance)](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)**: Fast type checking and IntelliSense for Python
  - Configured to work with our custom type stubs in the `typings/` directory
  - See `typings/fastapi/README.md` for information about our FastAPI type stub organization

### Code Quality Tools

- **[Ruff (charliermarsh.ruff)](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff)**: Fast Python linter and formatter integrated into VS Code
- **[isort (ms-python.isort)](https://marketplace.visualstudio.com/items?itemName=ms-python.isort)**: Import sorting for Python files (mostly handled by Ruff now)

### Python Workflow

- **[Poetry (njpwerner.poetry)](https://marketplace.visualstudio.com/items?itemName=njpwerner.poetry)**: Poetry commands and environment management
- **[Python Test Explorer (tht13.python)](https://marketplace.visualstudio.com/items?itemName=tht13.python)**: Discover and run Python tests

### FastAPI Development

- **[FastAPI Snippets (LikhithD.fastapi-snippets-extension)](https://marketplace.visualstudio.com/items?itemName=LikhithD.fastapi-snippets-extension)**: Code snippets for FastAPI development

## Nix Development Extensions

- **[Nix IDE (jnoortheen.nix-ide)](https://marketplace.visualstudio.com/items?itemName=jnoortheen.nix-ide)**: Language support, formatting, and linting for Nix files
- **[Nix Environment Selector (arrterian.nix-env-selector)](https://marketplace.visualstudio.com/items?itemName=arrterian.nix-env-selector)**: Manage and select Nix environments
- **[Nix (bbenoist.Nix)](https://marketplace.visualstudio.com/items?itemName=bbenoist.Nix)**: Syntax highlighting for Nix files
- **[direnv (mkhl.direnv)](https://marketplace.visualstudio.com/items?itemName=mkhl.direnv)**: Integrates direnv for automatic environment activation

## Frontend Development Extensions

### React & TypeScript

- **[ESLint (dbaeumer.vscode-eslint)](https://marketplace.visualstudio.com/items?itemName=dbaeumer.vscode-eslint)**: JavaScript and TypeScript linting
- **[Prettier (esbenp.prettier-vscode)](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode)**: Code formatting for JavaScript, TypeScript, and CSS
- **[ES7+ React/Redux/React-Native snippets (dsznajder.es7-react-js-snippets)](https://marketplace.visualstudio.com/items?itemName=dsznajder.es7-react-js-snippets)**: Code snippets for React development

### UI Development

- **[Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)](https://marketplace.visualstudio.com/items?itemName=bradlc.vscode-tailwindcss)**: IntelliSense for Tailwind CSS classes
- **[Headless UI Snippets (dylanwatson.headlessui-snippets)](https://marketplace.visualstudio.com/items?itemName=dylanwatson.headlessui-snippets)**: Code snippets for Headless UI components

### Build Tools

- **[Vite (antfu.vite)](https://marketplace.visualstudio.com/items?itemName=antfu.vite)**: Enhanced support for Vite projects

## General Development Tools

- **[JSON5 (mrmlnc.vscode-json5)](https://marketplace.visualstudio.com/items?itemName=mrmlnc.vscode-json5)**: Advanced JSON support with comments
- **[YAML (redhat.vscode-yaml)](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)**: YAML language support and validation

### AI Assistance

- **[GitHub Copilot (GitHub.copilot)](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)**: AI-powered code completion
- **[GitHub Copilot Chat (GitHub.copilot-chat)](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)**: Conversational AI assistance with MCP tools integration

## Using Extensions with Tasks

Many of these extensions work well with the VS Code tasks defined in `tasks.json`:

1. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
2. Type and select "Tasks: Run Task"
3. Choose a task like "Start Backend Server" or "Format Code (Ruff)"

See the [VS Code Tasks documentation](https://code.visualstudio.com/docs/editor/tasks) for more information on using tasks.

## MCP Tools Integration

The GitHub Copilot Chat extension integrates with Model Context Protocol (MCP) tools like @context7, @perplexity, and @github. See `docs/mcp-tools-setup.md` for detailed information on using these tools.

## Extension Configuration

Most extensions are pre-configured in `.vscode/settings.json`, but you may want to customize them further. Refer to each extension's documentation for configuration options.

For project-specific settings, update `.vscode/settings.json` to ensure consistency across the development team.
