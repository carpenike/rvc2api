---
applyTo: "**"
---

# VS Code Tasks

This file documents the VS Code tasks configuration for the `rvc2api` project. Tasks are configured in `.vscode/tasks.json` and provide shortcuts for common development operations.

## How to Use Tasks

- Open the Command Palette (Ctrl+Shift+P or ⌘+Shift+P on macOS)
- Type "Tasks: Run Task" and select the desired task
- Alternatively, use the shortcut Ctrl+Shift+B or ⌘+Shift+B on macOS to run the default build task
- Tasks can also be run from the Terminal menu → Run Task

## Task Organization

Tasks are organized into logical categories with clear naming conventions:

- **Server Tasks**: Development servers and documentation
- **Daily Development Tasks**: Fast Poetry/npm-based tasks for quick iterations
- **CI/Reproducible Tasks**: Nix-based tasks that match CI environment exactly
- **Build Tasks**: Production builds
- **Frontend Tasks**: Individual frontend development tasks
- **Development Environment**: Environment setup and maintenance
- **Dependency Management**: Package management
- **API and Documentation**: Schema and docs generation
- **System and vCAN**: Low-level system tasks
- **MCP and Status**: Tooling status and management

## Development Workflow Recommendations

### For Daily Development (Fast Iteration)
Use the "Dev:" prefixed tasks for quick feedback:
- `Dev: Run Tests (Quick)` - Fast Poetry-based test runs
- `Dev: Format Code (Quick)` - Quick Ruff formatting
- `Dev: Lint Backend (Quick)` - Fast linting
- `Dev: Run Pre-commit (Quick)` - Quick pre-commit checks

### For CI Parity and Release Prep
Use the "CI:" prefixed tasks to match the exact CI environment:
- `CI: Run Tests (Nix)` - Reproducible test environment
- `CI: Run Linters (Nix)` - Full linting suite
- `CI: Format Code (Nix)` - Full formatting (backend + frontend)
- `CI: Run Pre-commit (Nix)` - Exact CI pre-commit environment
- `CI: Full Suite (Nix)` - Complete CI reproduction

## Task Categories

### Server Tasks

| Task Name                            | Description                             | Command                                     |
| ------------------------------------ | --------------------------------------- | ------------------------------------------- |
| `Server: Start Backend`              | Start the FastAPI backend server        | `poetry run python run_server.py` |
| `Server: Start Frontend Dev Server`  | Start the Vite development server       | `cd web_ui && npm run dev`                  |
| `Server: Start Full Dev Environment` | Start both backend and frontend servers | _Compound task_                             |
| `Server: Serve Documentation`        | Preview documentation with mkdocs serve | `poetry run mkdocs serve`                   |

### Daily Development Tasks (Fast)

| Task Name                      | Description                    | Command                                         |
| ------------------------------ | ------------------------------ | ----------------------------------------------- |
| `Dev: Run Tests (Quick)`       | Fast pytest tests               | `poetry run pytest`                             |
| `Dev: Run Tests with Coverage` | Tests with coverage report | `poetry run pytest --cov=backend --cov-report=term` |
| `Dev: Format Code (Quick)`     | Quick Python formatting       | `poetry run ruff format src`                    |
| `Dev: Lint Backend (Quick)`    | Quick backend linting          | `poetry run ruff check .`                       |
| `Dev: Type Check (Quick)`      | Quick type checking            | `poetry run pyright src`                        |
| `Dev: Run Pre-commit (Quick)`  | Quick pre-commit checks        | `poetry run pre-commit run --all-files`         |

### CI/Reproducible Tasks (Nix)

| Task Name                   | Description                             | Command                       |
| --------------------------- | --------------------------------------- | ----------------------------- |
| `CI: Run Tests (Nix)`       | Tests in reproducible environment       | `nix run .#test`              |
| `CI: Run Linters (Nix)`     | Full linting suite (backend + frontend) | `nix run .#lint`              |
| `CI: Format Code (Nix)`     | Full formatting (backend + frontend)    | `nix run .#format`            |
| `CI: Run Pre-commit (Nix)`  | Pre-commit in CI environment            | `nix run .#precommit`         |
| `CI: Full Suite (Nix)`      | Complete CI reproduction                 | `nix run .#ci`                |

### Build Tasks

| Task Name                  | Description                               | Command                       |
| -------------------------- | ----------------------------------------- | ----------------------------- |
| `Build: Frontend (npm)`    | Build frontend with npm                   | `cd web_ui && npm run build`  |
| `Build: Frontend (Nix)`    | Build frontend in reproducible environment | `nix run .#build-frontend`    |
| `Build: Documentation`     | Build MkDocs documentation               | `poetry run mkdocs build`     |

### Frontend Tasks

| Task Name                        | Description                  | Command                               |
| -------------------------------- | ---------------------------- | ------------------------------------- |
| `Frontend: Lint (ESLint)`        | Run ESLint                   | `cd web_ui && npm run lint`           |
| `Frontend: Fix Lint Issues`      | Fix lint issues              | `cd web_ui && npm run lint:fix`       |
| `Frontend: Fix Style Issues`     | Fix style issues             | `cd web_ui && npm run fix:style`      |
| `Frontend: Fix Interface Issues` | Fix interface parsing issues | `cd web_ui && npm run fix:interfaces` |
| `Frontend: Type Check`           | Run TypeScript type checking | `cd web_ui && npm run typecheck`      |
| `Frontend: Clean`                | Remove build artifacts       | _Clean script_                        |

