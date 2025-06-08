"""
Tests for Spartan K2 Feature Integration

Comprehensive test suite covering:
- Feature lifecycle management (startup, shutdown, health monitoring)
- Integration with application configuration system
- Real-time message processing and status reporting
- Safety interlock validation and system diagnostics
- Error handling and graceful degradation

Follows established patterns from RV-C, J1939, and Firefly feature tests.
"""

import struct
import time
from unittest.mock import Mock, patch

import pytest

from backend.core.config import Settings
from backend.integrations.j1939.spartan_k2_extensions import SpartanK2SystemType
from backend.integrations.j1939.spartan_k2_feature import SpartanK2Feature


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)

    # Mock Spartan K2 configuration
    spartan_config = Mock()
    spartan_config.enabled = True
    spartan_config.enable_safety_interlocks = True
    spartan_config.enable_advanced_diagnostics = True
    spartan_config.enable_brake_monitoring = True
    spartan_config.enable_suspension_control = True
    spartan_config.enable_steering_monitoring = True
    spartan_config.chassis_interface = "chassis"
    spartan_config.brake_pressure_threshold = 80.0
    spartan_config.level_differential_threshold = 15.0
    spartan_config.steering_pressure_threshold = 1000.0
    spartan_config.max_steering_angle = 720.0

    settings.spartan_k2 = spartan_config
    return settings


@pytest.fixture
def spartan_feature(mock_settings):
    """Create a Spartan K2 feature for testing."""
    # Create with default parameters and some config
    config = {
        "enable_safety_interlocks": True,
        "enable_advanced_diagnostics": True,
        "chassis_interface": "chassis",
    }
    return SpartanK2Feature(enabled=True, config=config)


class TestSpartanK2FeatureLifecycle:
    """Test cases for feature lifecycle management."""

    def test_feature_properties(self, spartan_feature):
        """Test basic feature properties."""
        assert spartan_feature.name == "spartan_k2"
        assert spartan_feature.friendly_name == "Spartan K2 Chassis"
        assert spartan_feature.dependencies == ["j1939"]

    async def test_feature_startup_success(self, spartan_feature):
        """Test successful feature startup."""
        # Startup should initialize decoder and system health tracking
        await spartan_feature.startup()

        # Verify decoder is initialized
        assert spartan_feature._decoder is not None

        # Verify system health is initialized
        assert len(spartan_feature._system_health) > 0
        for system_type in SpartanK2SystemType:
            assert system_type.value in spartan_feature._system_health

    async def test_feature_startup_failure_handling(self, mock_settings):
        """Test feature startup failure handling."""
        # Create feature without proper configuration to cause startup failure
        feature = SpartanK2Feature(enabled=True)

        # Should raise exception on startup failure
        with pytest.raises(RuntimeError):
            await feature.startup()

    async def test_feature_shutdown(self, spartan_feature):
        """Test feature shutdown."""
        # Start up first
        await spartan_feature.startup()
        assert spartan_feature._decoder is not None

        # Shutdown should clean up resources
        await spartan_feature.shutdown()
        assert spartan_feature._decoder is None
        assert len(spartan_feature._system_health) == 0

    def test_health_check_no_decoder(self, spartan_feature):
        """Test health check when decoder is not available."""
        # Without startup, decoder should be None
        assert spartan_feature.is_healthy() is False

    async def test_health_check_with_decoder(self, spartan_feature):
        """Test health check with operational decoder."""
        await spartan_feature.startup()

        # With fresh startup and no errors, should be healthy
        assert spartan_feature.is_healthy() is True

    async def test_health_check_with_safety_violations(self, spartan_feature):
        """Test health check with safety violations."""
        await spartan_feature.startup()

        # Mock safety violations in critical systems
        with patch.object(spartan_feature._decoder, "get_system_status") as mock_status:
            mock_status.return_value = {"safety_status": "violation"}
            assert spartan_feature.is_healthy() is False


