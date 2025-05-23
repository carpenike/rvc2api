# Pre-commit and GitHub Actions Configuration

This document describes the enhanced pre-commit and GitHub Actions configuration for the `rvc2api` project.

## Pre-commit Configuration

The project uses [pre-commit](https://pre-commit.com/) to enforce code quality standards before commits. This ensures consistent code formatting and catches common issues early.

### Installed Hooks

The pre-commit configuration includes:

1. **Core file checks**:

   - Trailing whitespace removal
   - End-of-file fixer
   - YAML/JSON/TOML validation
   - Merge conflict detection
   - Debug statement detection
   - Line ending normalization
   - Large file checks

2. **Python code quality**:

   - **Ruff Format**: Code formatting
   - **Ruff**: Modern Python linting (replaces Flake8)
   - **Pyright**: Type checking (see `pyrightconfig.json` and `pyproject.toml`)

3. **Frontend code quality**:

   - **ESLint**: JavaScript/TypeScript linting
   - **djLint**: HTML template linting

4. **Project integrity**:
   - Poetry lock file validation

### Using Pre-commit

#### Traditional Method (Poetry)

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run against all files
poetry run pre-commit run --all-files

# Run a specific hook
poetry run pre-commit run ruff-format --all-files
```

#### Nix-based Method (Reproducible)

For maximum reproducibility and consistency with CI:

```bash
# Run pre-commit checks (same as CI)
nix run .#precommit

# Run full CI suite (includes pre-commit + tests + linting)
nix run .#ci

# Run individual components
nix run .#lint    # Ruff + Pyright + ESLint
nix run .#format  # Format code with Ruff + ESLint --fix
nix run .#test    # Run pytest
```

> **💡 Best Practice**:
> - Install Git hooks once: `poetry run pre-commit install`
> - Use Nix apps for CI-matching checks: `nix run .#precommit`
> - The `.pre-commit-config.yaml` defines **what** to check
> - The Nix apps provide **reproducible environments** to run the checks

## GitHub Actions Configuration

The project uses GitHub Actions to automate CI/CD processes.

### Available Workflows

1. **Nix-based CI** (`nix-ci.yml`):

   - Runs all pre-commit checks
   - Executes all tests
   - Validates Poetry lock file
   - Builds the project with Nix

2. **Frontend CI** (`frontend.yml`):

   - Triggered by changes to the `web_ui` directory
   - Runs linting and type checking
   - Builds the frontend
   - Uploads build artifacts

3. **Dependency Validation** (`nixpkgs-version-check.yml`):

   - Checks that Python dependencies are available in Nixpkgs
   - Triggered by changes to Poetry configuration

4. **Release Management** (`release-please.yml`):
   - Automates version bumping and release notes
   - Creates release pull requests

## Local Development

For day-to-day development, you have several options:

### VS Code Tasks

Use VS Code tasks for common operations:

- **Start Backend Server**: Run the FastAPI server
- **Start Frontend Dev Server**: Run the Vite development server
- **Run Tests**: Execute pytest
- **Format Code**: Run code formatters
- **Lint**: Run linters and type checkers
- **Build Frontend**: Create production frontend build

### Nix Apps (Recommended for Reproducibility)

Use Nix apps for reproducible development that matches CI exactly:

```bash
# Quality checks (same as CI)
nix run .#ci        # Full CI suite
nix run .#precommit # Pre-commit checks only
nix run .#lint      # Linting (Ruff + Pyright + ESLint)
nix run .#format    # Code formatting

# Testing and building
nix run .#test           # Run pytest
nix run .#build-frontend # Build React app
```

### Poetry/npm Commands (Traditional)

Or use traditional package manager commands:

```bash
# Backend
poetry run pytest
poetry run ruff check .
poetry run pyright src

# Frontend (from web_ui/ directory)
npm run dev
npm run build
npm run lint
```

## Adding New Checks

To add new checks to the pre-commit configuration:

1. Add the hook to `.pre-commit-config.yaml`
2. Update the Ruff configuration in `pyproject.toml` if needed
3. Update GitHub Actions workflows if additional CI steps are needed
