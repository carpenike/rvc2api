"""
Tests for Pydantic models defined in `core_daemon.models`.

This module verifies the correct behavior of various data models, including:
- Successful instantiation with valid data.
- Validation errors for missing required fields or invalid data types/values.
- Correct default values for optional fields.
- Handling of aliased fields.
- Correct structure for nested models and lists of models.
"""

import pytest
from core_daemon.models import (
    AllCANStats,
    BulkLightControlResponse,
    CANInterfaceStats,
    ControlCommand,
    ControlEntityResponse,
    Entity,
    SuggestedMapping,
    UnknownPGNEntry,
    UnmappedEntryModel,
)
from pydantic import ValidationError


def test_entity_model_success():
    """Tests successful creation of an Entity model with all fields populated."""
    data = {
        "entity_id": "light.living_room",
        "value": {"status": "on", "brightness_pct": "50"},
        "raw": {"operating_status": 100, "instance": 1},
        "state": "on",
        "timestamp": 1678886400.0,
        "suggested_area": "Living Room",
        "device_type": "light",
        "capabilities": ["on_off", "brightness"],
        "friendly_name": "Living Room Light",
        "groups": ["all_lights", "living_room_lights"],
    }
    entity = Entity(**data)
    assert entity.entity_id == data["entity_id"]
    assert entity.value == data["value"]
    assert entity.raw == data["raw"]
    assert entity.state == data["state"]
    assert entity.timestamp == data["timestamp"]
    assert entity.suggested_area == data["suggested_area"]
    assert entity.device_type == data["device_type"]
    assert entity.capabilities == data["capabilities"]
    assert entity.friendly_name == data["friendly_name"]
    assert entity.groups == data["groups"]


def test_entity_model_missing_required_fields():
    """Tests that Entity model raises ValidationError for missing required fields."""
    data = {
        "value": {"status": "on"},
        "raw": {"operating_status": 100},
        "state": "on",
        "timestamp": 1678886400.0,
    }
    with pytest.raises(ValidationError) as excinfo:
        Entity(**data)
    assert "entity_id" in str(excinfo.value)


def test_entity_model_optional_fields_default():
    """Tests that Entity model assigns correct default values for optional fields."""
    data = {
        "entity_id": "sensor.temp",
        "value": {"temperature": "22.5"},
        "raw": {"temp_raw": 225},
        "state": "active",
        "timestamp": 1678886400.0,
    }
    entity = Entity(**data)
    assert entity.suggested_area == "Unknown"
    assert entity.device_type == "unknown"
    assert entity.capabilities == []
    assert entity.friendly_name is None
    assert entity.groups == []


# --- ControlCommand Model Tests ---


def test_control_command_set_on_success():
    """Tests successful creation of ControlCommand for 'set on' with brightness."""
    data = {"command": "set", "state": "on", "brightness": 75}
    cmd = ControlCommand(**data)
    assert cmd.command == "set"
    assert cmd.state == "on"
    assert cmd.brightness == 75


def test_control_command_set_off_success():
    """Tests successful creation of ControlCommand for 'set off'."""
    data = {"command": "set", "state": "off"}
    cmd = ControlCommand(**data)
    assert cmd.command == "set"
    assert cmd.state == "off"
    assert cmd.brightness is None


def test_control_command_toggle_success():
    """Tests successful creation of ControlCommand for 'toggle'."""
    data = {"command": "toggle"}
    cmd = ControlCommand(**data)
    assert cmd.command == "toggle"
    assert cmd.state is None
    assert cmd.brightness is None


def test_control_command_brightness_invalid_range():
    """Tests that ControlCommand raises ValidationError for out-of-range brightness."""
    data_too_high = {"command": "set", "state": "on", "brightness": 101}
    with pytest.raises(ValidationError) as excinfo_high:
        ControlCommand(**data_too_high)
    assert "brightness" in str(excinfo_high.value)  # Pydantic v2 uses field name

    data_too_low = {"command": "set", "state": "on", "brightness": -1}
    with pytest.raises(ValidationError) as excinfo_low:
        ControlCommand(**data_too_low)
    assert "brightness" in str(excinfo_low.value)  # Pydantic v2 uses field name


def test_control_command_missing_command():
    """Tests that ControlCommand raises ValidationError if 'command' field is missing."""
    data = {"state": "on"}
    with pytest.raises(ValidationError) as excinfo:
        ControlCommand(**data)
    assert "command" in str(excinfo.value)


# --- SuggestedMapping Model Tests ---


def test_suggested_mapping_success():
    """Tests successful creation of a SuggestedMapping model."""
    data = {"instance": "1", "name": "Main Light", "suggested_area": "Cabin"}
    mapping = SuggestedMapping(**data)
    assert mapping.instance == "1"
    assert mapping.name == "Main Light"
    assert mapping.suggested_area == "Cabin"


def test_suggested_mapping_optional_area():
    """Tests SuggestedMapping with optional 'suggested_area' not provided."""
    data = {"instance": "2", "name": "Secondary Light"}
    mapping = SuggestedMapping(**data)
    assert mapping.instance == "2"
    assert mapping.name == "Secondary Light"
    assert mapping.suggested_area is None


# --- UnmappedEntryModel Tests ---


