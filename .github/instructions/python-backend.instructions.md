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

### Management Service Patterns (MANDATORY)

**ALL backend code MUST follow these service patterns:**

#### Core Management Services Access

```python
# ALWAYS use dependency injection for management services
from backend.core.dependencies import (
    get_feature_manager, get_entity_manager, get_app_state,
    get_database_manager, get_persistence_service, get_config_service
)

@router.get("/api/status")
async def get_system_status(
    feature_manager: FeatureManager = Depends(get_feature_manager),
    entity_manager: EntityManager = Depends(get_entity_manager),
    config_service: ConfigService = Depends(get_config_service)
):
    """Use management services for system operations."""
    features = feature_manager.get_enabled_features()
    entities = entity_manager.get_all_entities()
    config = await config_service.get_config_summary()
    return {"features": features, "entities": entities, "config": config}
```

#### Feature Registration Pattern

```python
# ALL new features must extend Feature base class
from backend.services.feature_base import Feature

class MyNewFeature(Feature):
    def __init__(self, friendly_name: str = "My New Feature"):
        super().__init__(friendly_name)

    async def start(self) -> None:
        """Initialize feature resources."""
        pass

    async def stop(self) -> None:
        """Cleanup feature resources."""
        pass

# Register with FeatureManager in feature_manager.py
feature_manager.register_feature("my_new_feature", MyNewFeature())
```

### Standard Design Patterns

- **FastAPI Routes**: Organized by domain in `backend/api/routers/` using APIRouter
- **Management Services**: ALWAYS access via dependency injection (FeatureManager, EntityManager, etc.)
- **Domain Services**: Business logic services accessed via dependency injection
- **WebSockets**: Use WebSocketManager feature for real-time updates
- **State Management**: Use AppState and EntityManager for centralized state
- **Feature Management**: YAML-driven flags with FeatureManager lifecycle management
- **Configuration**: Use ConfigService for all configuration access
- **Database Operations**: Use DatabaseManager and PersistenceService
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

- **Project-specific Management Services**:
  - Find service implementations: `@context7 FeatureManager implementation patterns`
  - Check entity management: `@context7 EntityManager entity operations`
  - Review configuration access: `@context7 ConfigService usage patterns`
  - Find database operations: `@context7 DatabaseManager connection handling`
  - Check persistence services: `@context7 PersistenceService backup operations`
  - Review dependency injection: `@context7 backend core dependencies implementation`
  - Find WebSocket handling: `@context7 WebSocketManager connection management`
  - Check state management: `@context7 AppState entity tracking`
  - Find CANbus integration: `@context7 CANService interface management`
  - Check feature registration: `@context7 feature management system registration`

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

## Environment Configuration

### Configuration Pattern

All environment variables use the `COACHIQ_` prefix:

- **Top-level settings**: `COACHIQ_APP_NAME`, `COACHIQ_ENVIRONMENT`
- **Nested settings**: `COACHIQ_SERVER__HOST`, `COACHIQ_CAN__INTERFACES`

### Configuration Files

- **`.env.example`**: Complete documentation of all available settings
- **`.env`**: Active configuration (gitignored)
- **`backend/core/config.py`**: Pydantic Settings with type validation

### Management Service Access for Configuration

```python
# ALWAYS use ConfigService for configuration access
from backend.core.dependencies import get_config_service

@router.get("/config/summary")
async def get_config_summary(
    config_service: ConfigService = Depends(get_config_service)
):
    """Access configuration through ConfigService."""
    return await config_service.get_config_summary()
```

### Key Configuration Sections

- **Server**: `COACHIQ_SERVER__*` (host, port, workers, SSL)
- **CAN Bus**: `COACHIQ_CAN__*` (interfaces, bustype, mappings)
- **Features**: `COACHIQ_FEATURES__*` (enable/disable features)
- **Persistence**: `COACHIQ_PERSISTENCE__*` (data storage settings)
- **Database**: `COACHIQ_DATABASE__*` (backend, connection settings)

## Nix Development Environment (Optional)

### Nix CLI Apps (if using Nix)

```bash
# Nix provides these CLI apps
nix run .#test      # Run tests
nix run .#lint      # Run linters
nix run .#format    # Format code
nix run .#ci        # Full CI suite
```

### Nix Flake Benefits (if used)

- **Reproducible environment**: Same setup across all developers
- **Python 3.12**: Consistent Python version
- **Automatic library paths**: Poetry works without manual LD_LIBRARY_PATH
- **Included tools**: pyright, ruff, nodejs for full-stack development
- **NixOS module**: Production deployment configuration

**Note**: Nix is optional. All standard Poetry commands work without Nix.

### NixOS Production Deployment

```nix
# In your system flake:
inputs.coachiq.url = "github:carpenike/coachiq";

# Enable the service:
coachiq.enable = true;
coachiq.settings = {
  server.host = "0.0.0.0";
  server.port = 8080;
  persistence.enabled = true;
  canbus.interfaces = ["can0", "can1"];
};
```

## Deployment

The Python backend can be deployed in multiple ways:

### Development Deployment

- Use `.env` file for configuration
- Run with `poetry run python run_server.py`
- Virtual CAN interfaces for testing

### Production Deployment (NixOS)

- Use NixOS module from flake
- Systemd service with automatic restart
- Environment variables set via Nix configuration
- Persistent data in `/var/lib/coachiq`

### Production Deployment (Traditional)

- Use systemd service file
- Set environment variables in service configuration
- Enable persistence with system directories
- Configure real CAN interfaces
