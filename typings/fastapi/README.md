# FastAPI Type Stubs

This directory contains type stubs for FastAPI to improve type checking and IDE support in the CoachIQ project.

## Organization

The FastAPI type stubs are organized into two primary files:

- `__init__.py` - Implementation file with detailed docstrings
- `__init__.pyi` - Type stub file with concise type definitions

## Design Decisions

1. **Consolidated Structure**: All type stubs are consolidated into these two files instead of spread across multiple files to simplify imports and maintenance.

2. **Complete WebSocket Support**: Special attention is given to WebSocket classes (`WebSocket`, `WebSocketDisconnect`, and `WebSocketException`) since they are critical to the project's functionality.

3. **Non-standard Naming**: The `Body()` function maintains its PascalCase name for compatibility with FastAPI's actual API, despite Python's naming conventions. This is specifically exempted from linting rules in `pyproject.toml`.

## Usage

To use these type stubs in your code, import FastAPI components normally:

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# The type hints will be properly resolved by Pylance/Pyright
```

## Customization

If additional FastAPI components need type definitions:

1. Add the component to `__init__.py` with complete docstrings and implementation details
2. Add corresponding stub definitions to `__init__.pyi`

## Reference

These type stubs are maintained to match FastAPI's actual behavior while providing improved type information for IDE tools and static type checkers.

For more details on type stub organization, see [PEP 561](https://peps.python.org/pep-0561/).
