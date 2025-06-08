# Fix Type Errors

Run comprehensive type checking and fix common issues across the codebase.

## Workflow

1. **Backend Type Checking**
   ```bash
   poetry run pyright backend
   ```

2. **Frontend Type Checking**
   ```bash
   cd frontend && npm run typecheck
   ```

3. **Common Fixes**
   - Add missing type annotations to function parameters and return values
   - Update type stubs in `typings/` directory for third-party libraries
   - Ensure TypeScript interfaces have at least one import statement
   - Fix Pydantic model type annotations

4. **Type Stub Creation**
   - For missing Python library types, create minimal stubs in `typings/`
   - Follow existing patterns in `typings/fastapi/`, `typings/httpx/`
   - Use Protocol-based implementations for complex interfaces

5. **Verification**
   ```bash
   poetry run pyright backend && cd frontend && npm run typecheck
   ```

## Arguments

$ARGUMENTS can specify:
- `backend` - Focus only on Python backend type issues
- `frontend` - Focus only on TypeScript frontend issues
- `stubs` - Focus on creating/updating type stubs
- Specific file paths to target particular files

## Requirements

- All code must pass type checking before commits
- Never use `# type: ignore` without documented justification
- Maintain custom type stubs for project-specific third-party library usage
