# Python Backend Instructions

## Technology Stack

- **Python 3.12+** with Poetry dependency management
- **FastAPI** for REST API and WebSocket support
- **Pydantic** for data validation and settings
- **SQLAlchemy** for database ORM (optional persistence feature)
- **pytest** for testing with asyncio support

## Architecture Patterns

### Management Services (REQUIRED)
All backend code MUST use the following management services for consistency and maintainability:

#### Core Management Services
- **FeatureManager** (`backend/services/feature_manager.py`): Register and manage all features, handle dependencies
- **EntityManager** (`backend/core/entity_manager.py`): Unified entity registration, state management, device lookups
- **AppState** (`backend/core/state.py`): Core application state management, entity tracking, metrics
- **DatabaseManager** (`backend/services/database_manager.py`): Database connections, health checks, migrations
- **PersistenceService** (`backend/services/persistence_service.py`): Data persistence, backup operations
- **ConfigService** (`backend/services/config_service.py`): Configuration retrieval, validation, environment variables

#### Service Access Pattern
```python
# ALWAYS access services through dependency injection
from backend.core.dependencies import (
    get_feature_manager, get_entity_manager, get_app_state,
    get_database_manager, get_persistence_service, get_config_service
)

@router.get("/entities")
async def get_entities(
    entity_manager: EntityManager = Depends(get_entity_manager),
    app_state: AppState = Depends(get_app_state)
):
    """Use EntityManager for entity operations, AppState for runtime state."""
    entities = entity_manager.get_all_entities()
    return entities
```

#### Feature Registration Pattern
```python
# ALL features must extend Feature base class and register with FeatureManager
from backend.services.feature_base import Feature
from backend.services.feature_manager import FeatureManager

class MyFeature(Feature):
    def __init__(self, friendly_name: str = "My Feature"):
        super().__init__(friendly_name)

    async def start(self) -> None:
        """Initialize feature resources."""
        pass

    async def stop(self) -> None:
        """Cleanup feature resources."""
        pass

# Register in feature_manager.py
feature_manager = FeatureManager()
feature_manager.register_feature("my_feature", MyFeature())
```

### Service-Oriented Architecture
- **Domain Services**: Business logic in `backend/services/` (e.g., `entity_service.py`, `can_service.py`)
- **Models**: Pydantic models in `backend/models/` for data validation
- **API Routers**: FastAPI routers in `backend/api/routers/` organized by domain
- **Core Components**: Management services in `backend/core/` and `backend/services/`

### Feature Management System
- **Feature Flags**: YAML-driven configuration in `backend/services/feature_flags.yaml`
- **Feature Manager**: Centralized feature lifecycle management via `FeatureManager`
- **Feature Classes**: ALL features must extend `Feature` base class
- **Dependency Resolution**: Automatic feature dependency management
- **Environment Override**: Features can be enabled/disabled via environment variables

### Configuration Management
```python
# ALWAYS use ConfigService for configuration access
config_service: ConfigService = Depends(get_config_service)
config = await config_service.get_config_summary()

# Environment variables with COACHIQ_ prefix
COACHIQ_SERVER__HOST=0.0.0.0
COACHIQ_SERVER__PORT=8080
COACHIQ_CAN__INTERFACES=can0,can1
COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=true
```

### Domain-Specific Services (Use When Appropriate)
These services handle specific business domains and should be used via dependency injection:

- **EntityService**: RV-C entity operations, state management, light control
- **CANService**: CAN bus operations, interface monitoring, message sending
- **RVCService**: RV-C protocol-specific operations, message translation
- **DashboardService**: Dashboard data aggregation, activity feeds, bulk operations
- **WebSocketManager**: Client connection management, real-time broadcasting

```python
# Example domain service usage
from backend.core.dependencies import get_entity_service, get_can_service

@router.post("/entities/{entity_id}/command")
async def control_entity(
    entity_id: str,
    command: EntityCommand,
    entity_service: EntityService = Depends(get_entity_service),
    can_service: CANService = Depends(get_can_service)
):
    """Use EntityService for entity logic, CANService for CAN operations."""
    result = await entity_service.control_entity(entity_id, command)
    return result
```

## Code Quality Requirements

### Formatting and Linting
```bash
# Required before all commits
poetry run ruff format backend
poetry run ruff check .
poetry run pyright backend
```

