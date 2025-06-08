# Code Quality Instructions

## Overview

Comprehensive code quality standards covering formatting, linting, type checking, and documentation for both Python backend and TypeScript frontend.

## Python Backend Quality

### Formatting with Ruff
```bash
# Format code (required before commits)
poetry run ruff format backend

# Check formatting without applying changes
poetry run ruff format backend --check
```

**Standards:**
- **Line Length**: 100 characters
- **Quote Style**: Double quotes preferred
- **Trailing Commas**: Allowed in multi-line structures
- **Import Formatting**: One import per line, grouped and sorted

### Linting with Ruff
```bash
# Run linting (required before commits)
poetry run ruff check .

# Auto-fix issues where possible
poetry run ruff check . --fix

# Show detailed error explanations
poetry run ruff check . --show-source
```

**Configuration (pyproject.toml):**
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]

[tool.ruff.lint.isort]
force-single-line = true
known-first-party = ["backend"]
```

### Type Checking with Pyright
```bash
# Run type checking (required before commits)
poetry run pyright backend

# Check specific files
poetry run pyright backend/services/entity_service.py
```

**Standards:**
- **Type Hints**: Required for all function parameters and return values
- **Generic Types**: Use proper generic typing for collections and protocols
- **Optional Types**: Use `Optional[T]` or `T | None` for nullable values
- **Custom Stubs**: Create type stubs in `typings/` for third-party libraries

**Type Stub Pattern:**
```python
# typings/example_lib/__init__.pyi
from typing import Protocol, TypeVar

T = TypeVar("T")

class AsyncContextManagerProtocol(Protocol[T]):
    async def __aenter__(self) -> T: ...
    async def __aexit__(self, *args) -> None: ...

def some_function(param: str) -> bool: ...
```

### Import Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
import fastapi
from pydantic import BaseModel

# Local imports (absolute only)
from backend.core.config import get_settings
from backend.services.entity_service import EntityService
```

### Documentation Standards
```python
def control_entity(entity_id: str, command: EntityControlCommand) -> EntityControlResult:
    """
    Control an RV-C entity with the specified command.

    Args:
        entity_id: Unique identifier for the entity to control
        command: Control command with action and optional parameters

    Returns:
        Result indicating success/failure and any response data

    Raises:
        EntityNotFoundError: If the entity_id is not found
        CANBusError: If communication with the CAN bus fails

    Example:
        >>> result = control_entity("light_1", EntityControlCommand(command="set", state="on"))
        >>> assert result.success is True
    """
    # Implementation
```

## TypeScript Frontend Quality

### ESLint Configuration
```bash
# Run linting (required before commits)
npm run lint

# Auto-fix issues where possible
npm run lint:fix

# Check specific files
npm run lint src/components/entity-card.tsx
```

**ESLint Rules (eslint.config.js):**
```javascript
export default [
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: "@typescript-eslint/parser",
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true }
      }
    },
    rules: {
      "comma-dangle": ["error", "never"],
      "quotes": ["error", "double"],
      "semi": ["error", "always"],
      "@typescript-eslint/no-unused-vars": "error",
      "react-hooks/exhaustive-deps": "warn"
    }
  }
];
```

### TypeScript Configuration
```bash
# Run type checking (required before commits)
npm run typecheck

# Build check
npm run build
```

**Standards:**
- **Strict Mode**: Enabled in tsconfig.json
- **Interface Requirements**: All standalone interface files must have imports
- **Component Props**: Use proper TypeScript interfaces for component props
- **Event Handlers**: Use proper React event types

**Component Type Pattern:**
```typescript
import type { ReactNode, MouseEvent } from "react";

interface ButtonProps {
  children: ReactNode;
  onClick: (event: MouseEvent<HTMLButtonElement>) => void;
  variant?: "primary" | "secondary";
  disabled?: boolean;
}

export function Button({ children, onClick, variant = "primary", disabled = false }: ButtonProps) {
  return (
    <button
      className={`btn btn-${variant}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
```

### Import Organization
```typescript
// React and React-related imports
import { useState, useEffect, type ReactNode } from "react";

// Third-party library imports
import { useQuery } from "@tanstack/react-query";

// UI component imports
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

// Local component and utility imports
import { EntityCard } from "@/components/entity-card";
import { apiClient } from "@/api/client";
import { cn } from "@/lib/utils";
```

## Pre-commit Hooks

### Configuration (.pre-commit-config.yaml)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.50.0
    hooks:
      - id: eslint
        files: \.(js|ts|tsx)$
        additional_dependencies:
          - eslint@8.50.0
          - "@typescript-eslint/parser@6.7.4"
```

### Running Pre-commit
```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run on all files manually
poetry run pre-commit run --all-files

# Run on specific files
poetry run pre-commit run --files backend/services/entity_service.py
```

## Quality Checklist

### Before Every Commit
```bash
# Backend quality check
poetry run ruff format backend
poetry run ruff check .
poetry run pyright backend

# Frontend quality check
cd frontend
npm run lint:fix
npm run typecheck

# Run tests
poetry run pytest
npm test
```

### Before Pull Requests
```bash
# Comprehensive quality check
poetry run pre-commit run --all-files

# Full test suite
poetry run pytest --cov=backend --cov-report=term
cd frontend && npm run test:coverage

# Build verification
cd frontend && npm run build
```

## Editor Configuration

### VS Code Settings (.vscode/settings.json)
```json
{
  "python.defaultInterpreterPath": "python",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.stubPath": "${workspaceFolder}/typings",
  "python.formatting.provider": "none",
  "editor.formatOnSave": false,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": true,
      "source.organizeImports.ruff": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## Error Resolution Patterns

### Common Python Issues
```python
# Type annotation missing
def process_data(data):  # ❌ Missing type hints
    return data

def process_data(data: dict[str, Any]) -> dict[str, Any]:  # ✅ Proper types
    return data

# Import order violation
from backend.services import EntityService  # ❌ Wrong order
import os  # ❌ Should be first

import os  # ✅ Standard library first
from backend.services import EntityService  # ✅ Local imports last
```

### Common TypeScript Issues
```typescript
// Missing interface import
export interface Props {  // ❌ Standalone interface without import
  children: ReactNode;
}

import type { ReactNode } from "react";  // ✅ Required import
export interface Props {
  children: ReactNode;
}

// Trailing comma violation
const config = {
  apiUrl: "http://localhost:8000",  // ❌ Trailing comma
};

const config = {
  apiUrl: "http://localhost:8000"  // ✅ No trailing comma
};
```

## Performance Considerations

### Python Performance
- Use `ruff` instead of multiple tools (Black, isort, flake8) for speed
- Run type checking only on changed files during development
- Use `.ruff_cache/` for faster subsequent runs

### Frontend Performance
- Use ESLint flat config for better performance
- Enable TypeScript incremental compilation
- Use `npm run lint -- --cache` for faster linting

## Continuous Integration

### GitHub Actions Quality Checks
```yaml
name: Code Quality
on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Python quality
        run: |
          poetry run ruff check .
          poetry run ruff format --check backend
          poetry run pyright backend

      - name: Frontend quality
        run: |
          cd frontend
          npm run lint
          npm run typecheck
          npm run build
```

All quality checks must pass before code can be merged to main branch.
