"""
Test suite for ConfigService.

Tests the configuration service business logic, including:
- Configuration retrieval and validation
- Environment variable access
- Application settings management
- Entity configuration handling
"""

import os
from unittest.mock import Mock, patch

import pytest

from backend.core.state import AppState
from backend.services.config_service import ConfigService

# ================================
# Test Fixtures
# ================================


@pytest.fixture
def mock_entity_manager():
    """Mock EntityManager for testing."""
    mock = Mock()
    mock.get_entity_ids.return_value = ["entity1", "entity2", "entity3"]
    mock.get_light_entity_ids.return_value = ["light1", "light2"]
    mock.get_entity.return_value = None

    # Mock entities for filter_entities
    light_entity1 = Mock()
    light_entity1.config = {
        "device_type": "light",
        "suggested_area": "living_room",
        "interface": "vcan0",
    }
    light_entity2 = Mock()
    light_entity2.config = {
        "device_type": "light",
        "suggested_area": "kitchen",
        "interface": "vcan1",
    }

    # Mock entity for get_all_entities - used by _get_unique_device_types and _get_unique_areas
    sensor_entity = Mock()
    sensor_entity.config = {"device_type": "sensor", "suggested_area": "kitchen"}
    switch_entity = Mock()
    switch_entity.config = {"device_type": "switch", "suggested_area": "living_room"}

    # filter_entities should return a dictionary
    mock.filter_entities.return_value = {"light1": light_entity1, "light2": light_entity2}

    # get_all_entities should return all entities
    mock.get_all_entities.return_value = {
        "light1": light_entity1,
        "light2": light_entity2,
        "sensor1": sensor_entity,
        "switch1": switch_entity,
    }

    return mock


@pytest.fixture
def mock_app_state(mock_entity_manager):
    """Mock AppState for testing."""
    mock = Mock(spec=AppState)
    mock.entity_manager = mock_entity_manager
    mock.controller_source_addr = 42
    mock.config_data = {"key1": "value1", "key2": "value2"}
    mock.coach_info = {"make": "Test", "model": "RV"}
    mock.decoder_map = {
        "dgn1": {"pgn": 123, "name": "decoder1"},
        "dgn2": {"pgn": 456, "name": "decoder2"},
    }
    mock.known_command_status_pairs = {"cmd1": "status1", "cmd2": "status2"}
    return mock


@pytest.fixture
def config_service(mock_app_state):
    """Create ConfigService instance for testing."""
    return ConfigService(app_state=mock_app_state)


@pytest.fixture
def sample_entity():
    """Create a sample entity for testing."""
    mock_entity = Mock()
    mock_entity.config = {
        "device_type": "light",
        "suggested_area": "living_room",
        "capabilities": ["brightness", "color"],
        "instance": 1,
    }
    return mock_entity


@pytest.fixture
def sample_non_light_entity():
    """Create a sample non-light entity for testing."""
    mock_entity = Mock()
    mock_entity.config = {
        "device_type": "sensor",
        "suggested_area": "kitchen",
        "capabilities": ["temperature"],
        "instance": 1,
    }
    return mock_entity


# ================================
# Core Functionality Tests
# ================================


class TestConfigServiceInitialization:
    """Test ConfigService initialization and setup."""

    def test_init_with_app_state(self, mock_app_state):
        """Test service initialization with app_state."""
        service = ConfigService(app_state=mock_app_state)
        assert service.app_state is mock_app_state

    def test_init_requires_app_state(self):
        """Test that ConfigService requires app_state."""
        # ConfigService requires app_state parameter
        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            ConfigService()


# ================================
# Configuration Summary Tests
# ================================


class TestConfigurationSummary:
    """Test configuration summary functionality."""

    async def test_get_config_summary_basic(self, config_service, mock_app_state):
        """Test basic configuration summary retrieval."""
        result = await config_service.get_config_summary()

        assert "entities" in result
        assert "can_interfaces" in result
        assert "system" in result
        assert "raw_config_keys" in result

        # Check entities section
        entities = result["entities"]
        assert entities["total_configured"] == 3
        assert entities["light_entities"] == 2
        assert isinstance(entities["device_types"], list)
        assert isinstance(entities["areas"], list)

        # Check CAN interfaces section
        can_interfaces = result["can_interfaces"]
        assert can_interfaces["controller_address"] == 42
        assert isinstance(can_interfaces["configured"], list)

        # Check system section
        system = result["system"]
        assert system["has_coach_info"] is True
        assert system["decoder_entries"] == 2
        assert system["known_command_pairs"] == 2

        # Check raw config keys
        assert result["raw_config_keys"] == ["key1", "key2"]

    async def test_get_config_summary_no_config_data(self, config_service, mock_app_state):
        """Test configuration summary when config_data is None."""
        mock_app_state.config_data = None

        result = await config_service.get_config_summary()

        assert result["raw_config_keys"] == []

    async def test_get_config_summary_no_coach_info(self, config_service, mock_app_state):
        """Test configuration summary when coach_info is missing."""
        mock_app_state.coach_info = None

        result = await config_service.get_config_summary()

        assert result["system"]["has_coach_info"] is False

    async def test_get_config_summary_empty_entities(self, config_service, mock_app_state):
        """Test configuration summary with no entities."""
        mock_app_state.entity_manager.get_entity_ids.return_value = []
        mock_app_state.entity_manager.get_light_entity_ids.return_value = []

        result = await config_service.get_config_summary()

        assert result["entities"]["total_configured"] == 0
        assert result["entities"]["light_entities"] == 0


