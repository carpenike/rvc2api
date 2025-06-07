"""
Persistence Feature

Feature wrapper for the PersistenceService, providing lifecycle management
and integration with the feature manager system.
"""

import logging

from backend.core.config import get_persistence_settings
from backend.services.feature_base import Feature
from backend.services.persistence_service import PersistenceService

logger = logging.getLogger(__name__)


class PersistenceFeature(Feature):
    """
    Feature wrapper for the PersistenceService.

    Provides lifecycle management, health monitoring, and integration
    with the feature management system for data persistence capabilities.
    """

    def __init__(self, **kwargs):
        """Initialize the persistence feature."""
        super().__init__(
            name="persistence",
            enabled=kwargs.get("enabled", True),
            core=kwargs.get("core", True),
            config=kwargs.get("config", {}),
            dependencies=kwargs.get("dependencies", []),
        )
        self._service: PersistenceService | None = None
        self._initialization_error: str | None = None

    async def startup(self) -> None:
        """Initialize the persistence service during startup."""
        if not self.enabled:
            logger.info("Persistence feature is disabled, skipping startup")
            return

        try:
            logger.info("Starting persistence feature")

            # Load settings
            settings = get_persistence_settings()

            # Create service instance
            self._service = PersistenceService(settings)

            # Initialize the service
            success = await self._service.initialize()

            if not success:
                self._initialization_error = "Failed to initialize persistence service"
                logger.error(self._initialization_error)
                return

            logger.info(
                f"Persistence feature started successfully. "
                f"Data directory: {self._service.data_dir}"
            )

            # Log storage information
            if self._service.enabled:
                storage_info = await self._service.get_storage_info()
                if "directories" in storage_info:
                    logger.info(
                        f"Persistence directories available: {list(storage_info['directories'].keys())}"
                    )

                # Log disk space information if available
                if "disk_usage" in storage_info:
                    disk = storage_info["disk_usage"]
                    logger.info(
                        f"Disk usage: {disk.get('usage_percent', 0):.1f}% "
                        f"({disk.get('free_gb', 0):.1f}GB free)"
                    )

        except Exception as e:
            self._initialization_error = f"Persistence feature startup failed: {e}"
            logger.error(self._initialization_error)
            # Don't re-raise - let the service start in degraded mode

    async def shutdown(self) -> None:
        """Clean shutdown of the persistence service."""
        if not self.enabled or not self._service:
            return

        try:
            logger.info("Shutting down persistence feature")
            await self._service.shutdown()
            logger.info("Persistence feature shutdown complete")
        except Exception as e:
            logger.error(f"Error during persistence feature shutdown: {e}")

    @property
    def health(self) -> str:
        """
        Return the health status of the persistence feature.

        Returns:
            "healthy" if service is functioning correctly
            "degraded" if service has initialization errors but is enabled
            "failed" if service has critical errors
        """
        if not self.enabled:
            return "healthy"  # Disabled features are considered healthy

        if self._initialization_error:
            return "degraded"

        if not self._service:
            return "failed"

        # Check if the service is properly initialized
        if not self._service._initialized:
            return "failed"

        # If persistence is disabled but feature is enabled, that's degraded
        if not self._service.enabled:
            return "degraded"

        return "healthy"

    def get_service(self) -> PersistenceService:
        """
        Get the persistence service instance.

        Returns:
            The PersistenceService instance

        Raises:
            RuntimeError: If the service is not initialized
        """
        if not self.enabled:
            raise RuntimeError("Persistence feature is disabled")

        if not self._service:
            raise RuntimeError("Persistence service not initialized")

        return self._service

    async def get_storage_info(self) -> dict:
        """
        Get storage information from the persistence service.

        Returns:
            Storage information dictionary
        """
        if not self.enabled or not self._service:
            return {"enabled": False, "error": "Service not available"}

        try:
            return await self._service.get_storage_info()
        except Exception as e:
            logger.error(f"Failed to get storage info: {e}")
            return {"enabled": True, "error": str(e)}

    async def backup_database(self, database_path, backup_name=None):
        """
        Create a database backup.

        Args:
            database_path: Path to the database to backup
            backup_name: Optional custom backup name

        Returns:
            Path to backup file if successful, None otherwise
        """
        if not self.enabled or not self._service:
            logger.warning("Cannot backup database: persistence service not available")
            return None

        return await self._service.backup_database(database_path, backup_name)

    async def list_backups(self, database_name=None):
        """
        List available database backups.

        Args:
            database_name: Optional filter by database name

        Returns:
            List of backup information
        """
        if not self.enabled or not self._service:
            return []

        return await self._service.list_backups(database_name)

    async def save_user_config(self, config_name: str, config_data: dict) -> bool:
        """
        Save user configuration data.

        Args:
            config_name: Name of the configuration
            config_data: Configuration data to save

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self._service:
            return False

        return await self._service.save_user_config(config_name, config_data)

    async def load_user_config(self, config_name: str) -> dict | None:
        """
        Load user configuration data.

        Args:
            config_name: Name of the configuration

        Returns:
            Configuration data if found, None otherwise
        """
        if not self.enabled or not self._service:
            return None

        return await self._service.load_user_config(config_name)


# Global instance for singleton access
_persistence_feature: PersistenceFeature | None = None


def get_persistence_feature() -> PersistenceFeature:
    """
    Get the global persistence feature instance.

    Returns:
        The PersistenceFeature instance

    Raises:
        RuntimeError: If the feature is not initialized
    """
    global _persistence_feature
    if _persistence_feature is None:
        raise RuntimeError("Persistence feature not initialized")
    return _persistence_feature


def set_persistence_feature(feature: PersistenceFeature) -> None:
    """
    Set the global persistence feature instance.

    Args:
        feature: The PersistenceFeature instance to set
    """
    global _persistence_feature
    _persistence_feature = feature
