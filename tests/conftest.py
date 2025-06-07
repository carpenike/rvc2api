"""
Global test configuration and fixtures for the rvc2api backend test suite.

This module provides reusable fixtures for testing FastAPI endpoints, services,
and integrations with proper mocking and isolation.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.core.dependencies import (
    get_app_state,
    get_can_service,
    get_config_service,
    get_entity_service,
    get_feature_manager_from_request,
)
from backend.main import app

# Import performance test fixtures
# performance_timer is imported here to make it available as a fixture
# pylint: disable=unused-import
# from tests.conftest_performance import performance_timer


def _setup_test_app_state() -> None:
    """
    Set up minimal app state for testing.
    This ensures that the app.state has the necessary attributes
    that the dependency functions expect.
    """
    if not hasattr(app.state, "feature_manager"):
        # Create basic mocks for app state
        app.state.feature_manager = Mock()
        app.state.feature_manager.is_enabled = Mock(return_value=True)
        app.state.entity_service = Mock()
        app.state.can_service = Mock()
        app.state.config_service = Mock()
        app.state.app_state = Mock()
        app.state.docs_service = Mock()
        app.state.vector_service = Mock()


# ================================
# Event Loop Configuration
# ================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.
    This ensures consistent async behavior across all tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ================================
# HTTP Client Fixtures
# ================================


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """
    Synchronous TestClient fixture for FastAPI.
    Use this for standard API endpoint testing where async is not required.
    """
    _setup_test_app_state()
    with TestClient(app=app, base_url="http://test") as test_client:
        yield test_client


@pytest.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Asynchronous AsyncClient fixture for FastAPI.
    Use this for testing async endpoints, WebSockets, or when you need
    to await client operations directly in your test.
    Note: If you encounter issues with this fixture, ensure httpx is up to date (>=0.23).
    """
    _setup_test_app_state()
    async with AsyncClient() as ac:
        yield ac


# ================================
# Service Mock Fixtures
# ================================


@pytest.fixture
def mock_app_state() -> Mock:
    """
    Mock for the AppState service with common methods.
    Provides a clean mock that can be customized per test.
    """
    mock = Mock()
    mock.get_entity = Mock(return_value=None)
    mock.update_entity = Mock()
    mock.get_all_entities = Mock(return_value=[])
    mock.get_state = Mock(return_value={})
    mock.update_state = Mock()
    return mock


@pytest.fixture
def mock_entity_service() -> AsyncMock:
    """
    Mock for the EntityService with common async methods.
    Use this to mock entity business logic operations.
    """
    mock = AsyncMock()
    mock.list_entities = AsyncMock(return_value={})
    mock.list_entity_ids = AsyncMock(return_value=[])
    mock.get_entity = AsyncMock(return_value=None)
    mock.get_entity_history = AsyncMock(return_value=[])
    mock.get_unmapped_entries = AsyncMock(return_value={})
    mock.get_unknown_pgns = AsyncMock(return_value={})
    mock.get_metadata = AsyncMock(return_value={})
    mock.control_light = AsyncMock()
    return mock


@pytest.fixture
def mock_can_service() -> AsyncMock:
    """
    Mock for the CAN service with common async methods.
    Use this to mock CANbus operations in tests.
    """
    mock = AsyncMock()
    mock.send_message = AsyncMock()
    mock.receive_message = AsyncMock(return_value=None)
    mock.get_status = AsyncMock(return_value={})
    return mock


@pytest.fixture
def mock_config_service() -> Mock:
    """
    Mock for the ConfigService with common methods.
    Use this to mock configuration operations.
    """
    mock = Mock()
    mock.get_config = Mock(return_value={})
    mock.update_config = Mock()
    mock.validate_config = Mock(return_value=True)
    return mock


@pytest.fixture
def mock_feature_manager() -> Mock:
    """
    Mock for the FeatureManager with common methods.
    Use this to mock feature flag operations.
    """
    mock = Mock()
    mock.is_enabled = Mock(return_value=True)
    mock.get_feature = Mock(return_value=None)
    mock.enable_feature = Mock()
    mock.disable_feature = Mock()
    return mock


# ================================
# Dependency Override Fixtures
# ================================


