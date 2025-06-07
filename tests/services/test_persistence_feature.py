"""
Tests for the PersistenceFeature.

Tests the feature wrapper functionality including lifecycle management,
health monitoring, and integration with the feature system.
"""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest

from backend.core.config import PersistenceSettings
from backend.services.persistence_feature import PersistenceFeature
from backend.services.persistence_service import PersistenceService


class TestPersistenceFeature:
    """Test cases for PersistenceFeature."""

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_settings(self, temp_data_dir):
        """Mock persistence settings."""
        return PersistenceSettings(
            enabled=True, data_dir=temp_data_dir, create_dirs=True, backup_enabled=True
        )

    @pytest.fixture
    def persistence_feature(self):
        """Create a PersistenceFeature instance."""
        return PersistenceFeature(enabled=True, core=True, config={}, dependencies=[])

    async def test_feature_initialization(self, persistence_feature):
        """Test feature initialization."""
        assert persistence_feature.name == "persistence"
        assert persistence_feature.enabled is True
        assert persistence_feature.core is True
        assert persistence_feature.dependencies == []

    async def test_startup_enabled(self, persistence_feature, mock_settings):
        """Test successful startup when feature is enabled."""
        with patch(
            "backend.services.persistence_feature.get_persistence_settings",
            return_value=mock_settings,
        ):
            await persistence_feature.startup()

            assert persistence_feature._service is not None
            assert isinstance(persistence_feature._service, PersistenceService)
            assert persistence_feature._initialization_error is None

    async def test_startup_disabled(self):
        """Test startup when feature is disabled."""
        feature = PersistenceFeature(enabled=False)

        await feature.startup()

        assert feature._service is None
        assert feature._initialization_error is None

    async def test_startup_with_initialization_error(self, persistence_feature):
        """Test startup handling of initialization errors."""
        with patch(
            "backend.services.persistence_feature.get_persistence_settings"
        ) as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings

            with patch(
                "backend.services.persistence_feature.PersistenceService"
            ) as mock_service_class:
                mock_service = AsyncMock()
                mock_service.initialize.return_value = False  # Initialization fails
                mock_service_class.return_value = mock_service

                await persistence_feature.startup()

                assert persistence_feature._service is not None
                assert persistence_feature._initialization_error is not None
                assert (
                    "Failed to initialize persistence service"
                    in persistence_feature._initialization_error
                )

    async def test_startup_with_exception(self, persistence_feature):
        """Test startup handling of exceptions."""
        with patch(
            "backend.services.persistence_feature.get_persistence_settings",
            side_effect=Exception("Test error"),
        ):
            await persistence_feature.startup()

            assert persistence_feature._initialization_error is not None
            assert "Test error" in persistence_feature._initialization_error

    async def test_shutdown_enabled(self, persistence_feature):
        """Test shutdown when feature is enabled."""
        # Set up a mock service
        mock_service = AsyncMock()
        persistence_feature._service = mock_service

        await persistence_feature.shutdown()

        mock_service.shutdown.assert_called_once()

    async def test_shutdown_disabled(self):
        """Test shutdown when feature is disabled."""
        feature = PersistenceFeature(enabled=False)

        # Should not raise any exceptions
        await feature.shutdown()

    async def test_shutdown_no_service(self, persistence_feature):
        """Test shutdown when no service is initialized."""
        # Should not raise any exceptions
        await persistence_feature.shutdown()

    async def test_health_disabled(self):
        """Test health status when feature is disabled."""
        feature = PersistenceFeature(enabled=False)

        assert feature.health == "healthy"

    async def test_health_initialization_error(self, persistence_feature):
        """Test health status with initialization error."""
        persistence_feature._initialization_error = "Some error"

        assert persistence_feature.health == "degraded"

    async def test_health_no_service(self, persistence_feature):
        """Test health status when service is not initialized."""
        assert persistence_feature.health == "failed"

    async def test_health_service_not_initialized(self, persistence_feature):
        """Test health status when service exists but not initialized."""
        mock_service = Mock()
        mock_service._initialized = False
        persistence_feature._service = mock_service

        assert persistence_feature.health == "failed"

    async def test_health_service_disabled(self, persistence_feature):
        """Test health status when service is disabled."""
        mock_service = Mock()
        mock_service._initialized = True
        mock_service.enabled = False
        persistence_feature._service = mock_service

        assert persistence_feature.health == "degraded"

    async def test_health_healthy(self, persistence_feature):
        """Test health status when everything is working."""
        mock_service = Mock()
        mock_service._initialized = True
        mock_service.enabled = True
        persistence_feature._service = mock_service

        assert persistence_feature.health == "healthy"

    async def test_get_service_success(self, persistence_feature):
        """Test getting service when available."""
        mock_service = Mock()
        persistence_feature._service = mock_service

        service = persistence_feature.get_service()

        assert service is mock_service

    async def test_get_service_disabled(self):
        """Test getting service when feature is disabled."""
        feature = PersistenceFeature(enabled=False)

        with pytest.raises(RuntimeError, match="Persistence feature is disabled"):
            feature.get_service()

    async def test_get_service_not_initialized(self, persistence_feature):
        """Test getting service when not initialized."""
        with pytest.raises(RuntimeError, match="Persistence service not initialized"):
            persistence_feature.get_service()

    async def test_get_storage_info_success(self, persistence_feature):
        """Test getting storage info when service is available."""
        mock_service = AsyncMock()
        mock_service.get_storage_info.return_value = {"enabled": True, "data": "test"}
        persistence_feature._service = mock_service

        storage_info = await persistence_feature.get_storage_info()

        assert storage_info == {"enabled": True, "data": "test"}
        mock_service.get_storage_info.assert_called_once()

    async def test_get_storage_info_disabled(self):
        """Test getting storage info when feature is disabled."""
        feature = PersistenceFeature(enabled=False)

        storage_info = await feature.get_storage_info()

        assert storage_info == {"enabled": False, "error": "Service not available"}

    async def test_get_storage_info_error(self, persistence_feature):
        """Test getting storage info with service error."""
        mock_service = AsyncMock()
        mock_service.get_storage_info.side_effect = Exception("Service error")
        persistence_feature._service = mock_service

        storage_info = await persistence_feature.get_storage_info()

        assert storage_info == {"enabled": True, "error": "Service error"}

    async def test_backup_database_success(self, persistence_feature):
        """Test database backup when service is available."""
        mock_service = AsyncMock()
        mock_service.backup_database.return_value = Path("/backup/path.db")
        persistence_feature._service = mock_service

        backup_path = await persistence_feature.backup_database("/db/path.db", "backup_name")

        assert backup_path == Path("/backup/path.db")
        mock_service.backup_database.assert_called_once_with("/db/path.db", "backup_name")

    async def test_backup_database_unavailable(self):
        """Test database backup when service is unavailable."""
        feature = PersistenceFeature(enabled=False)

        backup_path = await feature.backup_database("/db/path.db")

        assert backup_path is None

    async def test_list_backups_success(self, persistence_feature):
        """Test listing backups when service is available."""
        mock_service = AsyncMock()
        mock_service.list_backups.return_value = [{"name": "backup1.db"}]
        persistence_feature._service = mock_service

        backups = await persistence_feature.list_backups("test_db")

        assert backups == [{"name": "backup1.db"}]
        mock_service.list_backups.assert_called_once_with("test_db")

    async def test_list_backups_unavailable(self):
        """Test listing backups when service is unavailable."""
        feature = PersistenceFeature(enabled=False)

        backups = await feature.list_backups()

        assert backups == []

    async def test_save_user_config_success(self, persistence_feature):
        """Test saving user config when service is available."""
        mock_service = AsyncMock()
        mock_service.save_user_config.return_value = True
        persistence_feature._service = mock_service

        config_data = {"theme": "dark"}
        success = await persistence_feature.save_user_config("user_settings", config_data)

        assert success is True
        mock_service.save_user_config.assert_called_once_with("user_settings", config_data)

    async def test_save_user_config_unavailable(self):
        """Test saving user config when service is unavailable."""
        feature = PersistenceFeature(enabled=False)

        success = await feature.save_user_config("config", {})

        assert success is False

    async def test_load_user_config_success(self, persistence_feature):
        """Test loading user config when service is available."""
        mock_service = AsyncMock()
        mock_service.load_user_config.return_value = {"theme": "dark"}
        persistence_feature._service = mock_service

        config_data = await persistence_feature.load_user_config("user_settings")

        assert config_data == {"theme": "dark"}
        mock_service.load_user_config.assert_called_once_with("user_settings")

    async def test_load_user_config_unavailable(self):
        """Test loading user config when service is unavailable."""
        feature = PersistenceFeature(enabled=False)

        config_data = await feature.load_user_config("config")

        assert config_data is None


class TestPersistenceFeatureSingleton:
    """Test singleton access functions for PersistenceFeature."""

    def test_get_feature_not_initialized(self):
        """Test getting feature when not initialized."""
        from backend.services.persistence_feature import (
            _persistence_feature,
            get_persistence_feature,
        )

        # Ensure feature is not set
        if _persistence_feature is not None:
            from backend.services.persistence_feature import set_persistence_feature

            set_persistence_feature(None)

        with pytest.raises(RuntimeError, match="Persistence feature not initialized"):
            get_persistence_feature()

    def test_set_and_get_feature(self):
        """Test setting and getting feature instance."""
        from backend.services.persistence_feature import (
            get_persistence_feature,
            set_persistence_feature,
        )

        feature = PersistenceFeature(enabled=True)
        set_persistence_feature(feature)

        retrieved_feature = get_persistence_feature()

        assert retrieved_feature is feature

    def teardown_method(self):
        """Clean up singleton state after each test."""
        from backend.services.persistence_feature import set_persistence_feature

        set_persistence_feature(None)