class TestSpartanK2MessageProcessing:
    """Test cases for message processing functionality."""

    async def test_message_decoding_success(self, spartan_feature):
        """Test successful message decoding."""
        await spartan_feature.startup()

        # Create test brake system message
        pgn = 65280
        source_address = 11
        data = struct.pack("<HBBBBBB", 240, 0x01, 0x01, 0xFF, 50, 55, 80)
        timestamp = time.time()

        result = spartan_feature.decode_message(pgn, source_address, data, timestamp=timestamp)

        assert result is not None
        assert result["pgn"] == pgn
        assert result["source_address"] == source_address
        assert result["system_type"] == "brakes"
        assert result["manufacturer"] == "Spartan"
        assert result["chassis_model"] == "K2"
        assert "decoded_signals" in result
        assert "safety_interlocks" in result
        assert "diagnostic_codes" in result

        # Verify statistics updated
        assert spartan_feature._message_count == 1
        assert spartan_feature._last_message_time == timestamp

    async def test_message_decoding_unknown_pgn(self, spartan_feature):
        """Test message decoding with unknown PGN."""
        await spartan_feature.startup()

        # Unknown PGN should return None
        result = spartan_feature.decode_message(99999, 10, b"\x00\x01\x02\x03\x04\x05\x06\x07")
        assert result is None

    def test_message_decoding_no_decoder(self, spartan_feature):
        """Test message decoding when decoder is not available."""
        # Without startup, decoder should be None
        result = spartan_feature.decode_message(65280, 10, b"\x00" * 8)
        assert result is None

    async def test_message_decoding_error_handling(self, spartan_feature):
        """Test error handling during message decoding."""
        await spartan_feature.startup()

        # Mock decoder to raise exception
        with patch.object(
            spartan_feature._decoder, "decode_message", side_effect=Exception("Test error")
        ):
            result = spartan_feature.decode_message(65280, 10, b"\x00" * 8)
            assert result is None
            assert spartan_feature._error_count == 1

    async def test_system_health_update(self, spartan_feature):
        """Test system health tracking updates."""
        await spartan_feature.startup()

        # Create message with safety violations
        pgn = 65280  # Brake system
        data = struct.pack("<HBBBBBB", 100, 0x00, 0x00, 0xFF, 80, 85, 95)  # Low pressure, no ABS
        timestamp = time.time()

        spartan_feature.decode_message(pgn, 11, data, timestamp=timestamp)

        # Check system health was updated
        brake_health = spartan_feature._system_health.get("brakes")
        assert brake_health is not None
        assert brake_health["last_update"] == timestamp
        assert brake_health["message_count"] == 1


class TestSpartanK2StatusReporting:
    """Test cases for status and diagnostic reporting."""

    def test_get_status_no_decoder(self, spartan_feature):
        """Test status retrieval when decoder is not available."""
        status = spartan_feature.get_status()

        assert status["enabled"] is False
        assert status["status"] == "not_initialized"
        assert "error" in status

    async def test_get_status_with_decoder(self, spartan_feature):
        """Test comprehensive status retrieval."""
        await spartan_feature.startup()

        status = spartan_feature.get_status()

        assert status["enabled"] is True
        assert status["status"] == "operational"
        assert "decoder_info" in status
        assert "systems" in status
        assert "statistics" in status
        assert "health" in status
        assert "configuration" in status

        # Verify statistics structure
        stats = status["statistics"]
        assert "messages_processed" in stats
        assert "errors" in stats
        assert "error_rate" in stats
        assert "last_message_time" in stats

        # Verify systems status
        systems = status["systems"]
        for system_type in SpartanK2SystemType:
            assert system_type.value in systems

    async def test_get_system_diagnostics_success(self, spartan_feature):
        """Test system-specific diagnostics retrieval."""
        await spartan_feature.startup()

        # Test valid system type
        diagnostics = spartan_feature.get_system_diagnostics("brakes")

        assert "error" not in diagnostics
        assert "system_type" in diagnostics
        assert diagnostics["system_type"] == "brakes"

    async def test_get_system_diagnostics_invalid_system(self, spartan_feature):
        """Test diagnostics retrieval for invalid system type."""
        await spartan_feature.startup()

        diagnostics = spartan_feature.get_system_diagnostics("invalid_system")
        assert "error" in diagnostics
        assert "Unknown system type" in diagnostics["error"]

    def test_get_system_diagnostics_no_decoder(self, spartan_feature):
        """Test diagnostics retrieval when decoder is not available."""
        diagnostics = spartan_feature.get_system_diagnostics("brakes")
        assert "error" in diagnostics
        assert "Decoder not available" in diagnostics["error"]


class TestSpartanK2SafetyValidation:
    """Test cases for safety interlock validation."""

    async def test_validate_safety_interlocks_success(self, spartan_feature):
        """Test safety validation with no violations."""
        await spartan_feature.startup()

        # Process messages with good safety conditions
        good_messages = [
            (65280, struct.pack("<HBBBBBB", 240, 0x01, 0x01, 0xFF, 50, 55, 80)),  # Good brakes
            (
                65281,
                struct.pack("<BBBBBBBB", 125, 130, 80, 0x00, 0x02, 10, 12, 50),
            ),  # Good suspension
            (65282, struct.pack("<HHBBBB", 320, 16000, 50, 0x00, 0x00, 70)),  # Good steering
        ]

        timestamp = time.time()
        for pgn, data in good_messages:
            spartan_feature.decode_message(pgn, 11, data, timestamp=timestamp)

        safety_status = spartan_feature.validate_safety_interlocks()

        assert "error" not in safety_status
        assert safety_status["overall_status"] == "ok"
        assert len(safety_status["critical_violations"]) == 0
        assert len(safety_status["systems_checked"]) == 3
        assert any("normally" in rec for rec in safety_status["recommendations"])

    async def test_validate_safety_interlocks_violations(self, spartan_feature):
        """Test safety validation with violations."""
        await spartan_feature.startup()

        # Process message with safety violations (low brake pressure)
        unsafe_brake_data = struct.pack("<HBBBBBB", 100, 0x00, 0x00, 0xFF, 80, 85, 95)
        spartan_feature.decode_message(65280, 11, unsafe_brake_data, timestamp=time.time())

        safety_status = spartan_feature.validate_safety_interlocks()

        assert safety_status["overall_status"] == "critical"
        assert len(safety_status["critical_violations"]) > 0
        assert any("Immediate attention" in rec for rec in safety_status["recommendations"])

    async def test_validate_safety_interlocks_warnings(self, spartan_feature):
        """Test safety validation with warnings (diagnostic codes)."""
        await spartan_feature.startup()

        # Process diagnostic message with trouble codes
        diagnostic_data = struct.pack("<HBBHH", 1234, 15, 85, 1500, 45000)
        spartan_feature.decode_message(65284, 55, diagnostic_data, timestamp=time.time())

        safety_status = spartan_feature.validate_safety_interlocks()

        assert safety_status["overall_status"] in ["warning", "ok"]  # Depends on other systems
        assert len(safety_status["warnings"]) > 0
        assert any("diagnostic codes" in warning for warning in safety_status["warnings"])

    def test_validate_safety_interlocks_no_decoder(self, spartan_feature):
        """Test safety validation when decoder is not available."""
        safety_status = spartan_feature.validate_safety_interlocks()
        assert "error" in safety_status
        assert "Decoder not available" in safety_status["error"]


