"""
Tests for the API router managing RVC entities and their interactions.

This module provides tests for the endpoints defined in
`core_daemon.api_routers.entities.py`. It covers:
- Listing and retrieving entities and their details.
- Accessing entity history.
- Viewing unmapped CAN PGN entries and unknown PGNs.
- Listing and filtering light entities.
- Retrieving metadata about entity types, areas, capabilities, etc.
- Controlling light entities (individual and bulk operations).

Mocks are used extensively to simulate application state, lookup tables,
and CAN command sending. FastAPI's TestClient is used for endpoint testing.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core_daemon.models import Entity, UnknownPGNEntry, UnmappedEntryModel

# --- Mock Data and Fixtures ---


@pytest.fixture
def mock_app_state_data():
    """Provides mock application state data for entities."""
    return {
        "entity1": Entity(
            entity_id="light.living_room",
            value={"status": "on"},
            raw={},
            state="on",
            timestamp=time.time(),
            device_type="light",
            suggested_area="Living Room",
            capabilities=["on_off", "brightness"],
        ),
        "entity2": Entity(
            entity_id="sensor.temp_patio",
            value={"temp": 25},
            raw={},
            state="25",
            timestamp=time.time(),
            device_type="sensor",
            suggested_area="Patio",
        ),
        "entity3": Entity(
            entity_id="light.kitchen",
            value={"status": "off"},
            raw={},
            state="off",
            timestamp=time.time(),
            device_type="light",
            suggested_area="Kitchen",
            capabilities=["on_off"],
        ),
    }


@pytest.fixture
def mock_entity_id_lookup_data():
    """Provides mock entity ID lookup data."""
    return {
        "light.living_room": {
            "device_type": "light",
            "suggested_area": "Living Room",
            "capabilities": ["on_off", "brightness"],
            "groups": ["all_lights", "group1"],
        },
        "sensor.temp_patio": {
            "device_type": "sensor",
            "suggested_area": "Patio",
            "groups": ["all_sensors"],
        },
        "light.kitchen": {
            "device_type": "light",
            "suggested_area": "Kitchen",
            "capabilities": ["on_off"],
            "groups": ["all_lights", "group2"],
        },
    }


@pytest.fixture
def mock_history_data():
    """Provides mock entity history data."""
    ts = time.time()
    return {
        "light.living_room": [
            Entity(
                entity_id="light.living_room",
                value={"status": "off"},
                raw={},
                state="off",
                timestamp=ts - 100,
                device_type="light",
            ),
            Entity(
                entity_id="light.living_room",
                value={"status": "on"},
                raw={},
                state="on",
                timestamp=ts - 50,
                device_type="light",
            ),
        ],
        "sensor.temp_patio": [
            Entity(
                entity_id="sensor.temp_patio",
                value={"temp": 20},
                raw={},
                state="20",
                timestamp=ts - 60,
                device_type="sensor",
            ),
            Entity(
                entity_id="sensor.temp_patio",
                value={"temp": 25},
                raw={},
                state="25",
                timestamp=ts - 30,
                device_type="sensor",
            ),
        ],
    }


@pytest.fixture
def mock_unmapped_entries_data():
    """Provides mock unmapped CAN PGN entries."""
    return {
        "0x1EF00_0": UnmappedEntryModel(
            pgn_hex="1EF00",
            dgn_hex="F00",
            instance="0",
            last_data_hex="ABC",
            first_seen_timestamp=time.time(),
            last_seen_timestamp=time.time(),
            count=1,
        ),
    }


@pytest.fixture
def mock_unknown_pgns_data():
    """Provides mock unknown CAN PGN entries."""
    return {
        "0x12345": UnknownPGNEntry(
            arbitration_id_hex="12345",
            first_seen_timestamp=time.time(),
            last_seen_timestamp=time.time(),
            count=1,
            last_data_hex="DEF",
        ),
    }


@pytest.fixture
def mock_light_command_info_data():
    """Provides mock command info for light entities."""
    return {
        "light.living_room": {"dgn": 0x1F806, "instance": 0, "interface": "can0"},
        "light.kitchen": {"dgn": 0x1F806, "instance": 1, "interface": "can0"},
    }


@pytest.fixture
def mock_light_entity_ids_data():
    """Provides a list of mock light entity IDs."""
    return ["light.living_room", "light.kitchen"]


# --- GET /entities ---
@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
def test_list_entities_no_filters(
    mock_lookup, mock_state, mock_app_state_data, mock_entity_id_lookup_data, client
):
    """Tests listing all entities without any filters."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)

    response = client.get("/api/entities")
    assert response.status_code == 200
    assert len(response.json()) == 3
    assert "light.living_room" in response.json()


