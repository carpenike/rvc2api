"""
Test suite for Firefly RV Systems Extensions

This comprehensive test suite validates:
- Firefly decoder functionality
- Firefly encoder functionality
- Message multiplexing
- Safety interlock validation
- CAN Detective integration
- Configuration management
"""

import time
from unittest.mock import patch

import pytest

from backend.core.config import FireflySettings
from backend.integrations.rvc.firefly_extensions import (
    FireflyCANDetectiveIntegration,
    FireflyComponentType,
    FireflyDecoder,
    FireflyDGNType,
    FireflyEncoder,
    FireflyMessage,
    MultiplexBuffer,
    SafetyInterlockState,
)
from backend.integrations.rvc.firefly_feature import FireflyFeature


class TestFireflySettings:
    """Test Firefly configuration settings."""

    def test_default_settings(self):
        """Test default Firefly settings."""
        settings = FireflySettings()

        assert settings.enabled is False
        assert settings.enable_multiplexing is True
        assert settings.enable_custom_dgns is True
        assert settings.enable_state_interlocks is True
        assert settings.enable_can_detective_integration is False
        assert settings.default_interface == "house"
        assert settings.custom_dgn_range_start == 0x1F000
        assert settings.custom_dgn_range_end == 0x1FFFF

    def test_environment_variable_override(self):
        """Test environment variable overrides."""
        with patch.dict(
            "os.environ",
            {
                "COACHIQ_FIREFLY__ENABLED": "true",
                "COACHIQ_FIREFLY__ENABLE_MULTIPLEXING": "false",
                "COACHIQ_FIREFLY__DEFAULT_INTERFACE": "chassis",
                "COACHIQ_FIREFLY__MULTIPLEX_TIMEOUT_MS": "2000",
            },
        ):
            settings = FireflySettings()

            assert settings.enabled is True
            assert settings.enable_multiplexing is False
            assert settings.default_interface == "chassis"
            assert settings.multiplex_timeout_ms == 2000

    def test_component_list_parsing(self):
        """Test parsing of component lists from environment variables."""
        with patch.dict(
            "os.environ", {"COACHIQ_FIREFLY__SUPPORTED_COMPONENTS": "lighting,climate,slides"}
        ):
            settings = FireflySettings()

            assert settings.supported_components == ["lighting", "climate", "slides"]

    def test_dgn_list_parsing(self):
        """Test parsing of DGN lists from environment variables."""
        with patch.dict("os.environ", {"COACHIQ_FIREFLY__PRIORITY_DGNS": "0x1FECA,0x1FEDB,130522"}):
            settings = FireflySettings()

            assert 0x1FECA in settings.priority_dgns
            assert 0x1FEDB in settings.priority_dgns
            assert 130522 in settings.priority_dgns


