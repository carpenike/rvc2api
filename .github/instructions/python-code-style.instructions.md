---
applyTo: "**/*.py"
---

# Python Code Style Guidelines

## Linting & Code Quality

- **Python Version**: 3.12+
- **Tool**: Ruff (replacing Flake8, Black, isort)
- **Commands**:
  - Format: `poetry run ruff format backend`
  - Lint: `poetry run ruff check .`
- **Line Length**: 100 characters
- **Type Checking**: Pyright (basic mode)
  - Command: `npx pyright backend`
  - Configuration in pyrightconfig.json and pyproject.toml
- **Import Order**: stdlib → third-party → local
- **Line Endings**: LF (Unix style)
- **Verification**: All code must pass linting AND type checking
- **Fix Scripts**: Use VS Code tasks or command-line tools

## Code Structure

- Use clear module/class/function names that reflect purpose
- Function/method length should generally be ≤ 50 lines
- Classes should follow single responsibility principle
- Use docstrings (Google style) for all public functions, methods and classes
- Include type annotations for all function parameters and returns
- Document API endpoints comprehensively with examples and response schemas

## Import Structure

Organize imports in three sections with a blank line between each:

```python
# Standard library imports
import os
import sys
from typing import Optional, List

# Third-party imports
import fastapi
import pydantic
from fastapi import APIRouter, Depends

# Local imports
from src.common.models import Entity
from backend.core.config import Settings
```

## API Documentation

- **Route Metadata**: Include comprehensive metadata for FastAPI routes:

  ```python
  @router.get(
      "/endpoint",
      response_model=ResponseModel,
      summary="Brief summary",
      description="Detailed description",
      response_description="What the response contains",
      tags=["Category"]
  )
  ```

- **Docstrings**: Include detailed Google-style docstrings with examples:

  ````python
  async def get_entities():
      """
      Get all entities in the system.

      This endpoint provides a list of all entities regardless of their state.

      Returns:
          List[EntityResponse]: A list of entity objects

      Examples:
          ```json
          [
              {
                  "id": "light_123",
                  "name": "Main Light",
                  "type": "light"
              }
          ]
          ```
      """
  ````

- **Response Models**: Define and use Pydantic models for all request/response schemas
- **Generate OpenAPI**: Update OpenAPI schema when changing endpoints (`API: Export OpenAPI Schema` task)

## Best Practices

- Prefer f-strings over other string formatting methods
- Use context managers (`with` statements) for resource cleanup
- Follow SOLID design principles
- Use explicit variable names (avoid single letter names except in loops)
- Use descriptive exceptions with helpful error messages
- Add comments for complex algorithms or business logic
- Limit deeply nested code (extract complex logic to functions)

## Type Annotations

- Use type hints for all function parameters and return values
- Use Union/Optional for parameters that can be None or multiple types
- Create Protocol classes for duck-typing interfaces
- Add custom type stubs in `typings/` for third-party libraries

## MCP Tools for Python Code Style

### @context7 Use Cases - ALWAYS USE FIRST

Always use `@context7` first for any Python-related questions to get current, accurate guidance:

- **Python Typing**: `@context7 Python TypeVar constraints`, `@context7 Protocol implementation`
- **Code Style**: `@context7 FastAPI route organization`, `@context7 Pydantic model style`
- **Best Practices**: `@context7 Python context manager patterns`, `@context7 async function design`

### @perplexity Use Cases - FOR GENERAL CONCEPTS ONLY

Only use `@perplexity` for general concepts not related to specific library APIs:

- Research patterns: `@perplexity Python design patterns for service architecture`
- Investigate general concepts: `@perplexity Python performance optimization`

> **Important**: For any Python, FastAPI, or Pydantic questions, always use `@context7` first to avoid outdated or hallucinated APIs.