@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
def test_list_entities_filter_by_type(
    mock_lookup, mock_state, mock_app_state_data, mock_entity_id_lookup_data, client
):
    """Tests listing entities filtered by type."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)

    response = client.get("/api/entities?type=light")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "light.living_room" in data
    assert "light.kitchen" in data
    assert "sensor.temp_patio" not in data


@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
def test_list_entities_filter_by_area(
    mock_lookup, mock_state, mock_app_state_data, mock_entity_id_lookup_data, client
):
    """Tests listing entities filtered by area."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)

    response = client.get("/api/entities?area=Living Room")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "light.living_room" in data


@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
def test_list_entities_filter_by_type_and_area(
    mock_lookup, mock_state, mock_app_state_data, mock_entity_id_lookup_data, client
):
    """Tests listing entities filtered by type and area."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)

    response = client.get("/api/entities?type=light&area=Kitchen")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "light.kitchen" in data


# --- GET /entities/ids ---
@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
def test_list_entity_ids(mock_state, mock_app_state_data, client):
    """Tests retrieving IDs of all entities."""
    mock_state.keys.return_value = mock_app_state_data.keys()
    response = client.get("/api/entities/ids")
    assert response.status_code == 200
    ids = response.json()
    assert len(ids) == 3
    assert "light.living_room" in ids
    assert "sensor.temp_patio" in ids


# --- GET /entities/{entity_id} ---
@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
def test_get_entity_success(mock_state, mock_app_state_data, client):
    """Tests retrieving a specific entity successfully."""
    mock_state.get.return_value = mock_app_state_data["light.living_room"]
    response = client.get("/api/entities/light.living_room")
    assert response.status_code == 200
    assert response.json()["entity_id"] == "light.living_room"


@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
def test_get_entity_not_found(mock_state, client):
    """Tests retrieving a non-existent entity."""
    mock_state.get.return_value = None
    response = client.get("/api/entities/non.existent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Entity not found"}


# --- GET /entities/{entity_id}/history ---
@patch("core_daemon.api_routers.entities.history", new_callable=MagicMock)
def test_get_history_success(mock_hist, mock_history_data, client):
    """Tests retrieving history for an entity successfully."""
    mock_hist.__contains__.return_value = True  # For `entity_id not in history`
    mock_hist.__getitem__.return_value = mock_history_data["light.living_room"]

    response = client.get("/api/entities/light.living_room/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["value"]["status"] == "off"


@patch("core_daemon.api_routers.entities.history", new_callable=MagicMock)
def test_get_history_not_found(mock_hist, client):
    """Tests retrieving history for a non-existent entity."""
    mock_hist.__contains__.return_value = False
    response = client.get("/api/entities/non.existent/history")
    assert response.status_code == 404
    assert response.json() == {"detail": "Entity not found"}


@patch("core_daemon.api_routers.entities.history", new_callable=MagicMock)
def test_get_history_with_since(mock_hist, mock_history_data, client):
    """Tests retrieving entity history with a 'since' timestamp."""
    mock_hist.__contains__.return_value = True
    mock_hist.__getitem__.return_value = mock_history_data["light.living_room"]
    since_ts = mock_history_data["light.living_room"][0].timestamp + 1  # after the first entry

    response = client.get(f"/api/entities/light.living_room/history?since={since_ts}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["value"]["status"] == "on"


@patch("core_daemon.api_routers.entities.history", new_callable=MagicMock)
def test_get_history_with_limit(mock_hist, mock_history_data, client):
    """Tests retrieving entity history with a 'limit'."""
    mock_hist.__contains__.return_value = True
    mock_hist.__getitem__.return_value = mock_history_data["light.living_room"]

    response = client.get("/api/entities/light.living_room/history?limit=1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["value"]["status"] == "on"  # last entry


# --- GET /unmapped_entries ---
@patch("core_daemon.api_routers.entities.unmapped_entries", new_callable=MagicMock)
def test_get_unmapped_entries_api(mock_unmapped, mock_unmapped_entries_data, client):
    """Tests the API endpoint for unmapped CAN PGN entries."""
    mock_unmapped.return_value = mock_unmapped_entries_data  # Direct assignment if it's a variable
    # If unmapped_entries is a dict that's directly used:
    with patch("core_daemon.api_routers.entities.unmapped_entries", mock_unmapped_entries_data):
        response = client.get("/api/unmapped_entries")
    assert response.status_code == 200
    assert "0x1EF00_0" in response.json()


# --- GET /unknown_pgns ---
@patch("core_daemon.api_routers.entities.unknown_pgns", new_callable=MagicMock)
def test_get_unknown_pgns_api(mock_unknown, mock_unknown_pgns_data, client):
    """Tests the API endpoint for unknown CAN PGN entries."""
    with patch("core_daemon.api_routers.entities.unknown_pgns", mock_unknown_pgns_data):
        response = client.get("/api/unknown_pgns")
    assert response.status_code == 200
    assert "0x12345" in response.json()


# --- GET /lights ---
@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.light_entity_ids", new_callable=MagicMock)
def test_list_lights_no_filters(
    mock_light_ids,
    mock_lookup,
    mock_state,
    mock_app_state_data,
    mock_entity_id_lookup_data,
    mock_light_entity_ids_data,
    client,
):
    """Tests listing all light entities without filters."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)
    mock_light_ids.__contains__ = (
        lambda x: x in mock_light_entity_ids_data
    )  # Simulate `eid in light_entity_ids`

    response = client.get("/api/lights")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "light.living_room" in data
    assert "light.kitchen" in data


