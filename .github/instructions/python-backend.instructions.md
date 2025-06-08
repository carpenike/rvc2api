---
applyTo: "**/backend/**"
---

# Python Backend Architecture

## Technology Stack

- Python 3.12+ with FastAPI and Poetry dependency management
- WebSocket support for real-time communication
- Pydantic for data validation and settings management
- SQLAlchemy ORM for optional persistence features
- Multi-interface CAN bus integration for RV-C protocol
- YAML-driven feature flag system
- Type hints throughout the codebase

## Linting & Code Quality

- **Tool**: Ruff (replacing Flake8, Black, isort)
- **Commands**:
  - Format: `poetry run ruff format backend`
  - Lint: `poetry run ruff check .`
- **Line Length**: 100 characters
- **Type Checking**: Pyright (basic mode)
  - Command: `poetry run pyright backend`
  - Configuration in pyrightconfig.json and pyproject.toml
- **Import Order**: stdlib → third-party → local
- **Line Endings**: LF (Unix style)
- **Verification**: All code must pass linting AND type checking
- **Fix Scripts**: Use VS Code tasks or command-line tools

## Directory Structure

- `backend/`: Main FastAPI application with service-oriented architecture
  - `backend/main.py`: FastAPI application entry point
  - `backend/core/`: Core application components (config, state, dependencies)
  - `backend/services/`: Business logic services (entity, CAN, RV-C, persistence)
  - `backend/api/routers/`: API route definitions organized by domain
  - `backend/websocket/`: WebSocket management and real-time communication
  - `backend/integrations/`: Protocol integrations (CAN, RV-C, Bluetooth)
  - `backend/models/`: Pydantic domain models and data validation
  - `backend/middleware/`: HTTP middleware components
- `typings/`: Custom type stubs for third-party libraries
- `config/`: Configuration files (RV-C specs, coach mappings)

## Design Patterns

- **FastAPI Routes**: Organized by domain in `backend/api/routers/` using APIRouter
- **WebSockets**: Real-time updates in `backend/websocket/` with connection management
- **State Management**: Centralized in `backend/core/state.py`
- **Feature Management**: YAML-driven flags in `backend/services/feature_flags.yaml`
- **Service Architecture**: Business logic in `backend/services/` with dependency injection
- **Configuration**: Environment variables with Pydantic Settings
- **Error Handling**: Structured exceptions with proper logging
- **API Documentation**: Comprehensive docstrings and metadata for OpenAPI schema
  - All endpoints documented with examples and detailed descriptions
  - OpenAPI schema exported to JSON/YAML for use in documentation and type generation
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
  - Check WebSocket handling: `@context7 WebSocket connection management`
  - Review state management: `@context7 backend core state implementation`
  - Find CANbus integration: `@context7 CAN manager and message processing`
  - Check feature flags: `@context7 feature management system`

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