@pytest.fixture
def override_app_state(mock_app_state: Mock) -> Generator[Mock, None, None]:
    """
    Override the app_state dependency with a mock.
    Use this when testing endpoints that depend on app state.
    """
    app.dependency_overrides[get_app_state] = lambda: mock_app_state  # type: ignore[attr-defined]
    yield mock_app_state
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_entity_service(
    mock_entity_service: AsyncMock,
) -> Generator[AsyncMock, None, None]:
    """
    Override the entity_service dependency with a mock.
    Use this when testing endpoints that depend on entity operations.
    """
    app.dependency_overrides[get_entity_service] = lambda: mock_entity_service  # type: ignore[attr-defined]
    yield mock_entity_service
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_can_service(
    mock_can_service: AsyncMock,
) -> Generator[AsyncMock, None, None]:
    """
    Override the can_service dependency with a mock.
    Use this when testing endpoints that depend on CAN operations.
    """
    app.dependency_overrides[get_can_service] = lambda: mock_can_service  # type: ignore[attr-defined]
    yield mock_can_service
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_config_service(mock_config_service: Mock) -> Generator[Mock, None, None]:
    """
    Override the config_service dependency with a mock.
    Use this when testing endpoints that depend on configuration.
    """
    app.dependency_overrides[get_config_service] = lambda: mock_config_service  # type: ignore[attr-defined]
    yield mock_config_service
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_feature_manager(mock_feature_manager: Mock) -> Generator[Mock, None, None]:
    """
    Override the feature_manager dependency with a mock.
    Use this when testing endpoints that depend on feature flags.
    """
    app.dependency_overrides[get_feature_manager_from_request] = lambda: mock_feature_manager  # type: ignore[attr-defined]
    app.state.feature_manager = mock_feature_manager
    yield mock_feature_manager
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_all_services(
    mock_app_state: Mock,
    mock_entity_service: AsyncMock,
    mock_can_service: AsyncMock,
    mock_config_service: Mock,
    mock_feature_manager: Mock,
) -> Generator[dict[str, Mock | AsyncMock], None, None]:
    """
    Override all major service dependencies with mocks.
    Use this for comprehensive endpoint testing.
    """
    app.dependency_overrides.update(
        {
            get_app_state: lambda: mock_app_state,
            get_entity_service: lambda: mock_entity_service,
            get_can_service: lambda: mock_can_service,
            get_config_service: lambda: mock_config_service,
            get_feature_manager_from_request: lambda: mock_feature_manager,
        }
    )  # type: ignore[attr-defined]
    yield {
        "app_state": mock_app_state,
        "entity_service": mock_entity_service,
        "can_service": mock_can_service,
        "config_service": mock_config_service,
        "feature_manager": mock_feature_manager,
    }
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


# ================================
# Test Data Fixtures
# ================================


@pytest.fixture
def sample_entity_data() -> dict[str, int | str | dict[str, int]]:
    """
    Sample entity data for testing.
    Returns a dictionary with typical entity properties.
    """
    return {
        "id": 1,
        "name": "Test Entity",
        "type": "sensor",
        "value": 100,
        "unit": "temperature",
        "properties": {
            "min_value": 0,
            "max_value": 200,
            "precision": 1,
        },
    }


@pytest.fixture
def sample_can_message() -> dict[str, int | list[int] | bool | float]:
    """
    Sample CAN message data for testing.
    Returns a dictionary with typical CAN message properties.
    """
    return {
        "arbitration_id": 0x18FEF100,
        "data": [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08],
        "is_extended_id": True,
        "timestamp": 1234567890.123,
    }


@pytest.fixture
def sample_config_data() -> dict[str, str | dict[str, bool | int]]:
    """
    Sample configuration data for testing.
    Returns a dictionary with typical configuration properties.
    """
    return {
        "can_interface": "can0",
        "log_level": "INFO",
        "features": {
            "entity_discovery": True,
            "can_logging": False,
        },
        "thresholds": {
            "temperature_warning": 80,
            "pressure_critical": 100,
        },
    }


# ================================
# Integration Test Fixtures
# ================================


@pytest.fixture
def mock_can_bus() -> Generator[Mock, None, None]:
    """
    Mock for CAN bus interface operations.
    Use this to mock hardware-level CAN interactions.
    """
    mock_instance = Mock()
    mock_instance.send.return_value = True
    mock_instance.receive.return_value = None
    mock_instance.is_connected.return_value = True
    yield mock_instance


@pytest.fixture
def mock_rvc_decoder() -> Generator[Mock, None, None]:
    """
    Mock for RV-C protocol decoder.
    Use this to mock RV-C message decoding operations.
    """
    mock_instance = Mock()
    mock_instance.decode_message.return_value = {"decoded": True}
    mock_instance.is_valid_message.return_value = True
    yield mock_instance


# ================================
# WebSocket Test Fixtures
# ================================


@pytest.fixture
def websocket_test_client() -> Generator[TestClient, None, None]:
    """
    Test client configured for WebSocket testing.
    Use this for testing WebSocket connections and messaging.
    """
    from starlette.testclient import TestClient as StarletteTestClient

    _setup_test_app_state()
    with StarletteTestClient(app) as client:
        yield client


# ================================
# State Cleanup Fixtures
# ================================


@pytest.fixture(autouse=True)
def clean_app_state() -> Generator[None, None, None]:
    """
    Automatically clean up application state after each test.
    Ensures test isolation by preventing state leakage.
    """
    yield
    # Clean up any global state if needed
    # This is a placeholder for actual state cleanup


@pytest.fixture(autouse=True)
def reset_dependency_overrides() -> Generator[None, None, None]:
    """
    Automatically reset FastAPI dependency overrides after each test.
    Ensures clean dependency injection state.
    """
    yield
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


# ================================
# Pytest Configuration
# ================================


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "can: CAN bus related tests")
    config.addinivalue_line("markers", "websocket: WebSocket tests")
    config.addinivalue_line("markers", "performance: Performance tests")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Automatically mark tests based on their location."""
    for item in items:
        # Add markers based on test file location
        if "test_api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        elif "test_services" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_integrations" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_websocket" in str(item.fspath):
            item.add_marker(pytest.mark.websocket)

        # Mark tests that contain 'can' in their name
        if "can" in item.name.lower():
            item.add_marker(pytest.mark.can)

        # Mark performance tests
        if "performance" in item.name.lower() or "perf" in item.name.lower():
            item.add_marker(pytest.mark.performance)
