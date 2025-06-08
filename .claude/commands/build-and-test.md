# Build and Test

Execute a complete build and test cycle for both backend and frontend.

## Full Build and Test Workflow

### 1. Code Quality Pre-check
```bash
# Run all quality checks first
poetry run ruff check . && poetry run pyright backend
cd frontend && npm run lint && npm run typecheck
cd ..
```

### 2. Backend Testing
```bash
# Run backend test suite
poetry run pytest

# With coverage reporting
poetry run pytest --cov=backend --cov-report=term --cov-report=html
```

### 3. Frontend Build and Test
```bash
cd frontend

# Install dependencies (if needed)
npm install

# Run frontend tests
npm test

# Build for production
npm run build

# Verify build output
ls -la dist/
```

### 4. Integration Verification
```bash
# Start backend in test mode
poetry run python run_server.py --test-mode &
BACKEND_PID=$!

# Verify API endpoints respond
curl -f http://localhost:8000/health || exit 1

# Cleanup
kill $BACKEND_PID
```

### 5. Documentation Build
```bash
# Export OpenAPI schema
poetry run python scripts/export_openapi.py

# Build documentation
poetry run mkdocs build

# Verify documentation build
ls -la site/
```

## Build Artifacts

### Frontend Build Output
- `frontend/dist/` - Production build files
- `frontend/dist/index.html` - Entry point
- `frontend/dist/assets/` - Static assets

### Documentation Output
- `site/` - Built documentation site
- `docs/api/openapi.json` - Generated API schema
- `docs/api/openapi.yaml` - YAML API schema

### Test Coverage
- `htmlcov/` - HTML coverage reports
- `coverage.xml` - XML coverage for CI

## Arguments

$ARGUMENTS can specify:
- `--skip-tests` - Build only, skip test execution
- `--coverage` - Include detailed coverage reporting
- `backend-only` - Build and test only backend
- `frontend-only` - Build and test only frontend
- `--clean` - Clean build artifacts before building
- `--production` - Use production build settings

## CI/CD Integration

This workflow matches the CI/CD pipeline steps:
1. Code quality checks
2. Test execution with coverage
3. Production builds
4. Artifact verification

All steps must pass for successful deployment.
