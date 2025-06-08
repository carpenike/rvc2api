# Python Backend Instructions

## Technology Stack

- **Python 3.12+** with Poetry dependency management
- **FastAPI** for REST API and WebSocket support
- **Pydantic** for data validation and settings
- **SQLAlchemy** for database ORM (optional persistence feature)
- **pytest** for testing with asyncio support

## Architecture Patterns

### Service-Oriented Architecture
- **Services**: Business logic in `backend/services/` (e.g., `entity_service.py`, `can_service.py`)
- **Models**: Pydantic models in `backend/models/` for data validation
- **API Routers**: FastAPI routers in `backend/api/routers/` organized by domain
- **Core Components**: Configuration, dependencies, state management in `backend/core/`

### Feature Management System
- **Feature Flags**: YAML-driven configuration in `backend/services/feature_flags.yaml`
- **Feature Classes**: Base classes in `backend/services/feature_base.py`
- **Dependency Resolution**: Automatic feature dependency management
- **Environment Override**: Features can be enabled/disabled via environment variables

### Configuration Management
```python
# Environment variables with COACHIQ_ prefix
COACHIQ_SERVER__HOST=0.0.0.0
COACHIQ_SERVER__PORT=8080
COACHIQ_CAN__INTERFACES=can0,can1
COACHIQ_FEATURES__ENABLE_VECTOR_SEARCH=true
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
- **Manager**: `backend/integrations/can/manager.py` handles multiple interfaces
- **Message Factory**: `backend/integrations/can/message_factory.py` creates CAN messages
- **Auto-reconnection**: Built-in retry logic for interface failures

### RV-C Protocol
- **Decoder**: `backend/integrations/rvc/decode.py` handles PGN/SPN decoding
- **Feature Integration**: `backend/integrations/rvc/feature.py` manages RV-C features
- **Configuration**: Uses `config/rvc.json` for protocol specifications

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
```python
# Enable persistence feature via environment variable
COACHIQ_FEATURES__ENABLE_PERSISTENCE=true

# Use repositories for data access
from backend.services.repositories import EntityRepository

async def get_entities():
    repo = EntityRepository()
    return await repo.get_all()
```

## Critical Requirements

- **All Python commands MUST use Poetry**: `poetry run python script.py`
- **Enter Nix shell for system operations**: `nix develop`
- **Use absolute imports only**: `from backend.services.entity_service import EntityService`
- **All API endpoints use `/api/entities`**: Never create separate endpoint patterns like `/api/lights`
- **Comprehensive API documentation**: Include examples, descriptions, and response schemas