class TestSpartanK2ErrorHandling:
    """Test cases for error handling and edge cases."""

    async def test_error_rate_tracking(self, spartan_feature):
        """Test error rate tracking affects health status."""
        await spartan_feature.startup()

        # Generate many errors to exceed threshold
        spartan_feature._message_count = 200
        spartan_feature._error_count = 25  # 12.5% error rate (>10% threshold)

        assert spartan_feature.is_healthy() is False

    async def test_decoder_exception_handling(self, spartan_feature):
        """Test handling of decoder exceptions."""
        await spartan_feature.startup()

        # Mock decoder methods to raise exceptions
        with patch.object(
            spartan_feature._decoder, "get_system_status", side_effect=Exception("Test error")
        ):
            diagnostics = spartan_feature.get_system_diagnostics("brakes")
            assert "error" in diagnostics

        with patch.object(
            spartan_feature._decoder, "get_system_status", side_effect=Exception("Test error")
        ):
            safety_status = spartan_feature.validate_safety_interlocks()
            assert "error" in safety_status

    async def test_configuration_access_with_none_config(self, spartan_feature):
        """Test handling when spartan_config is None."""
        spartan_feature.spartan_config = None
        await spartan_feature.startup()

        status = spartan_feature.get_status()
        config = status["configuration"]

        # Should use default values when config is None
        assert config["safety_interlocks_enabled"] is True
        assert config["advanced_diagnostics_enabled"] is True
        assert config["chassis_interface"] == "chassis"


class TestSpartanK2Integration:
    """Integration tests for real-world scenarios."""

    async def test_complete_operational_cycle(self, spartan_feature):
        """Test complete operational cycle with multiple message types."""
        # Startup
        await spartan_feature.startup()
        assert spartan_feature.is_healthy()

        # Process various message types
        message_sequence = [
            (65280, struct.pack("<HBBBBBB", 240, 0x01, 0x01, 0xFF, 50, 55, 80)),
            (65281, struct.pack("<BBBBBBBB", 125, 130, 80, 0x00, 0x02, 10, 12, 50)),
            (65282, struct.pack("<HHBBBB", 320, 16000, 50, 0x00, 0x00, 70)),
            (65284, struct.pack("<HBBHH", 0, 45, 92, 1200, 42000)),
        ]

        timestamp = time.time()
        decoded_count = 0
        for pgn, data in message_sequence:
            result = spartan_feature.decode_message(pgn, 11, data, timestamp=timestamp)
            if result:
                decoded_count += 1
            timestamp += 0.1

        assert decoded_count == 4
        assert spartan_feature._message_count == 4
        assert spartan_feature._error_count == 0

        # Verify comprehensive status
        status = spartan_feature.get_status()
        assert status["statistics"]["error_rate"] == 0.0
        assert len(status["systems"]) == len(SpartanK2SystemType)

        # Verify safety validation
        safety_status = spartan_feature.validate_safety_interlocks()
        assert safety_status["overall_status"] == "ok"

        # Shutdown
        await spartan_feature.shutdown()
        assert spartan_feature._decoder is None

    async def test_high_message_volume_performance(self, spartan_feature):
        """Test performance with high message volume."""
        await spartan_feature.startup()

        # Process many messages rapidly
        brake_data = struct.pack("<HBBBBBB", 240, 0x01, 0x01, 0xFF, 50, 55, 80)

        start_time = time.time()
        message_count = 100

        for i in range(message_count):
            result = spartan_feature.decode_message(
                65280, 11, brake_data, timestamp=start_time + i * 0.01
            )
            assert result is not None

        end_time = time.time()
        processing_time = end_time - start_time

        # Verify performance (should process 100 messages in reasonable time)
        assert processing_time < 1.0  # Less than 1 second for 100 messages
        assert spartan_feature._message_count == message_count
        assert spartan_feature._error_count == 0
