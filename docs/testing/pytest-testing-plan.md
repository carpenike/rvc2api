# Comprehensive Pytest Testing Plan for rvc2api Backend

## Overview

This document outlines a comprehensive testing strategy for the rvc2api FastAPI monolithic backend service. The plan is based on pytest best practices and the specific architecture of our RV-C (Recreational Vehicle Controller Area Network) API service.

## Current Test Structure Analysis

### Existing Tests
- `tests/conftest.py` - Basic FastAPI TestClient configuration
- `tests/api/test_feature_flags_integration.py` - Feature flag API endpoint tests
- `tests/services/test_feature_manager.py` - Feature manager service tests
- `tests/integrations/rvc/test_decoder.py` - RV-C decoder integration tests

### Architecture Overview
The backend follows a clean architecture pattern:
- **API Layer**: `backend/api/routers/` - FastAPI endpoints
- **Service Layer**: `backend/services/` - Business logic
- **Core Layer**: `backend/core/` - Configuration, state, dependencies
- **Integration Layer**: `backend/integrations/` - External systems (CAN, RV-C)
- **Models Layer**: `backend/models/` - Pydantic data models
- **WebSocket Layer**: `backend/websocket/` - Real-time communication

## Testing Strategy

### Test Coverage Targets
- **Overall Coverage**: 85-90%
- **API Endpoints**: 95% (critical for user interface)
- **Business Logic Services**: 90% (core functionality)
- **Core Utilities**: 80% (foundational components)
- **Integration Layer**: 70% (external dependencies, harder to test)
- **Models**: 95% (validation logic is critical)

### Test Categories

#### 1. Unit Tests
- **Scope**: Individual functions, classes, and methods
- **Focus**: Business logic, utility functions, model validation
- **Isolation**: Mocked dependencies
- **Speed**: Fast execution (< 100ms per test)

#### 2. Integration Tests
- **Scope**: Multiple components working together
- **Focus**: Service interactions, database operations, external integrations
- **Dependencies**: Real or test doubles of external services
- **Speed**: Medium execution (< 1s per test)

#### 3. API Tests
- **Scope**: HTTP endpoints and WebSocket connections
- **Focus**: Request/response handling, authentication, error cases
- **Setup**: Test client with overridden dependencies
- **Speed**: Medium execution (< 500ms per test)

#### 4. End-to-End Tests
- **Scope**: Complete user workflows
- **Focus**: Critical business processes
- **Setup**: Full application stack
- **Speed**: Slower execution (< 5s per test)

## Detailed Testing Plan by Component

### 1. API Layer Testing (`backend/api/routers/`)

#### Files to Test:
- `entities.py` - Entity CRUD operations
- `can.py` - CAN bus operations
- `config.py` - Configuration management
- `docs.py` - Documentation endpoints

#### Test Structure:
```
tests/api/
├── conftest.py              # API-specific fixtures
├── test_entities.py         # Entity endpoint tests
├── test_can.py             # CAN endpoint tests
├── test_config.py          # Config endpoint tests
├── test_docs.py            # Documentation endpoint tests
└── test_auth.py            # Authentication tests (if applicable)
```

#### Key Test Scenarios:
- **Happy Path**: Valid requests return expected responses
- **Validation Errors**: Invalid input triggers proper error responses
- **Authentication**: Protected endpoints require valid credentials
- **Error Handling**: Proper HTTP status codes and error messages
- **Content Negotiation**: JSON responses with correct content-type
- **Rate Limiting**: API limits are enforced (if applicable)

#### Example Test Pattern:
```python
@pytest.mark.asyncio
async def test_get_entities_success(async_client, mock_entity_service):
    # Arrange
    mock_entities = [{"id": 1, "name": "test"}]
    mock_entity_service.get_all.return_value = mock_entities

    # Act
    response = await async_client.get("/api/entities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"entities": mock_entities}
```

### 2. Service Layer Testing (`backend/services/`)

#### Files to Test:
- `entity_service.py` - Entity business logic
- `can_service.py` - CAN bus service
- `rvc_service.py` - RV-C protocol service
- `config_service.py` - Configuration service
- `feature_manager.py` - Feature flag management

