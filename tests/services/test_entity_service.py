"""
Test suite for EntityService.

Tests the entity service business logic, including:
- Entity retrieval and filtering
- Entity metadata extraction
- Light control operations
- WebSocket integration
"""

from unittest.mock import AsyncMock, Mock

import pytest

from backend.core.entity_manager import EntityManager
from backend.models.entity import ControlCommand
from backend.models.entity_model import Entity
from backend.services.entity_service import EntityService

# ================================
# Test Fixtures
# ================================


@pytest.fixture
def mock_entity_manager():
    """Mock EntityManager with entity management methods."""
    mock = Mock(spec=EntityManager)
    mock.get_entity = Mock(return_value=None)
    mock.update_entity = Mock()
    mock.get_all_entities = Mock(return_value={})
    mock.get_entity_ids = Mock(return_value=[])
    mock.filter_entities = Mock(return_value={})
    mock.unmapped_entries = {}
    mock.unknown_pgns = {}
    return mock


@pytest.fixture
def mock_websocket_manager():
    """Mock WebSocketManager for testing."""
    mock = Mock()
    mock.broadcast_message = AsyncMock()
    mock.broadcast_state_update = AsyncMock()
    return mock


@pytest.fixture
def sample_entity():
    """Create a sample entity for testing."""
    mock_entity = Mock(spec=Entity)
    mock_entity.entity_id = "test.entity.1"
    mock_entity.config = {
        "device_type": "light",
        "capabilities": ["brightness", "color"],
        "suggested_area": "living_room",
        "groups": ["main_lights"],
    }
    mock_entity.to_dict = Mock(
        return_value={
            "entity_id": "test.entity.1",
            "device_type": "light",
            "state": {"brightness": 50, "on": True},
        }
    )
    mock_entity.get_history = Mock(return_value=[])
    return mock_entity


@pytest.fixture
def entity_service(mock_entity_manager, mock_websocket_manager):
    """Create EntityService instance with mocked dependencies."""
    return EntityService(
        websocket_manager=mock_websocket_manager, entity_manager=mock_entity_manager
    )


# ================================
# EntityService Tests
# ================================