@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.light_entity_ids", new_callable=MagicMock)
def test_list_lights_filter_state_on(
    mock_light_ids,
    mock_lookup,
    mock_state,
    mock_app_state_data,
    mock_entity_id_lookup_data,
    mock_light_entity_ids_data,
    client,
):
    """Tests listing light entities filtered by 'on' state."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)
    mock_light_ids.__contains__ = lambda x: x in mock_light_entity_ids_data

    response = client.get("/api/lights?state=on")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "light.living_room" in data


@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.light_entity_ids", new_callable=MagicMock)
def test_list_lights_filter_capability_brightness(
    mock_light_ids,
    mock_lookup,
    mock_state,
    mock_app_state_data,
    mock_entity_id_lookup_data,
    mock_light_entity_ids_data,
    client,
):
    """Tests listing light entities filtered by 'brightness' capability."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)
    mock_light_ids.__contains__ = lambda x: x in mock_light_entity_ids_data

    response = client.get("/api/lights?capability=brightness")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "light.living_room" in data


@patch("core_daemon.api_routers.entities.state", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.light_entity_ids", new_callable=MagicMock)
def test_list_lights_filter_area(
    mock_light_ids,
    mock_lookup,
    mock_state,
    mock_app_state_data,
    mock_entity_id_lookup_data,
    mock_light_entity_ids_data,
    client,
):
    """Tests listing light entities filtered by area."""
    mock_state.items.return_value = mock_app_state_data.items()
    mock_lookup.get = lambda key, default: mock_entity_id_lookup_data.get(key, default)
    mock_light_ids.__contains__ = lambda x: x in mock_light_entity_ids_data

    response = client.get("/api/lights?area=Kitchen")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "light.kitchen" in data


# --- GET /meta ---
@patch("core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock)
@patch("core_daemon.api_routers.entities.light_command_info", new_callable=MagicMock)
def test_get_metadata(
    mock_light_cmd_info,
    mock_lookup,
    mock_entity_id_lookup_data,
    mock_light_command_info_data,
    client,
):
    """Tests the /meta endpoint for retrieving metadata about entities."""
    mock_lookup.values.return_value = mock_entity_id_lookup_data.values()
    mock_lookup.items.return_value = mock_entity_id_lookup_data.items()  # For command part
    mock_light_cmd_info.__contains__ = (
        lambda x: x in mock_light_command_info_data
    )  # For command part

    response = client.get("/api/meta")
    assert response.status_code == 200
    data = response.json()

    assert sorted(data["type"]) == sorted(["light", "sensor"])
    assert sorted(data["area"]) == sorted(["Kitchen", "Living Room", "Patio"])
    assert sorted(data["capability"]) == sorted(["on_off", "brightness"])
    assert sorted(data["groups"]) == sorted(["all_lights", "all_sensors", "group1", "group2"])
    # Commands are derived, check for expected light commands
    assert "set" in data["command"]
    assert "toggle" in data["command"]
    assert "brightness" in data["command"]
    assert "brightness_up" in data["command"]
    assert "brightness_down" in data["command"]


# --- POST /entities/{entity_id}/control ---


@pytest.fixture
def mock_control_dependencies(
    mock_entity_id_lookup_data, mock_light_command_info_data, mock_app_state_data
):
    """Groups common patches and mocks for entity control endpoints."""
    # This fixture will group common patches for control endpoints
    patches = {
        "entity_id_lookup_patch": patch(
            "core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock
        ),
        "light_command_info_patch": patch(
            "core_daemon.api_routers.entities.light_command_info", new_callable=MagicMock
        ),
        "state_patch": patch("core_daemon.api_routers.entities.state", new_callable=MagicMock),
        "get_last_known_brightness_patch": patch(
            "core_daemon.api_routers.entities.get_last_known_brightness"
        ),
        "set_last_known_brightness_patch": patch(
            "core_daemon.api_routers.entities.set_last_known_brightness"
        ),
        "send_light_can_command_patch": patch(
            "core_daemon.api_routers.entities._send_light_can_command", new_callable=AsyncMock
        ),  # Mocking the helper
    }

    mock_objects = {name: p.start() for name, p in patches.items()}

    # Configure default behaviors for mocks
    mock_objects["entity_id_lookup_patch"].get = (
        lambda key, default=None: mock_entity_id_lookup_data.get(key, default)
    )
    mock_objects["light_command_info_patch"].__contains__ = (
        lambda key: key in mock_light_command_info_data
    )
    mock_objects["light_command_info_patch"].get = lambda key: mock_light_command_info_data.get(key)

    # Initial state for a controllable light (e.g., living room light)
    # Ensure the state mock returns a mutable copy if tests modify it, or reset per test.
    # For simplicity, we'll often set specific return_value for state.get in tests.
    mock_objects["state_patch"].get.return_value = mock_app_state_data[
        "light.living_room"
    ].model_copy(deep=True)

    mock_objects[
        "get_last_known_brightness_patch"
    ].return_value = 50  # Default last known brightness
    mock_objects["send_light_can_command_patch"].return_value = True  # Default to successful send

    yield mock_objects  # Provide the dictionary of mock objects to the test

    # Stop all patches
    for p in patches.values():
        p.stop()


def test_control_entity_turn_on_from_off(mock_control_dependencies, mock_app_state_data, client):
    """Tests turning a light on (from off state) via control endpoint."""
    entity_id = "light.kitchen"  # Starts off
    mock_control_dependencies["state_patch"].get.return_value = mock_app_state_data[
        entity_id
    ].model_copy(deep=True)
    mock_control_dependencies[
        "get_last_known_brightness_patch"
    ].return_value = 70  # Assume it was 70% before turning off

    payload = {"command": "set", "state": "on"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "sent"
    assert data["entity_id"] == entity_id
    assert data["state"] == "on"
    assert data["brightness"] == 70  # Should turn on to last known brightness
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 70, "Set ON to 70%"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 70)


def test_control_entity_turn_on_with_brightness(mock_control_dependencies, client):
    """Tests turning a light on with a specific brightness."""
    entity_id = "light.living_room"
    payload = {"command": "set", "state": "on", "brightness": 85}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "on"
    assert data["brightness"] == 85
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 85, "Set ON to 85%"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 85)


def test_control_entity_turn_off(mock_control_dependencies, mock_app_state_data, client):
    """Tests turning a light off via control endpoint."""
    entity_id = "light.living_room"  # Starts on
    # Simulate current brightness is 60%
    current_entity_state = mock_app_state_data[entity_id].model_copy(deep=True)
    current_entity_state.raw = {"operating_status": 120}  # 120 raw = 60% UI
    current_entity_state.state = "on"
    mock_control_dependencies["state_patch"].get.return_value = current_entity_state

    payload = {"command": "set", "state": "off"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "off"
    assert data["brightness"] == 0
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 0, "Set OFF"
    )
    # Check that current brightness (60) was stored as last_known_brightness
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 60)


