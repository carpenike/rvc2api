---
applyTo: "**"
---

# Development Environment

## Dependency Management

-## Development Workflow Consistency

### Reproducible Development

- **GitHub Actions CI** uses `nix run .#ci`
- **Local Nix apps** provide identical environments to CI
- **VS Code tasks** include Nix-based options for consistency
- **Pre-commit hooks** run the same tools as CI via `.pre-commit-config.yaml`

### Pre-commit Best Practices

```bash
# For automatic Git hooks (recommended for daily development)
poetry run pre-commit install

# For manual checks with reproducible environment
nix run .#precommit  # Matches CI exactly

# For full CI reproduction locally
nix run .#ci         # Complete CI suite
```

The `.pre-commit-config.yaml` file defines **what** checks to run, while `nix run .#precommit` provides a **reproducible environment** to run them.

### Recommended Workflow

1. **Setup once**: `poetry run pre-commit install` (enables Git hooks)
2. **Daily development**: Let Git hooks run automatically
3. **Before pushing**: Run `nix run .#precommit` to match CI
4. **Debugging CI failures**: Use `nix run .#ci` to reproduce CI locallyn dependencies in pyproject.toml)
- npm (JavaScript dependencies in web_ui/package.json)
- nix (reproducible environments via flake)
- Version-locked dependencies

## Backend Dev Commands

### Traditional Method (Poetry)

```bash
poetry run python run_server.py  # Run server
poetry run pytest  # Tests
poetry run ruff format src  # Format
poetry run ruff check .  # Lint
npx pyright src  # Type checking
```

### Nix Apps (Reproducible - matches CI exactly)

```bash
nix run .#ci        # Full CI suite (pre-commit + tests + linting)
nix run .#precommit # Pre-commit checks only
nix run .#test      # Run pytest
nix run .#lint      # Run Ruff + Pyright + frontend linting
nix run .#format    # Format code (Ruff + ESLint --fix)
```

> **💡 Recommendation**: Use Nix apps for reproducible results that match CI.

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

1. Start the backend server: `poetry run python run_server.py`
2. In a separate terminal: `cd web_ui && npm run dev`
3. Access the frontend at http://localhost:5173

## VS Code Tasks

This project has extensive VS Code task configurations that streamline development workflows, including Nix-based tasks for reproducibility.

You can access tasks through:

- Command Palette (Ctrl+Shift+P or ⌘+Shift+P on macOS) → "Tasks: Run Task"
- Terminal menu → Run Task
- Quick access with Ctrl+Shift+B or ⌘+Shift+B for default build tasks

## Development Workflow Consistency

### Reproducible Development

- **GitHub Actions CI** uses `nix run .#ci`
- **Local Nix apps** provide identical environments to CI
- **VS Code tasks** include Nix-based options for consistency
- **Pre-commit hooks** run the same tools as CI

### Recommended Workflow

1. **For daily development**: Use VS Code tasks or Poetry/npm commands
2. **Before committing**: Run `nix run .#precommit` or `nix run .#ci`
3. **For debugging CI failures**: Use `nix run .#ci` to reproduce CI locally