@pytest.mark.unit
class TestEntityService:
    """Test suite for EntityService business logic."""

    @pytest.mark.asyncio
    async def test_list_entities_no_filter(
        self, entity_service, mock_entity_manager, sample_entity
    ):
        """Test listing all entities without filters."""
        # Arrange
        mock_entity_manager.filter_entities.return_value = {"test.entity.1": sample_entity}

        # Act
        result = await entity_service.list_entities()

        # Assert
        mock_entity_manager.filter_entities.assert_called_once_with(device_type=None, area=None)
        assert "test.entity.1" in result
        assert result["test.entity.1"]["entity_id"] == "test.entity.1"

    @pytest.mark.asyncio
    async def test_list_entities_with_device_type_filter(
        self, entity_service, mock_entity_manager, sample_entity
    ):
        """Test listing entities filtered by device type."""
        # Arrange
        mock_entity_manager.filter_entities.return_value = {"test.entity.1": sample_entity}

        # Act
        result = await entity_service.list_entities(device_type="light")

        # Assert
        mock_entity_manager.filter_entities.assert_called_once_with(device_type="light", area=None)
        assert "test.entity.1" in result

    @pytest.mark.asyncio
    async def test_list_entities_with_area_filter(
        self, entity_service, mock_entity_manager, sample_entity
    ):
        """Test listing entities filtered by area."""
        # Arrange
        mock_entity_manager.filter_entities.return_value = {"test.entity.1": sample_entity}

        # Act
        result = await entity_service.list_entities(area="living_room")

        # Assert
        mock_entity_manager.filter_entities.assert_called_once_with(
            device_type=None, area="living_room"
        )
        assert "test.entity.1" in result

    @pytest.mark.asyncio
    async def test_list_entity_ids(self, entity_service, mock_entity_manager):
        """Test listing all entity IDs."""
        # Arrange
        expected_ids = ["test.entity.1", "test.entity.2", "test.entity.3"]
        mock_entity_manager.get_entity_ids.return_value = expected_ids

        # Act
        result = await entity_service.list_entity_ids()

        # Assert
        assert result == expected_ids
        mock_entity_manager.get_entity_ids.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entity_success(self, entity_service, mock_entity_manager, sample_entity):
        """Test successful retrieval of a specific entity."""
        # Arrange
        entity_id = "test.entity.1"
        mock_entity_manager.get_entity.return_value = sample_entity

        # Act
        result = await entity_service.get_entity(entity_id)

        # Assert
        mock_entity_manager.get_entity.assert_called_once_with(entity_id)
        assert result["entity_id"] == entity_id
        sample_entity.to_dict.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_entity_not_found(self, entity_service, mock_entity_manager):
        """Test getting non-existent entity returns None."""
        # Arrange
        entity_id = "nonexistent.entity"
        mock_entity_manager.get_entity.return_value = None

        # Act
        result = await entity_service.get_entity(entity_id)

        # Assert
        mock_entity_manager.get_entity.assert_called_once_with(entity_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_entity_history_success(
        self, entity_service, mock_entity_manager, sample_entity
    ):
        """Test successful retrieval of entity history."""
        # Arrange
        entity_id = "test.entity.1"
        mock_state = Mock()
        mock_state.model_dump.return_value = {"timestamp": 1234567890, "brightness": 75}
        sample_entity.get_history.return_value = [mock_state]
        mock_entity_manager.get_entity.return_value = sample_entity

        # Act
        result = await entity_service.get_entity_history(entity_id)

        # Assert
        mock_entity_manager.get_entity.assert_called_once_with(entity_id)
        sample_entity.get_history.assert_called_once_with(count=1000, since=None)
        assert len(result) == 1
        assert result[0]["timestamp"] == 1234567890

    @pytest.mark.asyncio
    async def test_get_unmapped_entries(self, entity_service, mock_entity_manager):
        """Test retrieval of unmapped entries."""
        # Arrange
        mock_entity_manager.unmapped_entries = {
            "key1": {
                "pgn_hex": "0xFF01",
                "dgn_hex": "0x1234",
                "instance": "1",
                "last_data_hex": "0xABCD",
                "first_seen_timestamp": 1234567890.0,
                "last_seen_timestamp": 1234567900.0,
                "count": 5,
            },
            "key2": {
                "pgn_hex": "0xFF02",
                "dgn_hex": "0x5678",
                "instance": "2",
                "last_data_hex": "0xEFGH",
                "first_seen_timestamp": 1234567800.0,
                "last_seen_timestamp": 1234567890.0,
                "count": 3,
            },
        }

        # Act
        result = await entity_service.get_unmapped_entries()

        # Assert
        assert "key1" in result
        assert "key2" in result
        assert result["key1"].pgn_hex == "0xFF01"
        assert result["key2"].count == 3

    @pytest.mark.asyncio
    async def test_get_unknown_pgns(self, entity_service, mock_entity_manager):
        """Test retrieval of unknown PGN entries."""
        # Arrange
        mock_entity_manager.unknown_pgns = {
            "pgn1": {
                "arbitration_id_hex": "0x18FF1234",
                "first_seen_timestamp": 1234567890.0,
                "last_seen_timestamp": 1234567900.0,
                "count": 5,
                "last_data_hex": "0xABCDEF12",
            },
            "pgn2": {
                "arbitration_id_hex": "0x18FF5678",
                "first_seen_timestamp": 1234567800.0,
                "last_seen_timestamp": 1234567890.0,
                "count": 3,
                "last_data_hex": "0x12345678",
            },
        }

        # Act
        result = await entity_service.get_unknown_pgns()

        # Assert
        assert "pgn1" in result
        assert "pgn2" in result
        assert result["pgn1"].count == 5
        assert result["pgn2"].arbitration_id_hex == "0x18FF5678"

    @pytest.mark.asyncio
    async def test_get_metadata_with_entities(
        self, entity_service, mock_entity_manager, sample_entity
    ):
        """Test metadata extraction with sample entities."""
        # Arrange
        mock_entity_manager.get_all_entities.return_value = {"test.entity.1": sample_entity}

        # Act
        result = await entity_service.get_metadata()

        # Assert
        assert "device_types" in result
        assert "capabilities" in result
        assert "suggested_areas" in result
        assert "groups" in result

    @pytest.mark.asyncio
    async def test_control_light_entity_not_found(self, entity_service, mock_entity_manager):
        """Test light control for non-existent entity raises ValueError."""
        # Arrange
        entity_id = "nonexistent.light"
        command = ControlCommand(command="turn_on", state="on", brightness=50)
        mock_entity_manager.get_entity.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Entity 'nonexistent.light' not found"):
            await entity_service.control_light(entity_id, command)
