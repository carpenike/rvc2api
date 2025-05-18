---
applyTo: "**/src/**"
---

# Python Backend Architecture

## Technology Stack

- Python 3.12+ with FastAPI
- WebSocket support for real-time communication
- Pydantic for data validation and settings management
- CANbus integration for RV-C protocol
- Type hints throughout the codebase

## Linting & Code Quality

- **Tool**: Ruff (replacing Flake8, Black, isort)
- **Commands**:
  - Format: `poetry run ruff format src`
  - Lint: `poetry run ruff check .`
- **Line Length**: 100 characters
- **Type Checking**: Pyright (basic mode)
  - Command: `npx pyright src`
  - Configuration in pyrightconfig.json and pyproject.toml
- **Import Order**: stdlib → third-party → local
- **Line Endings**: LF (Unix style)
- **Verification**: All code must pass linting AND type checking
- **Fix Scripts**: Use VS Code tasks or command-line tools

## Directory Structure

- `src/common/`: Shared models and utilities
- `src/core_daemon/`: Main FastAPI application
  - `api_routers/`: API route definitions by domain
  - `services/`: Business logic implementations
  - `web_ui/`: Legacy frontend (being migrated to React)
- `src/rvc_decoder/`: DGN decoding, mappings, instance management
- `typings/`: Custom type stubs for third-party libraries

## Design Patterns

- **FastAPI Routes**: Organized by domain in `api_routers/` using APIRouter
- **WebSockets**: Used for real-time updates in `websocket.py`
- **State Management**: Centralized in `app_state.py`
- **Configuration**: Environment variables with Pydantic Settings
- **Error Handling**: Structured exceptions with proper logging
- **Type Stubs**: Custom type stubs in `typings/` for third-party libraries
  - Use Protocol-based implementations for complex interfaces
  - Only include required parts of the API that are actually used

## MCP Tools for Python Backend Development

### @context7 Use Cases - ALWAYS USE FIRST

Always use `@context7` first for any Python library or framework questions to get current, accurate API information:

- **FastAPI Core**: `@context7 FastAPI path parameters validation`, `@context7 FastAPI dependency injection`
- **FastAPI WebSockets**: `@context7 FastAPI WebSocket authentication`, `@context7 FastAPI WebSocket broadcast`
- **Pydantic**: `@context7 Pydantic model with nested objects`, `@context7 Pydantic validators`
- **Python Typing**: `@context7 Python TypeVar constraints`, `@context7 Python Protocol implementation`

- **Project-specific**:
  - Find API implementation: `@context7 entity API router implementation`
  - Check WebSocket handling: `@context7 WebSocket message broadcast`
  - Review state management: `@context7 app_state implementation`
  - Find CANbus integration: `@context7 CAN message processing`

### @perplexity Use Cases - FOR GENERAL CONCEPTS ONLY

Only use `@perplexity` for general concepts not related to specific library APIs:

- Research architectural patterns: `@perplexity API service architecture patterns`
- Investigate protocols: `@perplexity CANbus protocol details`
- Explore design principles: `@perplexity Python service design patterns`

> **Important**: For any FastAPI, Pydantic, or Python language questions, always use `@context7` first to avoid outdated or hallucinated APIs.

## Testing

- **Framework**: pytest
- **Strategy**: Mock CANbus interfaces for isolation
- **Command**: `poetry run pytest` or VS Code task `Backend: Run Tests`
- **Coverage**: Available via `Backend: Run Tests with Coverage` task

## Deployment

The Python backend is deployed as a service on the target system:

- FastAPI application served on configured port
- Environment variables set via config files
- Monitored via built-in health checks
- Logs accessible via standard system logging

## See Also

- [Python Code Style](python-code-style.instructions.md) - Detailed Python coding guidelines
- [VS Code Tasks](vscode-tasks.instructions.md) - Development workflow automation
- [MCP Tools](mcp-tools.instructions.md) - Context-aware AI assistance
- [Pull Request Expectations](pull-requests.instructions.md) - Code submission guidelines
- [Environment Variables](env-vars.instructions.md) - Configuration options