#### Test Structure:
```
tests/services/
├── conftest.py                 # Service-specific fixtures
├── test_entity_service.py      # Entity service tests
├── test_can_service.py        # CAN service tests
├── test_rvc_service.py        # RV-C service tests
├── test_config_service.py     # Config service tests
└── test_feature_manager.py    # Feature manager tests (exists)
```

#### Key Test Scenarios:
- **CRUD Operations**: Create, read, update, delete functionality
- **Business Logic**: Domain-specific rules and validations
- **Error Handling**: Exception handling and error propagation
- **State Management**: Proper state transitions
- **Async Operations**: Correct async/await patterns

### 3. Core Layer Testing (`backend/core/`)

#### Files to Test:
- `config.py` - Configuration management
- `dependencies.py` - FastAPI dependencies
- `entity_manager.py` - Entity management
- `state.py` - Application state

#### Test Structure:
```
tests/core/
├── conftest.py              # Core-specific fixtures
├── test_config.py           # Configuration tests
├── test_dependencies.py     # Dependency injection tests
├── test_entity_manager.py   # Entity manager tests
└── test_state.py           # State management tests
```

#### Key Test Scenarios:
- **Configuration Loading**: Environment variable handling
- **Dependency Injection**: Proper dependency resolution
- **State Management**: Thread-safe state operations
- **Validation**: Configuration validation

### 4. Integration Layer Testing (`backend/integrations/`)

#### Files to Test:
- `rvc/` directory - RV-C protocol integration
- `can/` directory - CAN bus integration

#### Test Structure:
```
tests/integrations/
├── conftest.py              # Integration-specific fixtures
├── rvc/
│   ├── test_decoder.py      # RV-C decoder tests (exists)
│   ├── test_protocol.py     # Protocol handling tests
│   └── test_mappings.py     # DGN mapping tests
└── can/
    ├── test_interface.py    # CAN interface tests
    └── test_bus.py          # CAN bus tests
```

#### Key Test Scenarios:
- **Protocol Decoding**: Correct message interpretation
- **Message Validation**: Proper validation of incoming data
- **Error Recovery**: Handling of malformed messages
- **Performance**: Message processing speed
- **Mocking**: External CAN bus simulation

### 5. Model Layer Testing (`backend/models/`)

#### Files to Test:
- `entities.py` - Entity models
- `can_models.py` - CAN message models
- `config_models.py` - Configuration models

#### Test Structure:
```
tests/models/
├── conftest.py              # Model-specific fixtures
├── test_entities.py         # Entity model tests
├── test_can_models.py       # CAN model tests
└── test_config_models.py    # Config model tests
```

#### Key Test Scenarios:
- **Validation**: Pydantic validation rules
- **Serialization**: JSON serialization/deserialization
- **Type Coercion**: Automatic type conversion
- **Error Messages**: Clear validation error messages

### 6. WebSocket Layer Testing (`backend/websocket/`)

#### Files to Test:
- `handlers.py` - WebSocket connection handlers

#### Test Structure:
```
tests/websocket/
├── conftest.py              # WebSocket-specific fixtures
└── test_handlers.py         # WebSocket handler tests
```

#### Key Test Scenarios:
- **Connection Management**: Connect/disconnect handling
- **Message Broadcasting**: Real-time message distribution
- **Authentication**: WebSocket authentication (if applicable)
- **Error Handling**: Connection error recovery
- **Performance**: Message throughput

## Test Fixtures and Utilities

### Global Fixtures (`tests/conftest.py`)

```python
import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, Mock

from backend.main import app
from backend.core.dependencies import get_entity_service, get_can_service

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_client():
    """Async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def mock_entity_service():
    """Mock entity service for dependency injection."""
    mock = AsyncMock()
    app.dependency_overrides[get_entity_service] = lambda: mock
    yield mock
    app.dependency_overrides.clear()

@pytest.fixture
def mock_can_service():
    """Mock CAN service for dependency injection."""
    mock = AsyncMock()
    app.dependency_overrides[get_can_service] = lambda: mock
    yield mock
    app.dependency_overrides.clear()

@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "id": 1,
        "name": "Test Entity",
        "type": "sensor",
        "properties": {"value": 100}
    }
```

### Test Data Factories

```python
# tests/factories.py
import factory
from backend.models.entities import Entity

class EntityFactory(factory.Factory):
    class Meta:
        model = Entity

    id = factory.Sequence(lambda n: n)
    name = factory.Faker('word')
    type = factory.Iterator(['sensor', 'actuator', 'controller'])
    properties = factory.LazyFunction(lambda: {"value": 100})
```

