---
applyTo: "**/*.py"
---

# Code Style & Documentation

- **Python**: Version 3.12+
- **Format**: `ruff format` (line length: 100)
- **Linting**: `ruff check`
- **Imports**: Group as `stdlib → third-party → local`
- **Typing**: Use full type hints and Pydantic models
- **Code Quality**: All code must pass both linting and type checking

## Linting & Type Checking Configuration

### Ruff

- Follows PEP8 with customizations
- Line length: 100 characters
- Import sorting using isort conventions
- Required for all Python code
- Run: `poetry run ruff check .`

### Ruff Format

- Line length: 100 characters
- Format follows a style similar to Black
- Required for all Python code
- Run: `poetry run ruff format backend`

### Pyright/Pylance

- Type checking mode: basic
- Python version: 3.12
- Custom type stubs in `typings/` directory
- Special handling for FastAPI type annotations
- Run checks in VS Code or with `poetry run pyright backend`

## Code Quality Requirements

### Before Submitting PRs

All code must pass both linting and type checking:

1. **Linting Check**: `poetry run ruff check .`
2. **Type Check**: `poetry run pyright backend`
3. **Formatting**: `poetry run ruff format backend`

### Handling Import Issues

- For third-party libraries without type hints, create stubs in `typings/` directory
- Follow the pattern in existing stubs (e.g., `httpx/__init__.pyi`, `fastapi/__init__.pyi`)
- Use Protocol-based implementations for complex interfaces like AsyncContextManager

### Common Type Stub Patterns

```python
# Example protocol pattern for context managers
from typing import TypeVar, Protocol

T_co = TypeVar("T_co", covariant=True)

class AsyncContextManagerProtocol(Protocol[T_co]):
    async def __aenter__(self) -> T_co: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...
```

## VS Code Configuration

The repository includes VS Code settings to help enforce both linting and type checking:

```json
{
  "python.defaultInterpreterPath": "python",
  "python.analysis.diagnosticMode": "workspace",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.stubPath": "${workspaceFolder}/typings",
  "python.linting.ruffEnabled": true,
  "python.languageServer": "Pylance"
}
```

When dealing with import errors even with proper type stubs:

1. Check that `python.analysis.stubPath` points to `typings/`
2. Try adding problematic modules to `python.analysis.ignore` in settings:
   ```json
   "python.analysis.ignore": ["httpx", "other-problem-module"]
   ```

## MCP Tools for Python Development

### @context7 Use Cases

- Find coding patterns: `@context7 FastAPI route implementation`
- Check API models: `@context7 Pydantic model for entities`
- Review error handling: `@context7 exception handling in can_manager`
- See WebSocket usage: `@context7 WebSocket connection handling`

### @perplexity Use Cases

- Research Python best practices: `@perplexity FastAPI dependency injection patterns`
- Learn about libraries: `@perplexity python-can vs socketcan-python`
- Find optimization techniques: `@perplexity optimizing async Python for embedded systems`

## Docstring Style (PEP 257 or Google-style)

```python
def send_command(command: str) -> bool:
    """
    Sends a command to the CANbus.

    Args:
        command: The command to transmit.

    Returns:
        True if acknowledged, False otherwise.
    """
```

- Include **module-level docstrings** summarizing file purpose.
- Document YAML schemas in comments when used (e.g., `coach_mapping.default.yml`).

## Error Handling

### Runtime Errors

- Catch and log expected exceptions with `logger.exception(...)`
- Avoid `except:` without re-raising or limiting scope
- Use custom error classes for integration-specific faults if needed

### Type Checking Errors

- Always provide proper type annotations for function parameters and return values
- Fix Pyright/Pylance reported errors using type hints or type stubs
- Never use `# type: ignore` unless absolutely necessary and documented with reason
- For third-party libraries without proper type hints:
  1. Create minimal type stubs in `typings/` directory
  2. Include only the parts of the API actually used in the codebase
  3. Document the type stub with source references where appropriate
