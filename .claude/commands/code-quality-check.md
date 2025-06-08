# Code Quality Check

Run comprehensive code quality checks across the entire codebase.

## Full Quality Check Workflow

### 1. Python Backend Quality
```bash
# Formatting check
poetry run ruff format backend --check

# Linting
poetry run ruff check .

# Type checking
poetry run pyright backend
```

### 2. Frontend Quality
```bash
cd frontend

# Linting and formatting
npm run lint

# Type checking
npm run typecheck
```

### 3. Pre-commit Hooks
```bash
poetry run pre-commit run --all-files
```

### 4. Test Suite
```bash
# Backend tests
poetry run pytest

# Frontend tests
cd frontend && npm test
```

## Fix Mode

Add `--fix` argument to automatically fix issues where possible:

### Backend Fixes
```bash
poetry run ruff format backend
poetry run ruff check . --fix
```

### Frontend Fixes
```bash
cd frontend && npm run lint:fix
```

## Quality Standards

### Python Requirements
- **Line Length**: 100 characters
- **Import Order**: stdlib → third-party → local
- **Type Hints**: Required for all functions
- **Docstrings**: Required for public APIs

### TypeScript Requirements
- **Strict Mode**: Enabled
- **No Trailing Commas**: `comma-dangle: ["error", "never"]`
- **Double Quotes**: `quotes: ["error", "double"]`
- **Semicolons**: Required

## Arguments

$ARGUMENTS can specify:
- `--fix` - Automatically fix issues where possible
- `backend` - Run only Python backend checks
- `frontend` - Run only TypeScript frontend checks
- `tests` - Include test suite execution
- `--strict` - Fail on any warnings (CI mode)

## CI/CD Integration

This command mirrors the checks run in CI/CD pipelines. All checks must pass before code can be merged.