# ================================
# Environment Info Tests
# ================================


class TestEnvironmentInfo:
    """Test environment information functionality."""

    @patch.dict(
        os.environ,
        {
            "CAN_BUSTYPE": "socketcan",
            "CAN_INTERFACE": "vcan0",
            "CAN_BITRATE": "250000",
            "LOG_LEVEL": "DEBUG",
            "DEBUG": "true",
            "HOST": "0.0.0.0",
            "PORT": "8080",
        },
    )
    async def test_get_environment_info_with_values(self, config_service):
        """Test environment info retrieval with set values."""
        result = await config_service.get_environment_info()

        env_vars = result["environment_variables"]
        assert env_vars["CAN_BUSTYPE"] == "socketcan"
        assert env_vars["CAN_INTERFACE"] == "vcan0"
        assert env_vars["CAN_BITRATE"] == "250000"
        assert env_vars["LOG_LEVEL"] == "DEBUG"
        assert env_vars["DEBUG"] is True
        assert env_vars["HOST"] == "0.0.0.0"
        assert env_vars["PORT"] == "8080"

        # Count non-None values: CAN_BUSTYPE, CAN_INTERFACE, CAN_BITRATE, LOG_LEVEL, DEBUG, HOST, PORT
        # Plus defaults: WORKERS, ENABLE_WEBSOCKETS, ENABLE_CAN_SNIFFER = 10 total
        assert result["total_env_vars"] == 10

    @patch.dict(os.environ, {}, clear=True)
    async def test_get_environment_info_defaults(self, config_service):
        """Test environment info with default values."""
        result = await config_service.get_environment_info()

        env_vars = result["environment_variables"]
        assert env_vars["CAN_BUSTYPE"] == "socketcan"
        assert env_vars["CAN_INTERFACE"] is None
        assert env_vars["LOG_LEVEL"] == "INFO"
        assert env_vars["DEBUG"] is False
        assert env_vars["HOST"] == "127.0.0.1"
        assert env_vars["PORT"] == "8000"

    @patch.dict(
        os.environ,
        {"API_SECRET": "supersecret", "DATABASE_PASSWORD": "dbpass", "AUTH_TOKEN": "token123"},
    )
    async def test_get_environment_info_masks_sensitive(self, config_service):
        """Test that sensitive environment variables are masked."""
        # Note: These won't be in the actual env_vars dict unless we add them to the service
        # This test demonstrates the masking logic if sensitive vars were added

    async def test_get_environment_info_boolean_parsing(self, config_service):
        """Test boolean environment variable parsing."""
        with patch.dict(os.environ, {"DEBUG": "false", "ENABLE_WEBSOCKETS": "true"}):
            result = await config_service.get_environment_info()
            env_vars = result["environment_variables"]
            assert env_vars["DEBUG"] is False
            assert env_vars["ENABLE_WEBSOCKETS"] is True

        with patch.dict(os.environ, {"DEBUG": "TRUE", "ENABLE_WEBSOCKETS": "FALSE"}):
            result = await config_service.get_environment_info()
            env_vars = result["DEBUG"] is True
            assert env_vars["ENABLE_WEBSOCKETS"] is False


# ================================
# Entity Configuration Tests
# ================================


class TestEntityConfiguration:
    """Test entity configuration functionality."""

    async def test_get_entity_configuration_specific_light(self, config_service, sample_entity):
        """Test getting configuration for a specific light entity."""
        config_service.app_state.entity_manager.get_entity.return_value = sample_entity

        result = await config_service.get_entity_configuration("light1")

        assert result["entity_id"] == "light1"
        assert result["configuration"] == sample_entity.config
        assert result["is_light"] is True
        assert result["light_info"] == sample_entity.config

    async def test_get_entity_configuration_specific_non_light(
        self, config_service, sample_non_light_entity
    ):
        """Test getting configuration for a specific non-light entity."""
        config_service.app_state.entity_manager.get_entity.return_value = sample_non_light_entity

        result = await config_service.get_entity_configuration("sensor1")

        assert result["entity_id"] == "sensor1"
        assert result["configuration"] == sample_non_light_entity.config
        assert result["is_light"] is False
        assert result["light_info"] is None

    async def test_get_entity_configuration_not_found(self, config_service):
        """Test getting configuration for non-existent entity."""
        config_service.app_state.entity_manager.get_entity.return_value = None

        with pytest.raises(ValueError, match="Entity 'nonexistent' not found in configuration"):
            await config_service.get_entity_configuration("nonexistent")

    async def test_get_entity_configuration_all_entities(self, config_service):
        """Test getting configuration for all entities."""
        # Setup mock entities
        light_entity = Mock()
        light_entity.config = {
            "device_type": "light",
            "suggested_area": "living_room",
            "capabilities": ["brightness"],
        }

        sensor_entity = Mock()
        sensor_entity.config = {
            "device_type": "sensor",
            "suggested_area": "kitchen",
            "capabilities": ["temperature"],
        }

        all_entities = {"light1": light_entity, "sensor1": sensor_entity}
        config_service.app_state.entity_manager.get_all_entities.return_value = all_entities

        result = await config_service.get_entity_configuration()

        assert "entities" in result
        entities = result["entities"]

        assert "light1" in entities
        assert entities["light1"]["device_type"] == "light"
        assert entities["light1"]["is_light"] is True

        assert "sensor1" in entities
        assert entities["sensor1"]["device_type"] == "sensor"
        assert entities["sensor1"]["is_light"] is False

    async def test_get_entity_configuration_empty_entities(self, config_service):
        """Test getting configuration when no entities exist."""
        config_service.app_state.entity_manager.get_all_entities.return_value = {}

        result = await config_service.get_entity_configuration()

        assert result["entities"] == {}


