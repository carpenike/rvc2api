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

## Task Categories

### Server Tasks

| Task Name                            | Description                             | Command                                     |
| ------------------------------------ | --------------------------------------- | ------------------------------------------- |
| `Server: Start Backend`              | Start the FastAPI backend server        | `poetry run python src/core_daemon/main.py` |
| `Server: Start Frontend Dev Server`  | Start the Vite development server       | `cd web_ui && npm run dev`                  |
| `Server: Start Full Dev Environment` | Start both backend and frontend servers | _Compound task_                             |
| `Server: Serve Documentation`        | Preview documentation with mkdocs serve | `cd docs && mkdocs serve`                   |

### Backend Tasks

| Task Name                          | Description                    | Command                                         |
| ---------------------------------- | ------------------------------ | ----------------------------------------------- |
| `Backend: Run Tests`               | Run pytest tests               | `poetry run pytest`                             |
| `Backend: Run Tests with Coverage` | Run tests with coverage report | `poetry run pytest --cov=src --cov-report=term` |
| `Backend: Format Code (Ruff)`      | Format Python code             | `poetry run ruff format src`                    |
| `Backend: Lint (Ruff)`             | Check code with ruff linter    | `poetry run ruff check .`                       |
| `Backend: Type Check (Pyright)`    | Run Pyright type checker       | `npx pyright src`                               |
| `Backend: Quality Check All`       | Run all code quality checks    | _Compound task_                                 |
| `Backend: Clean`                   | Remove Python cache files      | _Clean script_                                  |

### Frontend Tasks

| Task Name                        | Description                  | Command                               |
| -------------------------------- | ---------------------------- | ------------------------------------- |
| `Frontend: Lint (ESLint)`        | Run ESLint                   | `cd web_ui && npm run lint`           |
| `Frontend: Fix Lint Issues`      | Fix lint issues              | `cd web_ui && npm run lint:fix`       |
| `Frontend: Fix Style Issues`     | Fix style issues             | `cd web_ui && npm run fix:style`      |
| `Frontend: Fix Interface Issues` | Fix interface parsing issues | `cd web_ui && npm run fix:interfaces` |
| `Frontend: Type Check`           | Run TypeScript type checking | `cd web_ui && npm run typecheck`      |
| `Frontend: Quality Check All`    | Run all code quality checks  | _Compound task_                       |
| `Frontend: Clean`                | Remove build artifacts       | _Clean script_                        |

### Build Tasks

| Task Name              | Description         | Command                      |
| ---------------------- | ------------------- | ---------------------------- |
| `Build: Frontend`      | Build the frontend  | `cd web_ui && npm run build` |
| `Build: Documentation` | Build documentation | `cd docs && mkdocs build`    |

### Development Environment Tasks

| Task Name                    | Description                     | Command                      |
| ---------------------------- | ------------------------------- | ---------------------------- |
| `Dev: Enter Nix Shell`       | Enter the Nix development shell | `nix develop`                |
| `Dev: Run Pre-commit Checks` | Run all pre-commit hooks        | `pre-commit run --all-files` |

### MCP Tools Tasks

| Task Name                      | Description                 | Command            |
| ------------------------------ | --------------------------- | ------------------ | --- | ------------------- |
| `MCP: Restart Context7 Server` | Restart the Context7 server | `pkill -f context7 |     | true && context7 &` |

### Dependency Management Tasks

| Task Name               | Description                  | Command                   |
| ----------------------- | ---------------------------- | ------------------------- |
| `Deps: Update Poetry`   | Update Poetry dependencies   | `poetry update`           |
| `Deps: Lock Poetry`     | Lock Poetry dependencies     | `poetry lock --no-update` |
| `Deps: Update Frontend` | Update frontend dependencies | `cd web_ui && npm update` |

### System Status Tasks

| Task Name                 | Description                      | Command         |
| ------------------------- | -------------------------------- | --------------- |
| `Status: Check MCP Tools` | Check MCP tool processes         | _Shell command_ |
| `Status: Backend Info`    | Show Python version and packages | _Shell command_ |

## Customizing Tasks

If you need to modify or add tasks:

1. Edit `.vscode/tasks.json`
2. Follow the existing naming conventions and organization
3. Use appropriate problem matchers for error detection
4. Update this documentation file

## Best Practices

- Use `Server: Start Full Dev Environment` for daily development
- Run code quality tasks before committing changes
- Use `Backend: Quality Check All` and `Frontend: Quality Check All` to ensure all checks pass
- Keep the task configuration clean and organized by category
