"""
Tests for the entities API endpoints.

This module tests the /api/entities endpoints including list operations,
entity retrieval, control operations, and metadata endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_entities_success(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test successful retrieval of all entities."""
    # Arrange
    mock_entities = {
        "light_1": {
            "id": "light_1",
            "name": "Kitchen Light",
            "device_type": "light",
            "value": True,
        },
        "sensor_1": {
            "id": "sensor_1",
            "name": "Temperature Sensor",
            "device_type": "sensor",
            "value": 20.5,
        },
    }
    override_entity_service.list_entities.return_value = mock_entities
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get("/api/entities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "light_1" in data
    assert "sensor_1" in data
    override_entity_service.list_entities.assert_called_once_with(device_type=None, area=None)


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_entities_with_device_type_filter(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test entity listing with device_type filter."""
    # Arrange
    mock_entities = {
        "light_1": {
            "id": "light_1",
            "name": "Kitchen Light",
            "device_type": "light",
            "value": True,
        },
    }
    override_entity_service.list_entities.return_value = mock_entities
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get("/api/entities?device_type=light")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "light_1" in data
    override_entity_service.list_entities.assert_called_once_with(device_type="light", area=None)


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_entities_rvc_disabled(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test entity listing when RVC feature is disabled."""
    # Arrange
    override_feature_manager.is_enabled.return_value = False

    # Act
    response = await async_client.get("/api/entities")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "rvc feature is disabled" in data["detail"]
    override_entity_service.list_entities.assert_not_called()


@pytest.mark.api
@pytest.mark.asyncio
async def test_list_entity_ids_success(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test successful retrieval of entity IDs."""
    # Arrange
    mock_ids = ["light_1", "sensor_1", "lock_1"]
    override_entity_service.list_entity_ids.return_value = mock_ids
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get("/api/entities/ids")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data == mock_ids
    override_entity_service.list_entity_ids.assert_called_once()


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_entity_success(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test successful retrieval of a specific entity by ID."""
    # Arrange
    entity_id = "light_1"
    mock_entity = {"id": entity_id, "name": "Kitchen Light", "device_type": "light", "value": True}
    override_entity_service.get_entity.return_value = mock_entity
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get(f"/api/entities/{entity_id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == entity_id
    assert data["name"] == "Kitchen Light"
    override_entity_service.get_entity.assert_called_once_with(entity_id)


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_entity_not_found(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test entity not found returns 404."""
    # Arrange
    entity_id = "nonexistent_entity"
    override_entity_service.get_entity.return_value = None
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get(f"/api/entities/{entity_id}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "Entity 'nonexistent_entity' not found" in data["detail"]
    override_entity_service.get_entity.assert_called_once_with(entity_id)


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_unmapped_entries_success(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test successful retrieval of unmapped entries."""
    # Arrange
    mock_unmapped = {
        "unmapped_entries": [
            {"dgn": 65280, "instance": 1, "count": 5, "last_seen": "2023-01-01T12:00:00Z"}
        ]
    }
    override_entity_service.get_unmapped_entries.return_value = mock_unmapped
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get("/api/unmapped")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "unmapped_entries" in data
    assert len(data["unmapped_entries"]) == 1
    override_entity_service.get_unmapped_entries.assert_called_once()


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_unknown_pgns_success(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test successful retrieval of unknown PGNs."""
    # Arrange
    mock_unknown = {
        "unknown_pgns": [{"pgn": 123456, "count": 3, "last_seen": "2023-01-01T12:00:00Z"}]
    }
    override_entity_service.get_unknown_pgns.return_value = mock_unknown
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get("/api/unknown-pgns")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "unknown_pgns" in data
    assert len(data["unknown_pgns"]) == 1
    override_entity_service.get_unknown_pgns.assert_called_once()


@pytest.mark.api
@pytest.mark.asyncio
async def test_get_metadata_success(
    async_client: AsyncClient, override_entity_service, override_feature_manager
):
    """Test successful retrieval of metadata."""
    # Arrange
    mock_metadata = {
        "entity_types": ["light", "sensor", "lock"],
        "areas": ["kitchen", "living_room", "bedroom"],
        "total_entities": 15,
    }
    override_entity_service.get_metadata.return_value = mock_metadata
    override_feature_manager.is_enabled.return_value = True

    # Act
    response = await async_client.get("/api/metadata")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "entity_types" in data
    assert "areas" in data
    assert data["total_entities"] == 15
    override_entity_service.get_metadata.assert_called_once()
