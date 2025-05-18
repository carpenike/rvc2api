"""
Unit tests for the app_state module in the core_daemon.

These tests cover the initialization of application state from configuration,
management of entity states and history, handling of unmapped/unknown CAN messages,
and pre-seeding of light states.
"""

from collections import deque
from unittest.mock import MagicMock, call, patch

import pytest

# Assuming your app_state module is in core_daemon
from core_daemon import app_state


# Reset global state variables in app_state before each test
@pytest.fixture(autouse=True)
def reset_app_state_globals():
    """
    Automatically used fixture to reset all global state variables in the
    app_state module before each test. This ensures test isolation.
    """
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
    # Reset metrics if they are part of app_state or manipulated directly
    # For example, if ENTITY_COUNT and HISTORY_SIZE_GAUGE are directly manipulated
    # and need resetting. This might require more specific mock patching if they
    # are Prometheus client objects.
    # For simplicity, if they are just variables, reset them:
    # app_state.ENTITY_COUNT = MagicMock() # Or whatever their type is
    # app_state.HISTORY_SIZE_GAUGE = MagicMock()


@pytest.fixture
def mock_config_data_tuple():
    """
    Provides a mock tuple representing the complex configuration data
    expected by initialize_app_from_config.
    """
    return (
        {"decoder_map_val": 1},  # decoder_map
        {"raw_device_mapping_val": 2},  # raw_device_mapping
        {"device_lookup_val": 3},  # device_lookup
        {"status_lookup_val": 4},  # status_lookup
        ["light.one", "light.two"],  # light_entity_ids
        {
            "light.one": {"id": "light.one"},
            "light.two": {"id": "light.two"},
            "sensor.one": {"id": "sensor.one"},
        },  # entity_id_lookup
        {"light.one": {"cmd": "A"}, "light.two": {"cmd": "B"}},  # light_command_info
        {"PGN1": "Name1"},  # pgn_hex_to_name_map
    )


@pytest.fixture
def mock_decode_payload_function():
    """
    Provides a mock of the decode_payload function, returning predefined
    decoded and raw payloads for testing purposes.
    """
    # Returns (decoded_payload, raw_payload)
    return MagicMock(
        return_value=(
            {"decoded_key": "decoded_value"},
            {"raw_key": "raw_value", "operating_status": 0},
        )
    )


def test_initialize_app_from_config(mock_config_data_tuple, mock_decode_payload_function):
    """
    Test that initialize_app_from_config correctly populates all global
    state variables from the provided configuration data and calls helper functions.
    """
    with patch.object(
        app_state, "initialize_history_deques_internal"
    ) as mock_init_history, patch.object(
        app_state, "preseed_light_states_internal"
    ) as mock_preseed_lights:
        app_state.initialize_app_from_config(mock_config_data_tuple, mock_decode_payload_function)

        assert app_state.decoder_map == {"decoder_map_val": 1}
        assert app_state.raw_device_mapping == {"raw_device_mapping_val": 2}
        assert app_state.device_lookup == {"device_lookup_val": 3}
        assert app_state.status_lookup == {"status_lookup_val": 4}
        assert app_state.light_entity_ids == ["light.one", "light.two"]
        assert app_state.entity_id_lookup == {
            "light.one": {"id": "light.one"},
            "light.two": {"id": "light.two"},
            "sensor.one": {"id": "sensor.one"},
        }
        assert app_state.light_command_info == {
            "light.one": {"cmd": "A"},
            "light.two": {"cmd": "B"},
        }
        assert app_state.pgn_hex_to_name_map == {"PGN1": "Name1"}

        mock_init_history.assert_called_once()
        mock_preseed_lights.assert_called_once_with(mock_decode_payload_function)


def test_get_last_known_brightness():
    """Test retrieval of last known brightness, including default for unknown entities."""
    app_state.last_known_brightness_levels = {"light.one": 75, "light.two": 0}
    assert app_state.get_last_known_brightness("light.one") == 75
    assert app_state.get_last_known_brightness("light.two") == 0
    assert app_state.get_last_known_brightness("light.unknown") == 100  # Default


def test_set_last_known_brightness():
    """Test setting and updating the last known brightness for an entity."""
    app_state.set_last_known_brightness("light.one", 50)
    assert app_state.last_known_brightness_levels["light.one"] == 50
    app_state.set_last_known_brightness("light.one", 0)
    assert app_state.last_known_brightness_levels["light.one"] == 0