## Mocking Strategies

### External Dependencies

#### CAN Bus Mocking
```python
@pytest.fixture
def mock_can_bus():
    with patch('backend.integrations.can.interface.CANBus') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance
```

#### RV-C Protocol Mocking
```python
@pytest.fixture
def mock_rvc_decoder():
    with patch('backend.integrations.rvc.decoder.RVCDecoder') as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        yield mock_instance
```

### State Management Mocking
```python
@pytest.fixture
def clean_state():
    """Ensure clean application state for each test."""
    from backend.core.state import ApplicationState
    original_state = ApplicationState._instance
    ApplicationState._instance = None
    yield
    ApplicationState._instance = original_state
```

## Test Configuration

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --cov=backend
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=85
    --asyncio-mode=auto
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    slow: Slow running tests
    can: CAN bus related tests
    websocket: WebSocket tests
```

### Coverage Configuration
```ini
[coverage:run]
source = backend
omit =
    backend/main.py
    backend/*/__init__.py
    backend/*/migrations/*
    tests/*

[coverage:report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

## Test Execution Strategy

### Local Development
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=backend --cov-report=html

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m api

# Run tests for specific modules
poetry run pytest tests/services/
poetry run pytest tests/api/test_entities.py
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml
- name: Run Tests
  run: |
    poetry run pytest --cov=backend --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. ✅ Update `conftest.py` with async client and dependency overrides
2. ✅ Set up proper test configuration (pytest.ini, coverage)
3. ✅ Create test data factories
4. ✅ Implement core mocking utilities

### Phase 2: Core Testing (Week 2-3)
1. **Service Layer Tests**: Complete all service tests with proper mocking
2. **Model Layer Tests**: Comprehensive Pydantic model validation tests
3. **Core Layer Tests**: Configuration, dependencies, and state management

### Phase 3: API Testing (Week 4)
1. **Entity API Tests**: Complete CRUD endpoint testing
2. **CAN API Tests**: CAN bus operation endpoint testing
3. **Config API Tests**: Configuration management endpoints
4. **WebSocket Tests**: Real-time communication testing

### Phase 4: Integration Testing (Week 5)
1. **RV-C Integration Tests**: Protocol decoding and message handling
2. **CAN Integration Tests**: Hardware interface testing with mocks
3. **End-to-End Tests**: Critical user workflow testing

### Phase 5: Performance & Edge Cases (Week 6)
1. **Performance Tests**: Load testing for high-throughput scenarios
2. **Error Condition Tests**: Comprehensive error handling verification
3. **Security Tests**: Authentication and authorization testing
4. **Documentation**: Test documentation and examples

## Success Metrics

### Quantitative Metrics
- **Code Coverage**: Maintain 85%+ overall coverage
- **Test Execution Time**: All tests complete in < 30 seconds
- **Test Reliability**: < 1% flaky test rate
- **Bug Detection**: 90%+ of bugs caught before production

### Qualitative Metrics
- **Test Maintainability**: Easy to update tests when code changes
- **Test Clarity**: Tests serve as documentation
- **Development Velocity**: Tests don't slow down development
- **Confidence**: High confidence in deployments

## Best Practices

### Test Organization
- **One test per behavior**: Each test should verify one specific behavior
- **Descriptive names**: Test names should describe what they verify
- **AAA Pattern**: Arrange, Act, Assert structure
- **Independent tests**: Tests should not depend on each other

### Async Testing
- **Use AsyncClient**: For FastAPI endpoint testing
- **Proper async/await**: Consistent async patterns
- **Event loop management**: Proper fixture scoping

### Mocking Guidelines
- **Mock external dependencies**: CAN bus, file system, network
- **Keep internal logic real**: Don't mock the code under test
- **Use dependency injection**: Override FastAPI dependencies
- **Verify interactions**: Assert that mocks were called correctly

### Test Data Management
- **Use factories**: For consistent test data generation
- **Isolate test data**: Each test should have its own data
- **Clean up**: Ensure no test data leakage between tests

This comprehensive testing plan provides a roadmap for achieving robust test coverage across the entire rvc2api backend service, ensuring reliability, maintainability, and confidence in the codebase.
