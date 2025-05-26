import pytest
from fastapi.testclient import TestClient  # Added
from httpx import AsyncClient

# Assuming 'app' is the FastAPI instance from your main application module
# and 'app_state' and 'can_manager' are objects accessible from that module's scope
# or are attributes of the 'app' instance itself.
from backend.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    """
    Synchronous TestClient fixture for FastAPI.
    Use this for standard API endpoint testing.
    """
    with TestClient(app=app, base_url="http://test") as c:
        yield c


@pytest.fixture(scope="session")
async def async_client() -> AsyncClient:
    """
    Asynchronous AsyncClient fixture for FastAPI.
    Use this for testing async endpoints or features like WebSockets
    where you need to await client operations directly in your test.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_app_state(mocker):
    """
    Mocks the AppState instance presumably used by the FastAPI application.

    The patch target 'backend.core.state.app_state' assumes that 'app_state' is
    an object (e.g., an instance of an AppState class) that is either defined
    globally in 'backend/core/state.py' or imported into that namespace in a way
    that 'app' can access it.

    If 'app_state' is an attribute of the app instance (e.g., app.state),
    you would use: mocker.patch.object(app, "state", autospec=True)

    Adjust the target string as necessary based on your application's structure.
    """
    # Example: mock = mocker.patch("core_daemon.main.app_state_instance_name", autospec=True)
    mock = mocker.patch("backend.core.state.app_state", autospec=True)
    return mock


@pytest.fixture
def mock_can_manager(mocker):
    """
    Mocks the CANManager instance presumably used by the FastAPI application.

    Similar to 'mock_app_state', the patch target 'backend.integrations.can.manager'
    assumes 'can_manager' module is accessible from 'backend/integrations/can/manager.py'.

    If 'can_manager' is an attribute of the app instance (e.g., app.can_manager),
    you would use: mocker.patch.object(app, "can_manager", autospec=True)

    Adjust the target string as necessary.
    """
    # Example: mock = mocker.patch("core_daemon.main.can_manager_instance_name", autospec=True)
    mock = mocker.patch("backend.integrations.can.manager", autospec=True)
    return mock


# --- Global state reset fixtures for test isolation ---


@pytest.fixture(autouse=True)
def reset_app_state_globals():
    """
    Automatically reset all global state variables in app_state before each test.
    Ensures test isolation for all tests using app_state.
    """
    import backend.core.state as app_state

    app_state.state = {}
    app_state.history = {}
    app_state.unmapped_entries = {}
    app_state.unknown_pgns = {}
    app_state.last_known_brightness_levels = {}
    app_state.entity_id_lookup = {}
    app_state.light_entity_ids = []
    app_state.light_command_info = {}
    app_state.decoder_map = {}
    app_state.raw_device_mapping = {}
    app_state.device_lookup = {}
    app_state.status_lookup = {}
    app_state.pgn_hex_to_name_map = {}


@pytest.fixture(autouse=True)
def reset_can_manager_state():
    """
    Automatically reset global state in can_manager before each test.
    Ensures test isolation for all tests using can_manager.
    """
    import asyncio

    import backend.integrations.can.manager as can_manager

    can_manager.can_tx_queue = asyncio.Queue()
    can_manager.buses = {}


# How to use these fixtures in your tests:
#
# from fastapi.testclient import TestClient # If using client directly without fixture
# from httpx import AsyncClient # If using async_client directly
#
# def test_some_synchronous_endpoint(client: TestClient, mock_app_state):
# mock_app_state.get_some_data.return_value = {"example": "data"}
# response = client.get("/data-endpoint")
# assert response.status_code == 200
# assert response.json() == {"example": "data"}
# mock_app_state.get_some_data.assert_called_once()
#
# async def test_some_asynchronous_endpoint(async_client: AsyncClient, mock_can_manager):
# mock_can_manager.send_message_async.return_value = True # Assuming it's an async mock
# response = await async_client.post("/control-endpoint", json={"command": "do_something"})
# assert response.status_code == 200
# mock_can_manager.send_message_async.assert_called_once_with("expected_message")