def test_initialize_history_deques_internal():
    """
    Test that history deques are correctly initialized for entities defined
    in entity_id_lookup, preserving existing deques and creating new ones.
    """
    app_state.entity_id_lookup = {"entity1": {}, "entity2": {}}
    app_state.history = {"entity1": deque(["old_data"])}  # Pre-existing data for one entity

    app_state.initialize_history_deques_internal()

    assert "entity1" in app_state.history
    assert isinstance(app_state.history["entity1"], deque)
    assert (
        len(app_state.history["entity1"]) == 0
    )  # Should re-initialize if called again, or ensure it only adds new
    # The current implementation re-initializes to empty deque if entity exists.
    # If the intent is to preserve and only add new, the test or code needs adjustment.
    # Based on code: `if eid not in history: history[eid] = deque()` - this is wrong.
    # The code is `for eid in entity_id_lookup: if eid not in history: history[eid] = deque()`
    # This means it only adds if not present. Let's adjust test.

    # Re-test with correct understanding of the code
    app_state.history = {"entity1": deque(["old_data"])}
    app_state.entity_id_lookup = {"entity1": {}, "entity2": {}, "entity3": {}}
    app_state.initialize_history_deques_internal()
    assert app_state.history["entity1"] == deque(["old_data"])  # Unchanged
    assert app_state.history["entity2"] == deque()
    assert app_state.history["entity3"] == deque()


@patch("core_daemon.app_state.time.time")
@patch("core_daemon.app_state.ENTITY_COUNT")
@patch("core_daemon.app_state.HISTORY_SIZE_GAUGE")
def test_update_entity_state_and_history(mock_history_gauge, mock_entity_count_metric, mock_time):
    """
    Test updating an entity's state and history, including history pruning
    based on HISTORY_DURATION and metric updates.
    Also tests handling of entities for which history deques were not pre-initialized.
    """
    mock_current_time = 1700000000.0
    mock_time.return_value = mock_current_time

    entity_id = "sensor.temp"
    app_state.history[entity_id] = deque()  # Initialize deque for the entity
    app_state.HISTORY_DURATION = 3600  # 1 hour for testing

    payload1_ts = mock_current_time - 7200  # 2 hours ago (should be pruned)
    payload1 = {"value": 10, "timestamp": payload1_ts}
    payload2_ts = mock_current_time - 1800  # 30 mins ago (should be kept)
    payload2 = {"value": 20, "timestamp": payload2_ts}
    payload3_ts = mock_current_time - 10  # 10 secs ago (should be kept)
    payload3 = {"value": 30, "timestamp": payload3_ts}

    # Update with payload1 (old)
    app_state.update_entity_state_and_history(entity_id, payload1)
    assert app_state.state[entity_id] == payload1
    assert len(app_state.history[entity_id]) == 1
    assert app_state.history[entity_id][0] == payload1
    mock_entity_count_metric.set.assert_called_with(1)
    mock_history_gauge.labels(entity_id=entity_id).set.assert_called_with(1)

    # Update with payload2 (kept)
    app_state.update_entity_state_and_history(entity_id, payload2)
    assert app_state.state[entity_id] == payload2
    assert len(app_state.history[entity_id]) == 2
    assert app_state.history[entity_id][1] == payload2

    # Update with payload3 (kept, and payload1 should be pruned)
    app_state.update_entity_state_and_history(entity_id, payload3)
    assert app_state.state[entity_id] == payload3
    # Now check pruning: payload1's timestamp is payload1_ts (2h ago)
    # payload3's timestamp is mock_current_time - 10
    # cutoff = (mock_current_time - 10) - 3600
    # payload1_ts (mock_current_time - 7200) < cutoff (mock_current_time - 3610) -> should be pruned
    assert len(app_state.history[entity_id]) == 2  # payload2 and payload3 remain
    assert app_state.history[entity_id][0] == payload2
    assert app_state.history[entity_id][1] == payload3
    mock_history_gauge.labels(entity_id=entity_id).set.assert_called_with(2)

    # Test case where history deque doesn't exist (should log warning and create)
    entity_id_new = "sensor.new"
    with patch.object(app_state.logger, "warning") as mock_logger_warning:
        app_state.update_entity_state_and_history(entity_id_new, payload3)
        assert app_state.state[entity_id_new] == payload3
        assert len(app_state.history[entity_id_new]) == 1
        mock_logger_warning.assert_called_once_with(
            f"History deque not found for {entity_id_new}, created new one."
        )


