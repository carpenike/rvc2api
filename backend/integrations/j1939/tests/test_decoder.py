"""
Tests for J1939 decoder functionality.

This module contains comprehensive tests for the J1939 decoder,
ensuring proper message decoding, signal extraction, and error handling.
"""

from unittest.mock import Mock

import pytest

from backend.core.config import J1939Settings, Settings
from backend.integrations.j1939.decoder import (
    J1939Decoder,
    J1939Message,
    MessagePriority,
    SystemType,
)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    j1939_config = Mock(spec=J1939Settings)
    j1939_config.enabled = True
    j1939_config.enable_cummins_extensions = True
    j1939_config.enable_allison_extensions = True
    j1939_config.enable_chassis_extensions = True
    j1939_config.enable_address_validation = True
    j1939_config.priority_critical_pgns = [61444, 65262, 65265]
    j1939_config.priority_high_pgns = [65266, 65272, 61443]
    settings.j1939 = j1939_config
    return settings


@pytest.fixture
def j1939_decoder(mock_settings):
    """Create J1939 decoder instance for testing."""
    return J1939Decoder(mock_settings)


class TestJ1939Decoder:
    """Test cases for J1939Decoder class."""

    def test_decoder_initialization(self, j1939_decoder):
        """Test that decoder initializes correctly."""
        assert j1939_decoder is not None
        assert len(j1939_decoder.get_supported_pgns()) > 0

    def test_standard_pgn_support(self, j1939_decoder):
        """Test that standard J1939 PGNs are supported."""
        supported_pgns = j1939_decoder.get_supported_pgns()

        # Check for key standard PGNs
        assert 61444 in supported_pgns  # Electronic Engine Controller 1
        assert 65262 in supported_pgns  # Engine Temperature 1
        assert 65265 in supported_pgns  # Vehicle Speed
        assert 65266 in supported_pgns  # Fuel Economy

    def test_engine_speed_decoding(self, j1939_decoder):
        """Test decoding of engine speed message (PGN 61444)."""
        # Sample data for PGN 61444 (Electronic Engine Controller 1)
        # Engine speed: 1500 RPM (1500 / 0.125 = 12000 = 0x2EE0)
        data = bytes(
            [
                0x00,  # Engine torque mode
                0x80,  # Actual engine torque percent (-125 + 128 = 3%)
                0x00,  # Reserved
                0xE0,
                0x2E,  # Engine speed (12000 * 0.125 = 1500 RPM)
                0xF9,  # Source address
                0x00,  # Engine starter mode
                0x80,  # Engine demand torque percent
            ]
        )

        message = j1939_decoder.decode_message(
            pgn=61444, source_address=0xF9, data=data, priority=3
        )

        assert message is not None
        assert message.pgn == 61444
        assert message.system_type == SystemType.ENGINE
        assert "engine_speed" in message.decoded_signals
        assert abs(message.decoded_signals["engine_speed"] - 1500.0) < 0.1

    def test_engine_temperature_decoding(self, j1939_decoder):
        """Test decoding of engine temperature message (PGN 65262)."""
        # Sample data for PGN 65262 (Engine Temperature 1)
        # Coolant temp: 90°C (90 + 40 = 130 = 0x82)
        data = bytes(
            [
                0x82,  # Engine coolant temp (130 - 40 = 90°C)
                0x7D,  # Fuel temp (125 - 40 = 85°C)
                0x00,
                0x2C,  # Engine oil temp (11264 * 0.03125 - 273 = 79°C)
                0x00,
                0x2C,  # Turbo oil temp
                0x82,  # Engine intercooler temp
                0x64,  # Engine intercooler thermostat opening (100 * 0.4 = 40%)
            ]
        )

        message = j1939_decoder.decode_message(
            pgn=65262, source_address=0xF9, data=data, priority=6
        )

        assert message is not None
        assert message.pgn == 65262
        assert message.system_type == SystemType.ENGINE
        assert "engine_coolant_temp" in message.decoded_signals
        assert abs(message.decoded_signals["engine_coolant_temp"] - 90.0) < 0.1

    def test_unknown_pgn_handling(self, j1939_decoder):
        """Test handling of unknown PGN."""
        unknown_pgn = 99999
        data = bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])

        message = j1939_decoder.decode_message(pgn=unknown_pgn, source_address=0xF9, data=data)

        assert message is None

    def test_insufficient_data_handling(self, j1939_decoder):
        """Test handling of insufficient data length."""
        # PGN 61444 requires 8 bytes, provide only 4
        data = bytes([0x00, 0x01, 0x02, 0x03])

        message = j1939_decoder.decode_message(pgn=61444, source_address=0xF9, data=data)

        assert message is None

    def test_message_priority_classification(self, j1939_decoder):
        """Test message priority classification."""
        # Test critical priority
        assert j1939_decoder.get_message_priority(61444) == MessagePriority.HIGH
        assert j1939_decoder.get_message_priority(65262) == MessagePriority.CRITICAL

        # Test high priority
        assert j1939_decoder.get_message_priority(65266) == MessagePriority.HIGH

        # Test unknown PGN (should default to normal)
        assert j1939_decoder.get_message_priority(99999) == MessagePriority.NORMAL

    def test_system_type_classification(self, j1939_decoder):
        """Test system type classification."""
        assert j1939_decoder.get_system_type(61444) == SystemType.ENGINE
        assert j1939_decoder.get_system_type(65262) == SystemType.ENGINE
        assert j1939_decoder.get_system_type(65265) == SystemType.CHASSIS
        assert j1939_decoder.get_system_type(65266) == SystemType.FUEL
        assert j1939_decoder.get_system_type(99999) == SystemType.UNKNOWN

    def test_source_address_validation(self, j1939_decoder):
        """Test J1939 source address validation."""
        # Valid addresses
        assert j1939_decoder.validate_source_address(0) is True
        assert j1939_decoder.validate_source_address(128) is True
        assert j1939_decoder.validate_source_address(247) is True

        # Invalid addresses
        assert j1939_decoder.validate_source_address(248) is False
        assert j1939_decoder.validate_source_address(255) is False
        assert j1939_decoder.validate_source_address(-1) is False

    def test_pgn_info_retrieval(self, j1939_decoder):
        """Test PGN information retrieval."""
        info = j1939_decoder.get_pgn_info(61444)

        assert info is not None
        assert info["pgn"] == 61444
        assert info["name"] == "Electronic Engine Controller 1"
        assert info["system_type"] == "engine"
        assert "signals" in info
        assert len(info["signals"]) > 0

    def test_cummins_extensions(self, j1939_decoder):
        """Test Cummins-specific PGN support."""
        supported_pgns = j1939_decoder.get_supported_pgns()

        # Check for Cummins-specific PGNs
        assert 61445 in supported_pgns  # Cummins Electronic Engine Controller 3
        assert 65110 in supported_pgns  # Cummins Aftertreatment DEF Tank

    def test_allison_extensions(self, j1939_decoder):
        """Test Allison transmission-specific PGN support."""
        supported_pgns = j1939_decoder.get_supported_pgns()

        # Check for Allison-specific PGNs
        assert 61443 in supported_pgns  # Allison Electronic Transmission Controller 1
        assert 65272 in supported_pgns  # Allison Electronic Transmission Controller 2

    def test_chassis_extensions(self, j1939_decoder):
        """Test chassis-specific PGN support."""
        supported_pgns = j1939_decoder.get_supported_pgns()

        # Check for chassis-specific PGNs
        assert 65098 in supported_pgns  # Chassis Electronic Control Unit
        assert 65097 in supported_pgns  # Anti-lock Braking System