def test_unmapped_entry_model_success():
    """Tests successful creation of UnmappedEntryModel with comprehensive data."""
    data = {
        "pgn_hex": "1EF00",
        "pgn_name": "Engine Parameters, Rapid Update",
        "dgn_hex": "FEEF",
        "dgn_name": "Some DGN Name",
        "instance": "0",
        "last_data_hex": "0102030405060708",
        "decoded_signals": {"rpm": 1500, "oil_pressure": "40 psi"},
        "first_seen_timestamp": 1678886400.0,
        "last_seen_timestamp": 1678886401.0,
        "count": 5,
        "suggestions": [{"instance": "1", "name": "Possible Engine"}],
        "spec_entry": {"id": "0x1EF00", "signals": []},
    }
    entry = UnmappedEntryModel(**data)
    assert entry.pgn_hex == data["pgn_hex"]
    assert entry.dgn_name == data["dgn_name"]
    # ... check other fields


def test_unmapped_entry_model_minimal():
    """Tests UnmappedEntryModel creation with only minimal required fields."""
    data = {
        "pgn_hex": "1F001",
        "dgn_hex": "F001",
        "instance": "default",
        "last_data_hex": "AABBCCDD",
        "first_seen_timestamp": 1678886400.0,
        "last_seen_timestamp": 1678886400.0,
        "count": 1,
    }
    entry = UnmappedEntryModel(**data)
    assert entry.pgn_hex == data["pgn_hex"]
    assert entry.pgn_name is None
    assert entry.decoded_signals is None
    assert entry.suggestions is None
    assert entry.spec_entry is None


# --- UnknownPGNEntry Tests ---


def test_unknown_pgn_entry_success():
    """Tests successful creation of an UnknownPGNEntry model."""
    data = {
        "arbitration_id_hex": "18FFD1F9",
        "first_seen_timestamp": 1678886400.0,
        "last_seen_timestamp": 1678886405.0,
        "count": 10,
        "last_data_hex": "1122334455667788",
    }
    entry = UnknownPGNEntry(**data)
    assert entry.arbitration_id_hex == data["arbitration_id_hex"]
    assert entry.count == data["count"]


# --- BulkLightControlResponse Tests ---


def test_bulk_light_control_response_success():
    """Tests successful creation of BulkLightControlResponse with errors and details."""
    data = {
        "status": "partial_error",
        "message": "Some lights failed",
        "action": "set",
        "group": "interior",
        "lights_processed": 5,
        "lights_commanded": 3,
        "errors": [{"entity_id": "light.kitchen", "detail": "Failed to send"}],
        "details": [{"entity_id": "light.living_room", "status": "sent"}],
    }
    response = BulkLightControlResponse(**data)
    assert response.status == data["status"]
    assert response.lights_commanded == data["lights_commanded"]
    assert len(response.errors) == 1


def test_bulk_light_control_response_defaults():
    """Tests BulkLightControlResponse with default values for optional fields."""
    data = {
        "status": "success",
        "message": "All good",
        "action": "toggle",
        "lights_processed": 2,
        "lights_commanded": 2,
    }
    response = BulkLightControlResponse(**data)
    assert response.group is None
    assert response.errors == []
    assert response.details == []


# --- ControlEntityResponse Tests ---


def test_control_entity_response_success():
    """Tests successful creation of a ControlEntityResponse model."""
    data = {
        "status": "sent",
        "entity_id": "light.bedroom",
        "command": "set",
        "brightness": 50,
        "action": "Set ON to 50%",
        "state": "on",
    }
    response = ControlEntityResponse(**data)
    assert response.status == data["status"]
    assert response.entity_id == data["entity_id"]
    assert response.brightness == 50


# --- CANInterfaceStats Tests ---


def test_can_interface_stats_success():
    """Tests successful creation of CANInterfaceStats, including aliased field."""
    data = {
        "name": "can0",
        "state": "ERROR-ACTIVE",
        "bitrate": 250000,
        "tx_packets": 100,
        "rx_packets": 200,
        "clock": 8000000,  # Testing alias
    }
    stats = CANInterfaceStats(**data)
    assert stats.name == "can0"
    assert stats.state == "ERROR-ACTIVE"
    assert stats.bitrate == 250000
    assert stats.clock_freq == 8000000  # Check aliased field


def test_can_interface_stats_minimal():
    """Tests CANInterfaceStats creation with only the 'name' field."""
    data = {"name": "can1"}
    stats = CANInterfaceStats(**data)
    assert stats.name == "can1"
    assert stats.state is None


# --- AllCANStats Tests ---


def test_all_can_stats_success():
    """Tests successful creation of AllCANStats with multiple CAN interfaces."""
    can0_data = {"name": "can0", "state": "UP", "bitrate": 500000}
    can1_data = {"name": "can1", "state": "DOWN"}
    data = {
        "interfaces": {
            "can0": CANInterfaceStats(**can0_data),
            "can1": CANInterfaceStats(**can1_data),
        }
    }
    all_stats = AllCANStats(**data)
    assert len(all_stats.interfaces) == 2
    assert all_stats.interfaces["can0"].name == "can0"
    assert all_stats.interfaces["can0"].bitrate == 500000
    assert all_stats.interfaces["can1"].state == "DOWN"


def test_all_can_stats_empty():
    """Tests AllCANStats creation with an empty 'interfaces' dictionary."""
    data = {"interfaces": {}}
    all_stats = AllCANStats(**data)
    assert len(all_stats.interfaces) == 0