def test_control_entity_set_brightness_implies_on(mock_control_dependencies, client):
    """Tests that setting brightness also turns the light on."""
    entity_id = "light.kitchen"  # Starts off
    payload = {"command": "set", "brightness": 40}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "on"
    assert data["brightness"] == 40
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 40, "Set Brightness to 40% (implies ON)"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 40)


def test_control_entity_toggle_on_to_off(mock_control_dependencies, mock_app_state_data, client):
    """Tests toggling a light from on to off."""
    entity_id = "light.living_room"  # Starts on
    current_entity_state = mock_app_state_data[entity_id].model_copy(deep=True)
    current_entity_state.raw = {"operating_status": 100}  # 50% UI
    current_entity_state.state = "on"
    mock_control_dependencies["state_patch"].get.return_value = current_entity_state

    payload = {"command": "toggle"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "off"
    assert data["brightness"] == 0
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 0, "Toggle OFF"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(
        entity_id, 50
    )  # Stored current before turning off


def test_control_entity_toggle_off_to_on(mock_control_dependencies, mock_app_state_data, client):
    """Tests toggling a light from off to on."""
    entity_id = "light.kitchen"  # Starts off
    mock_control_dependencies["state_patch"].get.return_value = mock_app_state_data[
        entity_id
    ].model_copy(deep=True)
    mock_control_dependencies["get_last_known_brightness_patch"].return_value = 65

    payload = {"command": "toggle"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "on"
    assert data["brightness"] == 65
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 65, "Toggle ON to 65%"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 65)


def test_control_entity_brightness_up(mock_control_dependencies, mock_app_state_data, client):
    """Tests increasing light brightness."""
    entity_id = "light.living_room"
    current_entity_state = mock_app_state_data[entity_id].model_copy(deep=True)
    current_entity_state.raw = {"operating_status": 80}  # 40% UI
    current_entity_state.state = "on"
    mock_control_dependencies["state_patch"].get.return_value = current_entity_state

    payload = {"command": "brightness_up"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["brightness"] == 50  # 40 + 10
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 50, "Brightness UP to 50%"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 50)


def test_control_entity_brightness_up_from_off(
    mock_control_dependencies, mock_app_state_data, client
):
    """Tests increasing brightness for a light that is off (should turn on)."""
    entity_id = "light.kitchen"  # Starts off
    mock_control_dependencies["state_patch"].get.return_value = mock_app_state_data[
        entity_id
    ].model_copy(deep=True)

    payload = {"command": "brightness_up"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["brightness"] == 10  # Turns on to 10%
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 10, "Brightness UP to 10%"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 10)


def test_control_entity_brightness_down(mock_control_dependencies, mock_app_state_data, client):
    """Tests decreasing light brightness."""
    entity_id = "light.living_room"
    current_entity_state = mock_app_state_data[entity_id].model_copy(deep=True)
    current_entity_state.raw = {"operating_status": 100}  # 50% UI
    current_entity_state.state = "on"
    mock_control_dependencies["state_patch"].get.return_value = current_entity_state

    payload = {"command": "brightness_down"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["brightness"] == 40  # 50 - 10
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 40, "Brightness DOWN to 40%"
    )
    mock_control_dependencies["set_last_known_brightness_patch"].assert_any_call(entity_id, 40)


def test_control_entity_brightness_down_to_zero(
    mock_control_dependencies, mock_app_state_data, client
):
    """Tests decreasing light brightness to zero (should turn off)."""
    entity_id = "light.living_room"
    current_entity_state = mock_app_state_data[entity_id].model_copy(deep=True)
    current_entity_state.raw = {"operating_status": 10}  # 5% UI
    current_entity_state.state = "on"
    mock_control_dependencies["state_patch"].get.return_value = current_entity_state

    payload = {"command": "brightness_down"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["brightness"] == 0  # 5 - 10 = -5, so 0
    assert data["state"] == "off"
    mock_control_dependencies["send_light_can_command_patch"].assert_called_once_with(
        entity_id, 0, "Brightness DOWN to 0%"
    )
    called_with_zero = False
    for call_args in mock_control_dependencies["set_last_known_brightness_patch"].call_args_list:
        if call_args[0][1] == 0:
            called_with_zero = True
            break
    assert (
        not called_with_zero
    ), "set_last_known_brightness should not be called with 0 when brightness_down results in off"


# Error Cases for control_entity
def test_control_entity_not_found(mock_control_dependencies, client):
    """Tests control endpoint behavior for a non-existent entity."""
    mock_control_dependencies["entity_id_lookup_patch"].get.return_value = None
    payload = {"command": "set", "state": "on"}
    response = client.post("/api/entities/non.existent/control", json=payload)
    assert response.status_code == 404
    assert response.json() == {"detail": "Entity not found"}


def test_control_entity_not_controllable_light(mock_control_dependencies, client):
    """Tests control endpoint behavior for an entity not controllable as a light."""
    entity_id = "sensor.temp_patio"  # Not in light_command_info
    mock_control_dependencies["light_command_info_patch"].__contains__ = (
        lambda key: key != entity_id
    )
    payload = {"command": "set", "state": "on"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "Entity is not controllable as a light"}


def test_control_entity_invalid_command_str(mock_control_dependencies, client):
    """Tests control endpoint behavior with an invalid command string."""
    entity_id = "light.living_room"
    payload = {"command": "invalid_cmd", "state": "on"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 400  # Based on current Pydantic model, this might be 422
    assert response.json() == {"detail": "Invalid command: invalid_cmd"}


def test_control_entity_invalid_state_for_set(mock_control_dependencies, client):
    """Tests control endpoint behavior with an invalid state for the 'set' command."""
    entity_id = "light.living_room"
    payload = {"command": "set", "state": "invalid_state"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 400
    assert response.json() == {"detail": "State must be 'on' or 'off' for set command"}


def test_control_entity_send_can_command_fails(mock_control_dependencies, client):
    """Tests control endpoint behavior when sending the CAN command fails."""
    entity_id = "light.living_room"
    mock_control_dependencies[
        "send_light_can_command_patch"
    ].return_value = False  # Simulate failure
    payload = {"command": "set", "state": "on"}
    response = client.post(f"/api/entities/{entity_id}/control", json=payload)
    assert response.status_code == 500
    action_str = "Set ON to 50%"  # Default last known brightness is 50 from fixture
    assert response.json() == {
        "detail": f"Failed to send CAN command for {entity_id} (Action: {action_str})"
    }


# --- POST /lights/control (Bulk) ---


@pytest.fixture
def mock_bulk_control_dependencies(
    mock_entity_id_lookup_data,
    mock_light_command_info_data,
    mock_app_state_data,
    mock_light_entity_ids_data,
):
    """Groups common patches and mocks for bulk light control endpoints."""
    patches = {
        "entity_id_lookup_patch": patch(
            "core_daemon.api_routers.entities.entity_id_lookup", new_callable=MagicMock
        ),
        "light_command_info_patch": patch(
            "core_daemon.api_routers.entities.light_command_info", new_callable=MagicMock
        ),
        "state_patch": patch("core_daemon.api_routers.entities.state", new_callable=MagicMock),
        "get_last_known_brightness_patch": patch(
            "core_daemon.api_routers.entities.get_last_known_brightness"
        ),
        "set_last_known_brightness_patch": patch(
            "core_daemon.api_routers.entities.set_last_known_brightness"
        ),
        "send_light_can_command_patch": patch(
            "core_daemon.api_routers.entities._send_light_can_command", new_callable=AsyncMock
        ),
        "light_entity_ids_patch": patch(
            "core_daemon.api_routers.entities.light_entity_ids", new_callable=MagicMock
        ),
    }
    mock_objects = {name: p.start() for name, p in patches.items()}

    mock_objects["entity_id_lookup_patch"].get = (
        lambda key, default=None: mock_entity_id_lookup_data.get(key, default)
    )
    # For bulk, we iterate .items() of entity_id_lookup
    mock_objects["entity_id_lookup_patch"].items = lambda: mock_entity_id_lookup_data.items()

    mock_objects["light_command_info_patch"].__contains__ = (
        lambda key: key in mock_light_command_info_data
    )
    mock_objects["light_command_info_patch"].get = lambda key: mock_light_command_info_data.get(key)

    # state.get needs to return different states for different entities
    def state_get_side_effect(key, default=None):
        return (
            mock_app_state_data.get(key, default).model_copy(deep=True)
            if key in mock_app_state_data
            else default
        )

    mock_objects["state_patch"].get = MagicMock(side_effect=state_get_side_effect)

    mock_objects["get_last_known_brightness_patch"].return_value = 60  # Default for bulk tests
    mock_objects["send_light_can_command_patch"].return_value = True  # Default to successful send
    mock_objects["light_entity_ids_patch"].__contains__ = (
        lambda key: key in mock_light_entity_ids_data
    )

    yield mock_objects

    for p in patches.values():
        p.stop()


def test_control_lights_bulk_set_on_all(
    mock_bulk_control_dependencies, mock_light_command_info_data, client
):
    """Tests bulk controlling all lights to 'on'."""
    payload = {"command": "set", "state": "on"}
    # No group specified, should target all controllable lights
    response = client.post("/api/lights/control", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["lights_processed"] == len(
        mock_light_command_info_data
    )  # Both kitchen and living room
    assert data["lights_commanded"] == len(mock_light_command_info_data)

    send_calls = mock_bulk_control_dependencies["send_light_can_command_patch"].call_args_list
    assert len(send_calls) == len(mock_light_command_info_data)
    # Check if both lights were commanded (order might vary)
    called_entities = {call[0][0] for call in send_calls}
    assert "light.living_room" in called_entities
    assert "light.kitchen" in called_entities
    for call in send_calls:
        assert call[0][1] == 60  # Turned on to default last_known_brightness from fixture
        assert "Set ON to 60%" in call[0][2]


def test_control_lights_bulk_set_off_group(
    mock_bulk_control_dependencies, mock_entity_id_lookup_data, client
):
    """Tests bulk controlling lights in a specific group to 'off'."""
    # Target group1, which only contains light.living_room
    payload = {"command": "set", "state": "off"}
    response = client.post("/api/lights/control?group=group1", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["lights_processed"] == 1
    assert data["lights_commanded"] == 1
    assert data["details"][0]["entity_id"] == "light.living_room"
    assert data["details"][0]["state"] == "off"

    mock_bulk_control_dependencies["send_light_can_command_patch"].assert_called_once()
    call_args = mock_bulk_control_dependencies["send_light_can_command_patch"].call_args[0]
    assert call_args[0] == "light.living_room"
    assert call_args[1] == 0  # Brightness for OFF
    assert "Set OFF" in call_args[2]
    # Verify set_last_known_brightness was called for light.living_room before turning off
    # The state for light.living_room is initially ON with brightness (from mock_app_state_data)
    # Its raw.operating_status is not set in mock_app_state_data, so current_brightness_ui defaults
    # to 100 if on.
    mock_bulk_control_dependencies["set_last_known_brightness_patch"].assert_any_call(
        "light.living_room", 100
    )


def test_control_lights_bulk_toggle_group_all_lights(
    mock_bulk_control_dependencies, mock_light_command_info_data, mock_app_state_data, client
):
    """Tests bulk toggling lights in the 'all_lights' group."""
    # group "all_lights" contains both kitchen (off) and living_room (on)
    # living_room (on) -> should turn off, last brightness 100 (default from state)
    # kitchen (off) -> should turn on to 60 (default last_known_brightness from bulk fixture)
    payload = {"command": "toggle"}
    response = client.post("/api/lights/control?group=all_lights", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["lights_processed"] == 2
    assert data["lights_commanded"] == 2

    send_calls = mock_bulk_control_dependencies["send_light_can_command_patch"].call_args_list
    assert len(send_calls) == 2

    for call in send_calls:
        entity_id = call[0][0]
        target_brightness = call[0][1]
        action_desc = call[0][2]
        if entity_id == "light.living_room":
            assert target_brightness == 0  # Was on, toggles off
            assert "Toggle OFF" in action_desc
            mock_bulk_control_dependencies["set_last_known_brightness_patch"].assert_any_call(
                "light.living_room", 100
            )
        elif entity_id == "light.kitchen":
            assert target_brightness == 60  # Was off, toggles on to last known (60 from fixture)
            assert "Toggle ON to 60%" in action_desc
            mock_bulk_control_dependencies["set_last_known_brightness_patch"].assert_any_call(
                "light.kitchen", 60
            )


def test_control_lights_bulk_brightness_up_no_group(
    mock_bulk_control_dependencies, mock_app_state_data, client
):
    """Tests bulk increasing brightness for all lights."""
    # living_room: on, raw not set -> current_brightness_ui = 100. 100+10 = 100 (capped)
    # kitchen: off -> current_brightness_ui = 0. 0+10 = 10.
    payload = {"command": "brightness_up"}
    response = client.post("/api/lights/control", json=payload)  # All lights

    assert response.status_code == 200
    data = response.json()
    assert data["lights_processed"] == 2
    assert data["lights_commanded"] == 2

    for detail in data["details"]:
        if detail["entity_id"] == "light.living_room":
            assert detail["brightness"] == 100
            assert "Brightness UP to 100%" in detail["action"]
        elif detail["entity_id"] == "light.kitchen":
            assert detail["brightness"] == 10
            assert "Brightness UP to 10%" in detail["action"]


def test_control_lights_bulk_no_matching_group(mock_bulk_control_dependencies, client):
    """Tests bulk control behavior when no lights match the specified group."""
    payload = {"command": "set", "state": "on"}
    response = client.post("/api/lights/control?group=non_existent_group", json=payload)

    assert response.status_code == 200  # Endpoint returns 200 but with specific status
    data = response.json()
    assert data["status"] == "no_match"
    assert data["lights_processed"] == 0
    assert data["lights_commanded"] == 0
    assert "No lights found or matched" in data["message"]
    mock_bulk_control_dependencies["send_light_can_command_patch"].assert_not_called()


def test_control_lights_bulk_no_controllable_lights_in_system(
    mock_bulk_control_dependencies, client
):
    """Tests bulk control behavior when no controllable lights exist."""
    # Simulate no lights are controllable by making light_command_info empty
    mock_bulk_control_dependencies["light_command_info_patch"].__contains__ = lambda key: False
    mock_bulk_control_dependencies["light_command_info_patch"].get = lambda key: None
    mock_bulk_control_dependencies["light_entity_ids_patch"].__contains__ = lambda key: False

    payload = {"command": "set", "state": "on"}
    response = client.post("/api/lights/control", json=payload)  # All lights

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "no_match"  # Or a similar status indicating nothing to do
    assert data["lights_processed"] == 0
    assert "No controllable lights found" in data["message"]
    mock_bulk_control_dependencies["send_light_can_command_patch"].assert_not_called()


def test_control_lights_bulk_one_fails(mock_bulk_control_dependencies, mock_app_state_data, client):
    """Tests bulk control behavior when one of the CAN commands fails."""

    # Make sending command for kitchen light fail
    async def send_side_effect(entity_id, brightness, action):
        return entity_id != "light.kitchen"

    mock_bulk_control_dependencies["send_light_can_command_patch"].side_effect = send_side_effect

    payload = {"command": "set", "state": "on"}
    response = client.post("/api/lights/control", json=payload)  # All lights

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "partial_error"
    assert data["lights_processed"] == 2
    assert data["lights_commanded"] == 1  # Only living_room succeeded
    assert len(data["errors"]) == 1
    assert data["errors"][0]["entity_id"] == "light.kitchen"

    details = {d["entity_id"]: d for d in data["details"]}
    assert details["light.living_room"]["status"] == "sent"
    assert details["light.kitchen"]["status"] == "error"
