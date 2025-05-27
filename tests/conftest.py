"""
Global test configuration and fixtures for the rvc2api backend test suite.

This module provides reusable fixtures for testing FastAPI endpoints, services,
and integrations with proper mocking and isolation.
"""

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, Mock, patch

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


def _setup_test_app_state():
    """
    Set up minimal app state for testing.
    This ensures that the app.state has the necessary attributes
    that the dependency functions expect.
    """
    if not hasattr(app.state, "feature_manager"):
        from unittest.mock import Mock

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
def event_loop():
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
def client():  # type: ignore[no-untyped-def]
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
    """
    _setup_test_app_state()
    async with AsyncClient() as ac:
        yield ac


# ================================
# Service Mock Fixtures
# ================================


@pytest.fixture
def mock_app_state():
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
def mock_entity_service():
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
def mock_can_service():
    """
    Mock for the CANService with common async methods.
    Use this to mock CAN bus operations.
    """
    mock = AsyncMock()
    mock.send_message = AsyncMock(return_value=True)
    mock.get_status = AsyncMock(return_value={"connected": True})
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    return mock


@pytest.fixture
def mock_config_service():
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
def mock_feature_manager():
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
def override_app_state(mock_app_state):
    """
    Override the app_state dependency with a mock.
    Use this when testing endpoints that depend on app state.
    """
    app.dependency_overrides[get_app_state] = lambda: mock_app_state  # type: ignore[attr-defined]
    yield mock_app_state
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_entity_service(mock_entity_service):
    """
    Override the entity_service dependency with a mock.
    Use this when testing endpoints that depend on entity operations.
    """
    app.dependency_overrides[get_entity_service] = lambda: mock_entity_service  # type: ignore[attr-defined]
    yield mock_entity_service
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_can_service(mock_can_service):
    """
    Override the can_service dependency with a mock.
    Use this when testing endpoints that depend on CAN operations.
    """
    app.dependency_overrides[get_can_service] = lambda: mock_can_service  # type: ignore[attr-defined]
    yield mock_can_service
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_config_service(mock_config_service):
    """
    Override the config_service dependency with a mock.
    Use this when testing endpoints that depend on configuration.
    """
    app.dependency_overrides[get_config_service] = lambda: mock_config_service  # type: ignore[attr-defined]
    yield mock_config_service
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def override_feature_manager(mock_feature_manager):
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
    mock_app_state,
    mock_entity_service,
    mock_can_service,
    mock_config_service,
    mock_feature_manager,
):
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
def sample_entity_data():
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
def sample_can_message():
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
def sample_config_data():
    """
    Sample configuration data for testing.
    Returns a dictionary with typical configuration properties.
    """
    return {
        "can_interface": "vcan0",
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
def mock_can_bus():
    """
    Mock for CAN bus interface operations.
    Use this to mock hardware-level CAN interactions.
    """
    with patch("backend.integrations.can.interface.CANInterface") as mock:
        mock_instance = Mock()
        mock_instance.send.return_value = True
        mock_instance.receive.return_value = None
        mock_instance.is_connected.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_rvc_decoder():
    """
    Mock for RV-C protocol decoder.
    Use this to mock RV-C message decoding operations.
    """
    with patch("backend.integrations.rvc.decoder.RVCDecoder") as mock:
        mock_instance = Mock()
        mock_instance.decode_message.return_value = {"decoded": True}
        mock_instance.is_valid_message.return_value = True
        mock.return_value = mock_instance
        yield mock_instance


# ================================
# WebSocket Test Fixtures
# ================================


@pytest.fixture
def websocket_test_client():
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
def clean_app_state():
    """
    Automatically clean up application state after each test.
    Ensures test isolation by preventing state leakage.
    """
    yield
    # Clean up any global state if needed
    # This is a placeholder for actual state cleanup


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """
    Automatically reset FastAPI dependency overrides after each test.
    Ensures clean dependency injection state.
    """
    yield
    app.dependency_overrides.clear()  # type: ignore[attr-defined]


# ================================
# Performance Test Fixtures
# ================================


@pytest.fixture
def performance_timer():
    """
    Simple performance timer for testing response times.
    Use this to verify that operations complete within expected timeframes.
    """
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def elapsed(self):
            if self.start_time is None or self.end_time is None:
                return None
            return self.end_time - self.start_time

    return Timer()


# ================================
# Pytest Configuration
# ================================


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "can: CAN bus related tests")
    config.addinivalue_line("markers", "websocket: WebSocket tests")
    config.addinivalue_line("markers", "performance: Performance tests")


def pytest_collection_modifyitems(config, items):
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
