---
applyTo: "**"
---

# Development Environment

## Dependency Management

- poetry (Python dependencies in pyproject.toml)
- npm (JavaScript dependencies in web_ui/package.json)
- nix (reproducible environments via flake)
- Version-locked dependencies

## Backend Dev Commands

```bash
poetry run python src/core_daemon/main.py  # Run server
poetry run pytest  # Tests
poetry run ruff format src  # Format
poetry run ruff check .  # Lint
npx pyright src  # Type checking
```

## Frontend Dev Commands

```bash
cd web_ui
npm install  # Install dependencies
npm run dev  # Start development server
npm run build  # Build for production
npm run lint  # Run ESLint with flat config
npm run lint:fix  # Run ESLint with automatic fixes
npm run fix:style  # Run scripts to fix common ESLint issues
npm run fix:interfaces  # Fix TypeScript interface parsing errors
npm run typecheck  # Run TypeScript type checking
```

## Setup

```bash
git clone https://github.com/carpenike/rvc2api.git && cd rvc2api
nix develop  # Or: poetry install && cd web_ui && npm install
cp .env.example .env
```

## Running Both Frontend and Backend

1. Start the backend server: `poetry run python src/core_daemon/main.py`
2. In a separate terminal: `cd web_ui && npm run dev`
3. Access the frontend at http://localhost:5173

## VS Code Tasks

This project has extensive VS Code task configurations that streamline development workflows.

For detailed information about available tasks, see [vscode-tasks.instructions.md](vscode-tasks.instructions.md).

You can access tasks through:

- Command Palette (Ctrl+Shift+P or ⌘+Shift+P on macOS) → "Tasks: Run Task"
- Terminal menu → Run Task
- Quick access with Ctrl+Shift+B or ⌘+Shift+B for default build tasks
