"""
Tests for J1939 to RV-C protocol bridge functionality.

This module tests the bidirectional translation between J1939 and RV-C protocols.
"""

from unittest.mock import Mock

import pytest

from backend.core.config import J1939Settings, Settings
from backend.integrations.j1939.bridge import EntityMapping, J1939ProtocolBridge
from backend.integrations.j1939.decoder import J1939Message, SystemType


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    j1939_config = Mock(spec=J1939Settings)
    j1939_config.enable_rvc_bridge = True
    j1939_config.bridge_engine_data = True
    j1939_config.bridge_transmission_data = True
    settings.j1939 = j1939_config
    return settings


@pytest.fixture
async def protocol_bridge(mock_settings):
    """Create protocol bridge instance for testing."""
    bridge = J1939ProtocolBridge(mock_settings)
    await bridge.startup()
    return bridge


class TestJ1939ProtocolBridge:
    """Test cases for J1939ProtocolBridge class."""

    @pytest.mark.asyncio
    async def test_bridge_initialization(self, protocol_bridge):
        """Test that bridge initializes correctly."""
        assert protocol_bridge is not None
        status = protocol_bridge.get_bridge_status()
        assert status["active"] is True
        assert status["enabled"] is True
        assert status["entity_mappings"] > 0

    @pytest.mark.asyncio
    async def test_engine_data_bridging(self, protocol_bridge):
        """Test bridging of engine data from J1939 to RV-C."""
        # Create mock J1939 engine message
        j1939_message = J1939Message(
            pgn=61444,  # Electronic Engine Controller 1
            source_address=0xF9,
            data=bytes([0x00, 0x80, 0x00, 0xE0, 0x2E, 0xF9, 0x00, 0x80]),
            priority=3,
            system_type=SystemType.ENGINE,
            decoded_signals={
                "engine_speed": 1500.0,
                "actual_engine_torque_percent": 25.0,
                "engine_demand_torque_percent": 30.0,
            },
            raw_signals={
                "engine_speed": 12000,
                "actual_engine_torque_percent": 150,
                "engine_demand_torque_percent": 155,
            },
            timestamp=1234567890.0,
        )

        # Bridge the message
        bridged_data = protocol_bridge.bridge_j1939_to_rvc(j1939_message)

        assert bridged_data is not None
        assert bridged_data.source_protocol == "j1939"
        assert bridged_data.target_protocol == "rvc"
        assert bridged_data.entity_id == "engine_primary"

        # Check translated data
        rvc_data = bridged_data.translated_data
        assert "dgn_hex" in rvc_data
        assert "signals" in rvc_data
        assert "engine_speed" in rvc_data["signals"]

    @pytest.mark.asyncio
    async def test_transmission_data_bridging(self, protocol_bridge):
        """Test bridging of transmission data from J1939 to RV-C."""
        # Create mock J1939 transmission message
        j1939_message = J1939Message(
            pgn=61443,  # Electronic Transmission Controller 1
            source_address=0xF8,
            data=bytes([0x64, 0x00, 0x00, 0x03, 0x04, 0x00, 0x00, 0x00]),
            priority=3,
            system_type=SystemType.TRANSMISSION,
            decoded_signals={
                "transmission_current_gear": 3,
                "transmission_selected_gear": 4,
                "transmission_actual_gear_ratio": 2.5,
            },
            raw_signals={
                "transmission_current_gear": 128,  # 3 + 125
                "transmission_selected_gear": 129,  # 4 + 125
                "transmission_actual_gear_ratio": 2500,
            },
            timestamp=1234567890.0,
        )

        # Bridge the message
        bridged_data = protocol_bridge.bridge_j1939_to_rvc(j1939_message)

        assert bridged_data is not None
        assert bridged_data.entity_id == "transmission_primary"
        assert "signals" in bridged_data.translated_data
        assert "current_gear" in bridged_data.translated_data["signals"]

    @pytest.mark.asyncio
    async def test_rvc_to_j1939_command_bridging(self, protocol_bridge):
        """Test bridging of RV-C commands to J1939 format."""
        # Test command for engine
        rvc_command = {
            "engine_speed": 1800.0,
            "engine_load": 50.0,
        }

        j1939_data = protocol_bridge.bridge_rvc_to_j1939("engine_primary", rvc_command)

        assert j1939_data is not None
        assert "pgn" in j1939_data
        assert j1939_data["pgn"] == 61444
        assert "signals" in j1939_data

    @pytest.mark.asyncio
    async def test_unknown_entity_bridging(self, protocol_bridge):
        """Test bridging with unknown entity ID."""
        # Create message for unknown PGN
        j1939_message = J1939Message(
            pgn=99999,  # Unknown PGN
            source_address=0xF9,
            data=bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]),
            priority=6,
            system_type=SystemType.UNKNOWN,
            decoded_signals={},
            raw_signals={},
        )

        # Should return None for unknown mapping
        bridged_data = protocol_bridge.bridge_j1939_to_rvc(j1939_message)
        assert bridged_data is None

    @pytest.mark.asyncio
    async def test_bridge_statistics(self, protocol_bridge):
        """Test bridge statistics tracking."""
        initial_status = protocol_bridge.get_bridge_status()
        initial_bridged = initial_status["statistics"]["messages_bridged"]

        # Create and bridge a message
        j1939_message = J1939Message(
            pgn=61444,
            source_address=0xF9,
            data=bytes([0x00, 0x80, 0x00, 0xE0, 0x2E, 0xF9, 0x00, 0x80]),
            priority=3,
            system_type=SystemType.ENGINE,
            decoded_signals={"engine_speed": 1500.0},
            raw_signals={"engine_speed": 12000},
        )

        protocol_bridge.bridge_j1939_to_rvc(j1939_message)

        # Check statistics updated
        updated_status = protocol_bridge.get_bridge_status()
        updated_bridged = updated_status["statistics"]["messages_bridged"]
        assert updated_bridged == initial_bridged + 1

    @pytest.mark.asyncio
    async def test_entity_mappings_retrieval(self, protocol_bridge):
        """Test entity mappings retrieval."""
        mappings = protocol_bridge.get_entity_mappings()

        assert isinstance(mappings, dict)
        assert len(mappings) > 0

        # Check for expected engine mapping
        assert "engine_primary" in mappings
        engine_mapping = mappings["engine_primary"]
        assert engine_mapping["j1939_pgn"] == 61444
        assert engine_mapping["system_type"] == "engine"
        assert "signal_mappings" in engine_mapping

    @pytest.mark.asyncio
    async def test_bridge_shutdown(self, protocol_bridge):
        """Test bridge shutdown functionality."""
        assert protocol_bridge._active is True

        await protocol_bridge.shutdown()

        assert protocol_bridge._active is False

        # Should return None when inactive
        j1939_message = J1939Message(
            pgn=61444,
            source_address=0xF9,
            data=bytes([0x00, 0x80, 0x00, 0xE0, 0x2E, 0xF9, 0x00, 0x80]),
            priority=3,
            system_type=SystemType.ENGINE,
            decoded_signals={"engine_speed": 1500.0},
            raw_signals={"engine_speed": 12000},
        )

        bridged_data = protocol_bridge.bridge_j1939_to_rvc(j1939_message)
        assert bridged_data is None


class TestEntityMapping:
    """Test cases for EntityMapping data structure."""

    def test_entity_mapping_creation(self):
        """Test EntityMapping creation."""
        mapping = EntityMapping(
            j1939_pgn=61444,
            rvc_dgn_hex="1FFFF",
            entity_id="engine_test",
            system_type=SystemType.ENGINE,
            signal_mappings={"engine_speed": "speed"},
            scaling_factors={"engine_speed": 1.0},
            active=True,
        )

        assert mapping.j1939_pgn == 61444
        assert mapping.rvc_dgn_hex == "1FFFF"
        assert mapping.entity_id == "engine_test"
        assert mapping.system_type == SystemType.ENGINE
        assert mapping.signal_mappings["engine_speed"] == "speed"
        assert mapping.scaling_factors["engine_speed"] == 1.0
        assert mapping.active is True