### Standards
- **Line Length**: 100 characters
- **Import Order**: stdlib → third-party → local (absolute imports only)
- **Type Hints**: Required for all function parameters and return values
- **Docstrings**: Required for public APIs using Google-style format

### Type Checking
- **Tool**: Pyright in basic mode
- **Custom Stubs**: Create in `typings/` for third-party libraries without type hints
- **Pattern**: Use Protocol-based implementations for complex interfaces

## API Development Patterns

### Entity Control Commands
```python
# Standard entity control command structure
{
    "command": "set",       # Required: set, toggle, brightness_up, brightness_down
    "state": "on",         # Optional: on, off
    "brightness": 75       # Optional: 0-100
}
```

### FastAPI Route Structure
```python
from fastapi import APIRouter, Depends
from backend.core.dependencies import get_entity_service
from backend.models.entity import EntityResponse

router = APIRouter(prefix="/api/entities", tags=["entities"])

@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    entity_service: EntityService = Depends(get_entity_service)
) -> EntityResponse:
    """Get entity by ID with comprehensive documentation."""
    return await entity_service.get_entity(entity_id)
```

### WebSocket Patterns
```python
from fastapi import WebSocket
from backend.websocket.handlers import ConnectionManager

manager = ConnectionManager()

@app.websocket("/ws/entities")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

## Integration Patterns

### CAN Bus Integration
**REQUIRED**: Always use CANService and CANInterfaceService for CAN operations:
```python
# Use services, not direct integration access
can_service: CANService = Depends(get_can_service)
can_interface_service: CANInterfaceService = Depends(get_can_interface_service)

# Get CAN status through service
status = await can_service.get_status()
# Resolve interfaces through service
interface = can_interface_service.resolve_interface("logical_name")
```
- **Manager**: `backend/integrations/can/manager.py` (accessed via CANService)
- **Message Factory**: `backend/integrations/can/message_factory.py` (used by services)
- **Auto-reconnection**: Built-in retry logic for interface failures

### RV-C Protocol
**REQUIRED**: Always use RVCService for RV-C operations:
```python
# Use RVCService for protocol operations
rvc_service: RVCService = Depends(get_rvc_service)
await rvc_service.start()  # Proper lifecycle management
```
- **Decoder**: `backend/integrations/rvc/decode.py` (accessed via RVCService)
- **Feature Integration**: `backend/integrations/rvc/feature.py` (registered with FeatureManager)
- **Configuration**: Uses `config/rvc.json` for protocol specifications (via ConfigService)

## Testing Patterns

### pytest Configuration
```python
# Use pytest with asyncio support
import pytest
from backend.core.config import get_settings

@pytest.fixture
async def mock_can_interface():
    """Mock CAN interface for testing."""
    # Implementation

@pytest.mark.asyncio
async def test_entity_control(mock_can_interface):
    """Test entity control with mocked CAN interface."""
    # Test implementation
```

### Test Structure
- **Location**: `tests/` directory with domain-based organization
- **Factories**: Use `tests/factories.py` for test data creation
- **Mocking**: Mock CAN interfaces and external dependencies
- **Coverage**: Aim for >80% coverage on business logic

## MCP Tools for Backend Development

### Always Use @context7 First
- **FastAPI Questions**: `@context7 FastAPI dependency injection patterns`
- **Pydantic Models**: `@context7 Pydantic model with nested validation`
- **Python Typing**: `@context7 Python Protocol implementation`
- **WebSocket Handling**: `@context7 FastAPI WebSocket broadcast patterns`

### Project Context
- **Find Implementations**: `@context7 entity service implementation`
- **Check Patterns**: `@context7 CAN message processing patterns`
- **Review Configuration**: `@context7 feature flag configuration`

## Common Development Tasks

### Adding New Features
1. Define feature in `backend/services/feature_flags.yaml`
2. Create feature class inheriting from `FeatureBase` in `backend/services/`
3. Register feature in `backend/services/feature_manager.py`
4. Add feature dependencies if needed
5. Implement feature-specific services and models

### Adding API Endpoints
1. Create router in `backend/api/routers/`
2. Define Pydantic models in `backend/models/`
3. Implement service logic in `backend/services/`
4. Add comprehensive docstrings for OpenAPI generation
5. Write tests in corresponding `tests/` subdirectory
6. Update router configuration in `backend/api/router_config.py`

### Database Integration (Optional Persistence Feature)
**REQUIRED**: Always use DatabaseManager and PersistenceService for database operations:
```python
# Enable persistence feature via environment variable
COACHIQ_FEATURES__ENABLE_PERSISTENCE=true

