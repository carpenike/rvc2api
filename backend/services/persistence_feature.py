"""
Simplified Persistence Feature

Feature wrapper for persistence services, using dependency injection
to provide appropriate implementations based on configuration.
"""

import logging
from pathlib import Path

from backend.core.config import get_persistence_settings, get_settings
from backend.models.persistence import StorageInfo
from backend.services.feature_base import Feature
from backend.services.in_memory_persistence import InMemoryPersistenceService
from backend.services.persistence_interface import PersistenceServiceInterface
from backend.services.sqlite_persistence import SQLitePersistenceService

logger = logging.getLogger(__name__)


class PersistenceFeature(Feature):
    """
    Simplified persistence feature using dependency injection.

    Automatically selects the appropriate persistence implementation
    based on the persistence settings without complex conditional logic.
    """

    def __init__(self, **kwargs):
        """Initialize the persistence feature."""
        super().__init__(
            name="persistence",
            enabled=kwargs.get("enabled", True),
            core=kwargs.get("core", True),
            config=kwargs.get("config", {}),
            dependencies=kwargs.get("dependencies", []),
            friendly_name=kwargs.get("friendly_name"),
        )
        self._service: PersistenceServiceInterface | None = None
        self._initialization_error: str | None = None
        self._persistence_enabled: bool = False

    async def startup(self) -> None:
        """Initialize the persistence service during startup."""
        if not self.enabled:
            logger.info("Persistence feature is disabled, skipping startup")
            return

        try:
            logger.info("Starting persistence feature")

            # Load settings to determine persistence mode
            settings = get_settings()
            persistence_settings = get_persistence_settings()
            self._persistence_enabled = persistence_settings.enabled

            # Use dependency injection to select implementation
            if self._persistence_enabled:
                # Use SQLite persistence
                if settings.is_development():
                    # Development-friendly path
                    db_path = "backend/data/persistent/database/coachiq.db"
                    # Ensure directory exists
                    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
                else:
                    # Production path
                    db_path = str(persistence_settings.get_database_dir() / "coachiq.db")
                    # Ensure directory exists
                    persistence_settings.ensure_directories()

                logger.info(f"Initializing SQLite persistence with database: {db_path}")
                self._service = SQLitePersistenceService(db_path)
            else:
                # Use in-memory persistence
                logger.info("Initializing in-memory persistence (no database persistence)")
                self._service = InMemoryPersistenceService()

            # Initialize the service
            await self._service.initialize()

            logger.info(
                f"Persistence feature started successfully in {'SQLite' if self._persistence_enabled else 'in-memory'} mode"
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

        return "healthy"

    def get_service(self) -> PersistenceServiceInterface:
        """
        Get the persistence service instance.

        Returns:
            The PersistenceServiceInterface instance

        Raises:
            RuntimeError: If the service is not initialized
        """
        if not self.enabled:
            raise RuntimeError("Persistence feature is disabled")

        if not self._service:
            raise RuntimeError("Persistence service not initialized")

        return self._service

    def is_persistence_enabled(self) -> bool:
        """Check if database persistence is enabled."""
        return self._persistence_enabled

    async def get_storage_info(self) -> StorageInfo:
        """
        Get storage information from the persistence service.

        Returns:
            Storage information object
        """
        if not self.enabled or not self._service:
            return StorageInfo(
                enabled=False,
                data_dir=None,
                directories=None,
                disk_usage=None,
                backup_settings=None,
                error="Service not available",
            )

        # For now, return simplified storage info
        # The full storage info implementation would require extending the interface
        return StorageInfo(
            enabled=self._persistence_enabled,
            data_dir="/var/lib/coachiq" if self._persistence_enabled else None,
            directories=None,
            disk_usage=None,
            backup_settings=None,
            error=None,
        )

    def get_config_repository(self):
        """Get the configuration repository."""
        if not self._service:
            return None
        return self._service.config_repo

    def get_dashboard_repository(self):
        """Get the dashboard repository."""
        if not self._service:
            return None
        return self._service.dashboard_repo

    def get_unmapped_repository(self):
        """Get the unmapped PGN repository."""
        if not self._service:
            return None
        return self._service.unmapped_repo


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