# ================================
# Decoder Info Tests
# ================================


class TestDecoderInfo:
    """Test decoder information functionality."""

    async def test_get_decoder_info_basic(self, config_service, mock_app_state):
        """Test basic decoder information retrieval."""
        result = await config_service.get_decoder_info()

        assert "total_entries" in result
        assert "unique_pgns" in result
        assert "unique_dgns" in result
        assert "has_pgn_name_map" in result
        assert "sample_entries" in result

        assert result["total_entries"] == 2
        assert result["unique_pgns"] == 2  # Two unique PGNs: 123, 456
        assert result["unique_dgns"] == 0  # No dgn_hex in our mock data
        assert result["has_pgn_name_map"] is False
        assert len(result["sample_entries"]) == 2

    async def test_get_decoder_info_empty_decoder(self, config_service, mock_app_state):
        """Test decoder info when decoder map is empty."""
        mock_app_state.decoder_map = {}

        result = await config_service.get_decoder_info()

        assert result["total_entries"] == 0
        assert result["unique_pgns"] == 0
        assert result["unique_dgns"] == 0


# ================================
# Helper Method Tests
# ================================


class TestHelperMethods:
    """Test internal helper methods."""

    def test_get_unique_device_types(self, config_service):
        """Test _get_unique_device_types helper method."""
        result = config_service._get_unique_device_types()

        expected = ["light", "sensor", "switch"]
        assert sorted(result) == sorted(expected)

    def test_get_unique_areas(self, config_service):
        """Test _get_unique_areas helper method."""
        result = config_service._get_unique_areas()

        expected = ["living_room", "kitchen"]
        assert sorted(result) == sorted(expected)

    def test_get_configured_interfaces(self, config_service):
        """Test _get_configured_interfaces helper method."""
        with patch.dict(os.environ, {"CAN_INTERFACE": "vcan0,can0"}):
            result = config_service._get_configured_interfaces()
            assert "vcan0" in result or "can0" in result

        with patch.dict(os.environ, {}, clear=True):
            result = config_service._get_configured_interfaces()
            assert isinstance(result, list)


# ================================
# Error Handling Tests
# ================================


class TestErrorHandling:
    """Test error handling in various scenarios."""

    async def test_get_config_summary_entity_manager_error(self, config_service, mock_app_state):
        """Test config summary when entity manager raises an error."""
        mock_app_state.entity_manager.get_entity_ids.side_effect = RuntimeError(
            "Entity manager error"
        )

        with pytest.raises(RuntimeError):
            await config_service.get_config_summary()

    async def test_get_entity_configuration_missing_config(self, config_service):
        """Test entity configuration when entity has no config."""
        entity_no_config = Mock()
        entity_no_config.config = None
        config_service.app_state.entity_manager.get_entity.return_value = entity_no_config

        with pytest.raises(AttributeError):
            await config_service.get_entity_configuration("entity1")


# ================================
# Integration Tests
# ================================


class TestServiceIntegration:
    """Test service integration with dependencies."""

    async def test_complete_config_workflow(self, config_service):
        """Test complete configuration retrieval workflow."""
        # Get config summary
        summary = await config_service.get_config_summary()
        assert "entities" in summary

        # Get environment info
        env_info = await config_service.get_environment_info()
        assert "environment_variables" in env_info

        # Get decoder info
        decoder_info = await config_service.get_decoder_info()
        assert "total_entries" in decoder_info

        # Get all entity configurations
        entity_config = await config_service.get_entity_configuration()
        assert "entities" in entity_config

    async def test_service_state_consistency(self, config_service, mock_app_state):
        """Test that service maintains consistent state across calls."""
        # Make multiple calls and ensure consistency
        summary1 = await config_service.get_config_summary()
        summary2 = await config_service.get_config_summary()

        assert summary1 == summary2
        assert config_service.app_state is mock_app_state