class TestFireflyDecoder:
    """Test Firefly message decoder."""

    @pytest.fixture
    def decoder_settings(self):
        """Create test settings for decoder."""
        return FireflySettings(
            enabled=True,
            enable_multiplexing=True,
            enable_custom_dgns=True,
            enable_state_interlocks=True,
            multiplex_timeout_ms=1000,
            safety_interlock_components=["slides", "awnings"],
            required_interlocks={
                "slides": ["park_brake", "engine_off"],
                "awnings": ["wind_speed", "vehicle_level"],
            },
        )

    @pytest.fixture
    def decoder(self, decoder_settings):
        """Create Firefly decoder instance."""
        return FireflyDecoder(decoder_settings)

    def test_decoder_initialization(self, decoder):
        """Test decoder initialization."""
        assert decoder is not None
        assert len(decoder.safety_interlocks) == 2
        assert "slides" in decoder.safety_interlocks
        assert "awnings" in decoder.safety_interlocks

    def test_dgn_classification(self, decoder):
        """Test DGN classification logic."""
        # Standard RV-C DGN
        assert decoder._classify_dgn(0x1FEDA) == FireflyDGNType.STANDARD_RVC

        # Firefly custom DGN
        assert decoder._classify_dgn(0x1F100) == FireflyDGNType.FIREFLY_CUSTOM

        # Multiplexed DGN
        assert decoder._classify_dgn(0x1FFB7) == FireflyDGNType.MULTIPLEXED

        # Safety interlock DGN
        assert decoder._classify_dgn(0x1FECA) == FireflyDGNType.SAFETY_INTERLOCK

    def test_standard_rvc_message_decode(self, decoder):
        """Test decoding of standard RV-C messages."""
        dgn = 0x1FEDA  # Standard RV-C lighting status
        source_address = 0x17
        data = bytes([0x01, 0x64, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        timestamp = time.time()

        message = decoder.decode_message(dgn, source_address, data, timestamp, 0x181FEDA17)

        assert message is not None
        assert message.dgn == dgn
        assert message.source_address == source_address
        assert message.dgn_type == FireflyDGNType.STANDARD_RVC

    def test_firefly_custom_lighting_decode(self, decoder):
        """Test decoding of Firefly custom lighting messages."""
        dgn = 0x1F100  # Firefly lighting control
        source_address = 0x17
        data = bytes([0x01, 0x02, 0x64, 0x00, 0x00, 0x00, 0xFF, 0x00])
        timestamp = time.time()

        message = decoder.decode_message(dgn, source_address, data, timestamp, 0x181F10017)

        assert message is not None
        assert message.dgn == dgn
        assert message.dgn_type == FireflyDGNType.FIREFLY_CUSTOM
        assert message.component_type == FireflyComponentType.LIGHTING
        assert message.signals["lighting_zone"] == 1
        assert message.signals["command_type"] == 2
        assert message.signals["brightness_level"] == 100

    def test_firefly_custom_climate_decode(self, decoder):
        """Test decoding of Firefly custom climate messages."""
        dgn = 0x1F101  # Firefly climate control
        source_address = 0x17
        data = bytes([0x01, 0x48, 0x46, 0x03, 0x32, 0x2D, 0x00, 0x00])
        timestamp = time.time()

        message = decoder.decode_message(dgn, source_address, data, timestamp, 0x181F10117)

        assert message is not None
        assert message.dgn_type == FireflyDGNType.FIREFLY_CUSTOM
        assert message.component_type == FireflyComponentType.CLIMATE
        assert message.signals["zone_id"] == 1
        assert message.signals["target_temp_f"] == 72
        assert message.signals["current_temp_f"] == 70
        assert message.signals["hvac_mode"] == 3  # auto
        assert message.signals["fan_speed"] == 50

    def test_firefly_slide_awning_decode(self, decoder):
        """Test decoding of Firefly slide/awning messages."""
        dgn = 0x1F102  # Firefly slide/awning control
        source_address = 0x17
        data = bytes([0x00, 0x00, 0x32, 0x64, 0x01, 0x00, 0x0A, 0x00])
        timestamp = time.time()

        message = decoder.decode_message(dgn, source_address, data, timestamp, 0x181F10217)

        assert message is not None
        assert message.dgn_type == FireflyDGNType.FIREFLY_CUSTOM
        assert message.component_type == FireflyComponentType.SLIDES
        assert message.signals["device_id"] == 0
        assert message.signals["device_type"] == 0  # slide
        assert message.signals["position_percent"] == 50
        assert message.signals["target_position"] == 100
        assert message.signals["movement_state"] == 1  # extending

    def test_multiplexed_message_assembly(self, decoder):
        """Test multiplexed message assembly."""
        dgn = 0x1FFB7  # Tank levels
        source_address = 0x17
        timestamp = time.time()

        # First part of multiplexed message
        data_part1 = bytes([0x12, 0x00, 0x00, 0x64, 0x00, 0x64])  # seq=1, total=2, part=0
        message1 = decoder.decode_message(dgn, source_address, data_part1, timestamp, 0x181FFB717)

        # Should return None (incomplete)
        assert message1 is None

        # Second part of multiplexed message
        data_part2 = bytes([0x12, 0x01, 0x01, 0x32, 0x00, 0x32])  # seq=1, total=2, part=1
        message2 = decoder.decode_message(dgn, source_address, data_part2, timestamp, 0x181FFB717)

        # Should return complete message
        assert message2 is not None
        assert message2.dgn_type == FireflyDGNType.MULTIPLEXED
        assert message2.multiplexed_data is not None
        assert "tanks" in message2.multiplexed_data

    def test_tank_level_decoding(self, decoder):
        """Test tank level data decoding."""
        # Simulate assembled tank data: fresh_water=100%, gray_water=50%
        tank_data = bytes([0x00, 0x64, 0x00, 0x64, 0x01, 0x32, 0x00, 0x50])

        tanks = decoder._decode_tank_levels(tank_data)

        assert "tanks" in tanks
        assert "fresh_water" in tanks["tanks"]
        assert "gray_water" in tanks["tanks"]
        assert tanks["tanks"]["fresh_water"]["level_percent"] == 100
        assert tanks["tanks"]["gray_water"]["level_percent"] == 50

    def test_temperature_sensor_decoding(self, decoder):
        """Test temperature sensor data decoding."""
        # Simulate temperature data: interior=72°F, exterior=45°F
        temp_data = bytes([0x00, 0x23, 0x00, 0x01, 0x1C, 0x80])  # Encoded temperatures

        temperatures = decoder._decode_temperature_data(temp_data)

        assert "temperatures" in temperatures
        assert "interior_ambient" in temperatures["temperatures"]
        assert "exterior_ambient" in temperatures["temperatures"]
        assert temperatures["temperatures"]["interior_ambient"]["raw"] == 0x2300
        assert temperatures["temperatures"]["exterior_ambient"]["raw"] == 0x1C80

    def test_safety_interlock_validation(self, decoder):
        """Test safety interlock validation."""
        # Update vehicle state to safe conditions
        decoder.update_vehicle_state(
            "vehicle",
            {
                "park_brake_set": True,
                "engine_running": False,
                "wind_speed_mph": 5,
                "is_level": True,
            },
        )

        # Test slide operation - should be safe
        is_safe, violations = decoder.validate_safety_interlocks("slides", "extend")
        assert is_safe is True
        assert len(violations) == 0

        # Update to unsafe conditions
        decoder.update_vehicle_state("vehicle", {"park_brake_set": False, "engine_running": True})

        # Test slide operation - should be unsafe
        is_safe, violations = decoder.validate_safety_interlocks("slides", "extend")
        assert is_safe is False
        assert len(violations) > 0

    def test_safety_interlock_message_decode(self, decoder):
        """Test safety interlock message decoding."""
        dgn = 0x1FECA  # Safety interlock DGN
        source_address = 0x17
        data = bytes([0x00, 0x02, 0xFF, 0x05, 0x00, 0x00, 0x00, 0x00])  # slides, unsafe, fault 5
        timestamp = time.time()

        message = decoder.decode_message(dgn, source_address, data, timestamp, 0x181FECA17)

        assert message is not None
        assert message.dgn_type == FireflyDGNType.SAFETY_INTERLOCK
        assert message.safety_status == SafetyInterlockState.UNSAFE
        assert message.signals["component"] == "slides"
        assert message.signals["fault_code"] == 5

    def test_buffer_cleanup(self, decoder):
        """Test cleanup of expired multiplex buffers."""
        # Create an expired buffer
        buffer_key = "test_buffer"
        decoder.multiplex_buffers[buffer_key] = MultiplexBuffer(
            dgn=0x1FFB7, source_address=0x17, sequence_id=1, total_parts=2
        )
        decoder.multiplex_buffers[buffer_key].first_received = time.time() - 2.0  # 2 seconds ago

        # Trigger cleanup
        decoder._cleanup_expired_buffers()

        # Buffer should be cleaned up
        assert buffer_key not in decoder.multiplex_buffers

    def test_decoder_status(self, decoder):
        """Test decoder status reporting."""
        status = decoder.get_decoder_status()

        assert "enabled" in status
        assert "configuration" in status
        assert "runtime_status" in status
        assert "safety_interlocks" in status
        assert status["configuration"]["multiplexing_enabled"] is True
        assert status["configuration"]["custom_dgns_enabled"] is True


class TestFireflyEncoder:
    """Test Firefly message encoder."""

    @pytest.fixture
    def encoder_settings(self):
        """Create test settings for encoder."""
        return FireflySettings(
            enabled=True,
            enable_state_interlocks=True,
            safety_interlock_components=["slides", "awnings"],
            required_interlocks={
                "slides": ["park_brake", "engine_off"],
                "awnings": ["wind_speed", "vehicle_level"],
            },
        )

    @pytest.fixture
    def encoder(self, encoder_settings):
        """Create Firefly encoder instance."""
        return FireflyEncoder(encoder_settings)

    def test_encoder_initialization(self, encoder):
        """Test encoder initialization."""
        assert encoder is not None
        assert encoder.settings is not None
        assert encoder.decoder is not None

    def test_lighting_brightness_command(self, encoder):
        """Test encoding lighting brightness command."""
        # Mock safe vehicle state
        encoder.decoder.update_vehicle_state(
            "vehicle", {"park_brake_set": True, "engine_running": False}
        )

        messages = encoder.encode_command(
            "lighting", "set_brightness", {"zone": 1, "brightness": 75, "fade_time_ms": 500}
        )

        assert len(messages) == 1
        dgn, source_address, data = messages[0]

        assert dgn == 0x1F100  # Firefly lighting DGN
        assert source_address == 0x17
        assert data[0] == 1  # zone
        assert data[1] == 2  # dim command
        assert data[2] == 75  # brightness
        assert data[4] == 0x01  # fade_time high byte
        assert data[5] == 0xF4  # fade_time low byte (500)

    def test_lighting_scene_command(self, encoder):
        """Test encoding lighting scene command."""
        messages = encoder.encode_command("lighting", "set_scene", {"scene_id": 3})

        assert len(messages) == 1
        dgn, source_address, data = messages[0]

        assert dgn == 0x1F100
        assert data[0] == 0xFF  # all zones
        assert data[1] == 3  # scene command
        assert data[3] == 3  # scene ID

    def test_climate_temperature_command(self, encoder):
        """Test encoding climate temperature command."""
        messages = encoder.encode_command(
            "climate",
            "set_temperature",
            {"zone": 0, "temperature_f": 72, "mode": "cool", "fan_speed": 60},
        )

        assert len(messages) == 1
        dgn, source_address, data = messages[0]

        assert dgn == 0x1F101  # Firefly climate DGN
        assert data[0] == 0  # zone
        assert data[1] == 72  # target temp
        assert data[3] == 2  # cool mode
        assert data[4] == 60  # fan speed

    def test_slide_extend_command(self, encoder):
        """Test encoding slide extend command."""
        # Mock safe vehicle state
        encoder.decoder.update_vehicle_state(
            "vehicle", {"park_brake_set": True, "engine_running": False}
        )

        messages = encoder.encode_command("slides", "extend", {"device_id": 0, "position": 100})

        assert len(messages) == 1
        dgn, source_address, data = messages[0]

        assert dgn == 0x1F102  # Firefly slide/awning DGN
        assert data[0] == 0  # device ID
        assert data[1] == 0  # device type (slide)
        assert data[3] == 100  # target position
        assert data[4] == 1  # extending movement state

    def test_awning_retract_command(self, encoder):
        """Test encoding awning retract command."""
        # Mock safe vehicle state
        encoder.decoder.update_vehicle_state("vehicle", {"wind_speed_mph": 5, "is_level": True})

        messages = encoder.encode_command("awnings", "retract", {"device_id": 1, "position": 0})

        assert len(messages) == 1
        dgn, source_address, data = messages[0]

        assert dgn == 0x1F102
        assert data[0] == 1  # device ID
        assert data[1] == 1  # device type (awning)
        assert data[3] == 0  # target position (retracted)
        assert data[4] == 2  # retracting movement state

    def test_power_inverter_command(self, encoder):
        """Test encoding power inverter command."""
        messages = encoder.encode_command("power", "inverter_control", {"enable": True})

        assert len(messages) == 1
        dgn, source_address, data = messages[0]

        assert dgn == 0x1F103  # Firefly power DGN
        assert data[4] == 1  # inverter on

    def test_safety_interlock_blocking(self, encoder):
        """Test that safety interlocks block unsafe commands."""
        # Mock unsafe vehicle state
        encoder.decoder.update_vehicle_state(
            "vehicle", {"park_brake_set": False, "engine_running": True}
        )

        messages = encoder.encode_command(
            "slides", "extend", {"device_id": 0, "position": 100}, validate_safety=True
        )

        # Should return empty list due to safety violation
        assert len(messages) == 0

    def test_safety_validation_bypass(self, encoder):
        """Test bypassing safety validation."""
        # Mock unsafe vehicle state
        encoder.decoder.update_vehicle_state(
            "vehicle", {"park_brake_set": False, "engine_running": True}
        )

        messages = encoder.encode_command(
            "slides",
            "extend",
            {"device_id": 0, "position": 100},
            validate_safety=False,  # Bypass safety
        )

        # Should return message even with unsafe conditions
        assert len(messages) == 1


class TestFireflyCANDetectiveIntegration:
    """Test CAN Detective integration."""

    @pytest.fixture
    def can_detective_settings(self):
        """Create test settings for CAN Detective."""
        return FireflySettings(
            enabled=True,
            enable_can_detective_integration=True,
            can_detective_path="/usr/bin/can_detective",
        )

    @pytest.fixture
    def can_detective(self, can_detective_settings):
        """Create CAN Detective integration instance."""
        return FireflyCANDetectiveIntegration(can_detective_settings)

    def test_can_detective_initialization(self, can_detective):
        """Test CAN Detective initialization."""
        assert can_detective is not None
        assert can_detective.enabled is True

    def test_message_pattern_analysis(self, can_detective):
        """Test message pattern analysis."""
        # Create test messages
        messages = [
            FireflyMessage(0x1F100, 0x17, b"", time.time(), FireflyDGNType.FIREFLY_CUSTOM),
            FireflyMessage(0x1F100, 0x17, b"", time.time(), FireflyDGNType.FIREFLY_CUSTOM),
            FireflyMessage(0x1F101, 0x18, b"", time.time(), FireflyDGNType.FIREFLY_CUSTOM),
        ]

        analysis = can_detective.analyze_message_pattern(messages)

        assert analysis["message_count"] == 3
        assert analysis["unique_dgns"] == 2
        assert analysis["unique_sources"] == 2
        assert analysis["most_frequent_dgn"] == 0x1F100

    def test_can_detective_export_format(self, can_detective):
        """Test CAN Detective export format."""
        messages = [
            FireflyMessage(
                0x1F100, 0x17, bytes([1, 2, 3, 4]), 1234567890.123, FireflyDGNType.FIREFLY_CUSTOM
            ),
        ]

        export_data = can_detective.export_can_detective_format(messages)

        assert "# Firefly message export for CAN Detective analysis" in export_data
        assert "1234567890.123,1F100,17,01020304" in export_data

    def test_disabled_can_detective(self):
        """Test CAN Detective when disabled."""
        settings = FireflySettings(enable_can_detective_integration=False)
        can_detective = FireflyCANDetectiveIntegration(settings)

        assert can_detective.enabled is False
        assert can_detective.analyze_message_pattern([]) == {}
        assert can_detective.export_can_detective_format([]) == ""


class TestFireflyFeature:
    """Test Firefly feature integration."""

    @pytest.fixture
    def feature_settings(self):
        """Create test settings for feature."""
        return FireflySettings(
            enabled=True,
            enable_multiplexing=True,
            enable_custom_dgns=True,
            enable_state_interlocks=True,
            enable_can_detective_integration=False,
        )

    @pytest.fixture
    async def feature(self, feature_settings):
        """Create Firefly feature instance."""
        with patch(
            "backend.integrations.rvc.firefly_feature.get_firefly_settings",
            return_value=feature_settings,
        ):
            feature = FireflyFeature(enabled=True)
            await feature.startup()
            yield feature
            await feature.shutdown()

    @pytest.mark.asyncio
    async def test_feature_startup_shutdown(self, feature_settings):
        """Test feature startup and shutdown."""
        with patch(
            "backend.integrations.rvc.firefly_feature.get_firefly_settings",
            return_value=feature_settings,
        ):
            feature = FireflyFeature(enabled=True)

            # Test startup
            await feature.startup()
            assert feature.decoder is not None
            assert feature.encoder is not None
            assert feature.can_detective is None  # Disabled in settings

            # Test shutdown
            await feature.shutdown()
            assert feature.decoder is None
            assert feature.encoder is None
            assert feature.can_detective is None

    @pytest.mark.asyncio
    async def test_feature_disabled_startup(self):
        """Test feature startup when disabled."""
        settings = FireflySettings(enabled=False)
        with patch(
            "backend.integrations.rvc.firefly_feature.get_firefly_settings", return_value=settings
        ):
            feature = FireflyFeature(enabled=True)

            await feature.startup()

            # Components should not be initialized
            assert feature.decoder is None
            assert feature.encoder is None

    @pytest.mark.asyncio
    async def test_feature_decode_message(self, feature):
        """Test feature message decoding."""
        dgn = 0x1F100
        source_address = 0x17
        data = bytes([0x01, 0x02, 0x64, 0x00, 0x00, 0x00, 0xFF, 0x00])
        timestamp = time.time()

        result = feature.decode_message(dgn, source_address, data, timestamp, 0x181F10017)

        assert result is not None
        assert result["dgn"] == dgn
        assert result["firefly_specific"] is True
        assert result["component_type"] == "lighting"

    @pytest.mark.asyncio
    async def test_feature_encode_command(self, feature):
        """Test feature command encoding."""
        messages = feature.encode_command(
            "lighting", "set_brightness", {"zone": 1, "brightness": 50}
        )

        assert len(messages) == 1
        dgn, source_address, data = messages[0]
        assert dgn == 0x1F100

    @pytest.mark.asyncio
    async def test_feature_safety_validation(self, feature):
        """Test feature safety validation."""
        is_safe, violations = feature.validate_safety_interlocks("slides", "extend")

        # Should have violations due to unknown vehicle state
        assert is_safe is False
        assert len(violations) > 0

    @pytest.mark.asyncio
    async def test_feature_health_status(self, feature):
        """Test feature health status."""
        health = feature.health
        assert health == "healthy"

        # Test degraded state
        feature.decoder = None
        health = feature.health
        assert health == "degraded"

    @pytest.mark.asyncio
    async def test_feature_component_status(self, feature):
        """Test feature component status."""
        status = feature.get_component_status()

        assert status["enabled"] is True
        assert status["settings_enabled"] is True
        assert status["components"]["decoder"]["available"] is True
        assert status["components"]["encoder"]["available"] is True
        assert status["components"]["can_detective"]["available"] is False

    @pytest.mark.asyncio
    async def test_feature_supported_components(self, feature):
        """Test getting supported components."""
        components = feature.get_supported_components()

        assert "lighting" in components
        assert "climate" in components
        assert "slides" in components

    @pytest.mark.asyncio
    async def test_feature_dgn_ranges(self, feature):
        """Test getting DGN range information."""
        ranges = feature.get_firefly_dgn_ranges()

        assert "custom_range" in ranges
        assert ranges["custom_range"]["start"] == "0x1F000"
        assert ranges["custom_range"]["end"] == "0x1FFFF"

    @pytest.mark.asyncio
    async def test_feature_safety_interlock_status(self, feature):
        """Test getting safety interlock status."""
        status = feature.get_safety_interlock_status()

        assert "enabled" in status
        assert status["enabled"] is True


class TestMultiplexBuffer:
    """Test multiplex buffer functionality."""

    def test_buffer_initialization(self):
        """Test buffer initialization."""
        buffer = MultiplexBuffer(dgn=0x1FFB7, source_address=0x17, sequence_id=1, total_parts=3)

        assert buffer.dgn == 0x1FFB7
        assert buffer.source_address == 0x17
        assert buffer.sequence_id == 1
        assert buffer.total_parts == 3
        assert len(buffer.received_parts) == 0
        assert not buffer.is_complete()

    def test_buffer_completion(self):
        """Test buffer completion detection."""
        buffer = MultiplexBuffer(dgn=0x1FFB7, source_address=0x17, sequence_id=1, total_parts=2)

        # Add first part
        buffer.received_parts[0] = b"part0"
        assert not buffer.is_complete()

        # Add second part
        buffer.received_parts[1] = b"part1"
        assert buffer.is_complete()

    def test_buffer_expiration(self):
        """Test buffer expiration."""
        buffer = MultiplexBuffer(dgn=0x1FFB7, source_address=0x17, sequence_id=1, total_parts=2)

        # Set old timestamp
        buffer.first_received = time.time() - 2.0  # 2 seconds ago

        # Should be expired with 1000ms timeout
        assert buffer.is_expired(1000)

        # Should not be expired with 3000ms timeout
        assert not buffer.is_expired(3000)


if __name__ == "__main__":
    pytest.main([__file__])