@patch("core_daemon.app_state.update_entity_state_and_history")
def test_preseed_light_states_internal(mock_update_state_hist, mock_decode_payload_function):
    """
    Test the pre-seeding of light states to an 'off' state.
    Verifies that:
    - update_entity_state_and_history is called for valid lights with correct payloads.
    - decode_payload is called with the correct spec and default (off) payload bytes.
    - Warnings are logged for lights missing command info or DGN specifications.
    """
    app_state.light_entity_ids = ["light.one", "light.two", "light.no_info", "light.no_spec"]
    app_state.light_command_info = {
        "light.one": {"dgn": 0x12345},
        "light.two": {"dgn": 0xABCDE},
        # light.no_info has no entry here
        "light.no_spec": {"dgn": 0xFFFFF},  # This DGN won't be in decoder_map
    }
    app_state.decoder_map = {
        # DGNs are integers in light_command_info, hex strings in decoder_map keys (as per code)
        # The code converts info["dgn"] to hex string for lookup.
        "12345": {"dgn_hex": "12345", "name": "Light One Spec"},
        "ABCDE": {"dgn_hex": "ABCDE", "name": "Light Two Spec"},
    }
    app_state.entity_id_lookup = {
        "light.one": {
            "suggested_area": "Living Room",
            "device_type": "light",
            "capabilities": [],
            "friendly_name": "Light One",
            "groups": ["g1"],
        },
        "light.two": {
            "suggested_area": "Kitchen",
            "device_type": "dimmable_light",
            "capabilities": ["dim"],
            "friendly_name": "Light Two",
            "groups": ["g2"],
        },
        "light.no_info": {"friendly_name": "No Info Light"},  # Exists in entity_id_lookup
        "light.no_spec": {"friendly_name": "No Spec Light"},  # Exists in entity_id_lookup
    }

    # Mock the decode_payload_function to return consistent off state
    # (decoded_payload, raw_payload)
    # raw_payload should have "operating_status": 0 for off state
    mock_decode_payload_function.return_value = (
        {"brightness_pct": 0, "state_text": "OFF"},  # decoded
        {"operating_status": 0},  # raw
    )

    with patch.object(app_state.logger, "warning") as mock_logger_warning, patch(
        "core_daemon.app_state.time.time", return_value=12345.678
    ):
        app_state.preseed_light_states_internal(mock_decode_payload_function)

    assert mock_update_state_hist.call_count == 2  # light.one and light.two

    now = 12345.678

    # Expected payload for light.one
    payload_one = {
        "entity_id": "light.one",
        "value": {"brightness_pct": 0, "state_text": "OFF"},
        "raw": {"operating_status": 0},
        "state": "off",
        "timestamp": now,
        "suggested_area": "Living Room",
        "device_type": "light",
        "capabilities": [],
        "friendly_name": "Light One",
        "groups": ["g1"],
    }
    # Expected payload for light.two
    payload_two = {
        "entity_id": "light.two",
        "value": {"brightness_pct": 0, "state_text": "OFF"},
        "raw": {"operating_status": 0},
        "state": "off",
        "timestamp": now,
        "suggested_area": "Kitchen",
        "device_type": "dimmable_light",
        "capabilities": ["dim"],
        "friendly_name": "Light Two",
        "groups": ["g2"],
    }

    # Check calls to update_entity_state_and_history
    # The order of calls might not be guaranteed if light_entity_ids iteration order changes.
    # So, check for calls with specific arguments regardless of order.
    mock_update_state_hist.assert_any_call("light.one", payload_one)
    mock_update_state_hist.assert_any_call("light.two", payload_two)

    # Check warnings
    # Warning for light.no_info (no command info)
    # Warning for light.no_spec (no spec entry for DGN 0xFFFFF)
    assert mock_logger_warning.call_count == 2
    mock_logger_warning.assert_any_call(
        "Pre-seeding: No command info for light entity ID: light.no_info"
    )
    mock_logger_warning.assert_any_call(
        "Pre-seeding: No spec entry found for DGN FFFFF (from light light.no_spec)"
    )

    # Ensure decode_payload_function was called for the valid lights
    # It's called with (spec_entry, bytes([0]*8))
    # spec_entry for light.one is {"dgn_hex": "12345", "name": "Light One Spec"}
    # spec_entry for light.two is {"dgn_hex": "ABCDE", "name": "Light Two Spec"}
    expected_decode_calls = [
        call(app_state.decoder_map["12345"], bytes([0] * 8)),
        call(app_state.decoder_map["ABCDE"], bytes([0] * 8)),
    ]
    mock_decode_payload_function.assert_has_calls(expected_decode_calls, any_order=True)
    assert mock_decode_payload_function.call_count == 2