# Use DatabaseManager for connections
database_manager: DatabaseManager = Depends(get_database_manager)
session = await database_manager.get_session()

# Use PersistenceService for data operations
persistence_service: PersistenceService = Depends(get_persistence_service)
backup_result = await persistence_service.backup_database()

# Use repositories with proper dependency injection
from backend.services.repositories import EntityRepository, ConfigRepository

async def get_entities(db_manager: DatabaseManager = Depends(get_database_manager)):
    repo = EntityRepository(db_manager)
    return await repo.get_all()
```

## Nix Flake (Optional)

### Nix Development Environment
The project includes an optional Nix flake (`flake.nix`) that provides:
- **Reproducible development environment** with all Python dependencies
- **CLI apps** accessible via `nix run`:
  - `nix run .#test` - Run unit tests
  - `nix run .#lint` - Run linters (ruff, pyright)
  - `nix run .#format` - Format code
  - `nix run .#ci` - Full CI suite
  - `nix run .#build-frontend` - Build frontend
- **NixOS module** for production deployment
- **Automatic frontend setup** when entering nix shell

**Note**: Nix is optional. All commands work with standard Poetry and npm tooling.

## Environment Configuration

### Configuration Pattern
All environment variables follow the `COACHIQ_` prefix pattern:
```bash
# Top-level settings
COACHIQ_APP_NAME=CoachIQ
COACHIQ_ENVIRONMENT=development

# Nested settings (double underscore for nesting)
COACHIQ_SERVER__HOST=127.0.0.1
COACHIQ_SERVER__PORT=8000
COACHIQ_CAN__INTERFACES=virtual0
COACHIQ_FEATURES__ENABLE_PERSISTENCE=true
```

### Key Configuration Sections
1. **Server Configuration**: `COACHIQ_SERVER__*`
2. **CAN Bus Settings**: `COACHIQ_CAN__*`
3. **Feature Flags**: `COACHIQ_FEATURES__*`
4. **Persistence**: `COACHIQ_PERSISTENCE__*`
5. **Database**: `COACHIQ_DATABASE__*`
6. **Security**: `COACHIQ_SECURITY__*`
7. **Logging**: `COACHIQ_LOGGING__*`

### Persistence Modes
```bash
# 1. Memory-only (default - no persistence)
COACHIQ_PERSISTENCE__ENABLED=false

# 2. Development (local file storage)
COACHIQ_PERSISTENCE__ENABLED=true
COACHIQ_PERSISTENCE__DATA_DIR=backend/data

# 3. Production (system directory)
COACHIQ_PERSISTENCE__ENABLED=true
COACHIQ_PERSISTENCE__DATA_DIR=/var/lib/coachiq
```

### Configuration Loading Order
1. Default values in Pydantic Settings classes
2. Values from `.env` file
3. Environment variables (override everything)

**IMPORTANT**: Always use ConfigService to access configuration:
```python
config_service: ConfigService = Depends(get_config_service)
config = await config_service.get_config_summary()
```

## Critical Requirements

### Management Service Usage (MANDATORY)
- **ALWAYS use FeatureManager for feature registration**: Never directly instantiate features
- **ALWAYS use EntityManager for entity operations**: Never access entities directly from AppState
- **ALWAYS use ConfigService for configuration**: Never access settings directly
- **ALWAYS use DatabaseManager for database operations**: Never create direct SQLAlchemy sessions
- **ALWAYS use dependency injection**: Access services via `backend.core.dependencies`

### Development Standards
- **All Python commands MUST use Poetry**: `poetry run python script.py`
- **Use absolute imports only**: `from backend.services.entity_service import EntityService`
- **All API endpoints use `/api/entities`**: Never create separate endpoint patterns like `/api/lights`
- **Comprehensive API documentation**: Include examples, descriptions, and response schemas

### Service Dependency Examples
```python
# CORRECT: Use dependency injection
@router.get("/status")
async def get_status(
    feature_manager: FeatureManager = Depends(get_feature_manager),
    entity_manager: EntityManager = Depends(get_entity_manager)
):
    features = feature_manager.get_enabled_features()
    entities = entity_manager.get_all_entities()
    return {"features": features, "entities": entities}

# WRONG: Direct service access
from backend.services.feature_manager import feature_manager  # DON'T DO THIS
```