### Development Environment

| Task Name                 | Description                    | Command                   |
| ------------------------- | ------------------------------ | ------------------------- |
| `Dev: Enter Nix Shell`    | Enter Nix development shell    | `nix develop`             |
| `Dev: Clean All`          | Remove all cache files         | _Clean script_            |

### Dependency Management

| Task Name               | Description                  | Command                   |
| ----------------------- | ---------------------------- | ------------------------- |
| `Deps: Update Poetry`   | Update Poetry dependencies   | `poetry update`           |
| `Deps: Lock Poetry`     | Lock Poetry dependencies     | `poetry lock --no-update` |
| `Deps: Update Frontend` | Update frontend dependencies | `cd web_ui && npm update` |

### API and Documentation Tasks

| Task Name                    | Description                              | Command                                                                  |
| ---------------------------- | ---------------------------------------- | ------------------------------------------------------------------------ |
| `API: Export OpenAPI Schema` | Export OpenAPI schema to JSON/YAML files | `poetry run python scripts/export_openapi.py`                            |
| `API: Update Documentation`  | Export OpenAPI schema and rebuild docs   | `poetry run python scripts/export_openapi.py && poetry run mkdocs build` |

### Documentation Tasks

| Task Name                           | Description                      | Command                        |
| ----------------------------------- | -------------------------------- | ------------------------------ |
| `Docs: List Versions`               | List available doc versions      | `./scripts/docs_version.sh list` |
| `Docs: Deploy Current Version`      | Deploy current version           | `./scripts/docs_version.sh deploy` |
| `Docs: Deploy Dev Version`          | Deploy development version       | `./scripts/docs_version.sh deploy-dev` |
| `Docs: Set Default Version`         | Set default documentation version | `./scripts/docs_version.sh set-default` |
| `Docs: Serve Versioned Documentation` | Serve versioned documentation   | `./scripts/docs_version.sh serve` |

### System and vCAN Tasks

| Task Name                       | Description                            | Command                                |
| ------------------------------- | -------------------------------------- | -------------------------------------- |
| `System: Setup Colima vcan`     | Set up vcan interfaces in Colima VM   | `scripts/setup_colima_vcan.sh`        |
| `System: Ensure vcan Interfaces` | Ensure vcan interfaces are available  | `scripts/ensure_vcan_interfaces.sh`   |
| `System: Test vCAN Setup`       | Test vCAN setup by sending/receiving  | `poetry run python dev_tools/test_vcan_setup.py` |

### MCP and Status Tasks

| Task Name                      | Description                      | Command                    |
| ------------------------------ | -------------------------------- | -------------------------- |
| `MCP: Restart Context7 Server` | Restart the Context7 server     | `pkill -f context7 \|\| true; context7 &` |
| `Status: Check MCP Tools`      | Check MCP tool processes         | _Process check script_     |
| `Status: Backend Info`         | Show Python version and packages | _Version and package info_ |

## Customizing Tasks

If you need to modify or add tasks:

1. Edit `.vscode/tasks.json`
2. Follow the existing naming conventions and organization
3. Use appropriate problem matchers for error detection
4. Update this documentation file

## Best Practices

### Daily Development Workflow
1. Use `Server: Start Full Dev Environment` to start both backend and frontend
2. Use "Dev:" prefixed tasks for quick feedback during development:
   - `Dev: Run Tests (Quick)` for fast test runs
   - `Dev: Format Code (Quick)` for quick formatting
   - `Dev: Lint Backend (Quick)` for fast linting
   - `Dev: Run Pre-commit (Quick)` before committing

### CI Parity and Release Preparation
1. Use "CI:" prefixed tasks to ensure your code matches the CI environment:
   - `CI: Run Tests (Nix)` for reproducible test environment
   - `CI: Run Linters (Nix)` for full linting suite (backend + frontend)
   - `CI: Full Suite (Nix)` for complete CI reproduction
2. Always run CI tasks before opening pull requests

### Code Quality
- Run pre-commit checks before committing changes
- Use both quick (Poetry/npm) and reproducible (Nix) versions based on context
- Keep task configuration clean and organized by category
- Frontend tasks handle TypeScript, ESLint, and interface fixes

### Environment Management
- Use `Dev: Enter Nix Shell` for reproducible development environment
- Use system tasks to set up vCAN interfaces for testing
- Monitor MCP tools status for optimal development experience

## Important: JSON Compliance

VS Code configuration files (`.vscode/tasks.json`, `.vscode/launch.json`, etc.) must be valid JSON:

- **No Comments**: JSON files cannot contain `//` comments, even though VS Code editor may display them
- **Pre-commit Validation**: Our pre-commit hooks validate JSON syntax and will fail if comments are present
- **File Extensions**: Use `.jsonc` for JSON with comments, or `.json` for strict JSON compliance

### Common Issues

1. **Comments in JSON**: Remove all `// comment` lines from `.vscode/tasks.json`
2. **Trailing Commas**: Ensure no trailing commas in JSON objects/arrays
3. **Syntax Validation**: Use `python -m json.tool file.json` to validate JSON syntax

### Example Fix
```diff
- // This is a comment that breaks JSON compliance
{
  "version": "2.0.0",
  "tasks": [
    // ...existing tasks...
  ]
}