class TestJ1939Message:
    """Test cases for J1939Message data structure."""

    def test_message_creation(self):
        """Test J1939Message creation."""
        message = J1939Message(
            pgn=61444,
            source_address=0xF9,
            data=bytes([0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07]),
            priority=3,
            system_type=SystemType.ENGINE,
            decoded_signals={"engine_speed": 1500.0},
            raw_signals={"engine_speed": 12000},
            manufacturer="Standard",
            timestamp=1234567890.0,
        )

        assert message.pgn == 61444
        assert message.source_address == 0xF9
        assert message.priority == 3
        assert message.system_type == SystemType.ENGINE
        assert message.decoded_signals["engine_speed"] == 1500.0
        assert message.raw_signals["engine_speed"] == 12000
        assert message.manufacturer == "Standard"
        assert message.timestamp == 1234567890.0


class TestSignalExtraction:
    """Test cases for signal bit extraction functionality."""

    def test_extract_signal_bits(self, j1939_decoder):
        """Test bit extraction from CAN data."""
        # Test data: 0x12345678
        data = bytes([0x78, 0x56, 0x34, 0x12])  # Little-endian

        # Extract bits 8-15 (should be 0x56)
        result = j1939_decoder._extract_signal_bits(data, 8, 8)
        assert result == 0x56

        # Extract bits 0-7 (should be 0x78)
        result = j1939_decoder._extract_signal_bits(data, 0, 8)
        assert result == 0x78

        # Extract bits 16-31 (should be 0x1234)
        result = j1939_decoder._extract_signal_bits(data, 16, 16)
        assert result == 0x1234

    def test_extract_signal_bits_boundary(self, j1939_decoder):
        """Test signal extraction at data boundaries."""
        data = bytes([0xFF, 0xFF])

        # Extract all bits
        result = j1939_decoder._extract_signal_bits(data, 0, 16)
        assert result == 0xFFFF

        # Extract single bit
        result = j1939_decoder._extract_signal_bits(data, 0, 1)
        assert result == 1

    def test_extract_signal_bits_overflow(self, j1939_decoder):
        """Test signal extraction with overflow."""
        data = bytes([0xFF])

        # Try to extract beyond data length
        with pytest.raises(ValueError):
            j1939_decoder._extract_signal_bits(data, 0, 16)  # Only 8 bits available
