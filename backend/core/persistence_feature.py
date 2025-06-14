"""
Persistence Feature for CoachIQ.

This module implements the Persistence service as a proper Feature that can be registered
with the FeatureManager, providing database management, backup operations, and
persistent storage capabilities.
"""

import logging
from typing import TYPE_CHECKING, Any

from backend.core.config import get_persistence_settings
from backend.services.database_engine import DatabaseSettings
from backend.services.feature_base import Feature

if TYPE_CHECKING:
    from backend.services.database_manager import DatabaseManager
    from backend.services.persistence_service import PersistenceService
    from backend.services.repositories import ConfigRepository, DashboardRepository

logger = logging.getLogger(__name__)


class PersistenceFeature(Feature):
    """
    Feature that provides persistent data storage and management.

    This Feature wraps the PersistenceService and DatabaseManager to integrate them
    properly with the FeatureManager system, providing database operations, backup
    management, and configuration persistence.
    """

    def __init__(
        self,
        name: str = "persistence",
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
        safety_classification=None,
        log_state_transitions: bool = True,
        **kwargs
    ) -> None:
        """
        Initialize the Persistence feature.

        Args:
            name: Feature name (default: "persistence")
            enabled: Whether the feature is enabled (default: False)
            core: Whether this is a core feature (default: False)
            config: Configuration options
            dependencies: Feature dependencies
            friendly_name: Human-readable display name for the feature
            safety_classification: Safety classification for state validation
            log_state_transitions: Whether to log state transitions
            **kwargs: Additional arguments for compatibility
        """
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config or {},
            dependencies=dependencies or [],
            friendly_name=friendly_name,
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )

        # Initialize components (lazy loading)
        self._persistence_service: PersistenceService | None = None
        self._database_manager: DatabaseManager | None = None
        self._config_repository: ConfigRepository | None = None
        self._dashboard_repository: DashboardRepository | None = None

    async def startup(self) -> None:
        """Initialize the Persistence feature on startup."""
        logger.info("Starting Persistence feature")

        try:
            # Initialize persistence service
            from backend.services.persistence_service import PersistenceService

            persistence_settings = get_persistence_settings()
            self._persistence_service = PersistenceService(persistence_settings)

            # Initialize the persistence service
            if not await self._persistence_service.initialize():
                logger.error("Failed to initialize persistence service")
                msg = "Persistence service initialization failed"
                raise RuntimeError(msg)

            # Initialize database manager
            from backend.services.database_manager import DatabaseManager

            # Get database settings from config
            database_settings = DatabaseSettings()
            if hasattr(persistence_settings, "data_dir"):
                # Use CoachIQ database name by default
                database_path = persistence_settings.data_dir / "coachiq.db"
                database_settings.sqlite_path = str(database_path)

            self._database_manager = DatabaseManager(database_settings)

            # Initialize database manager
            if not await self._database_manager.initialize():
                logger.error("Failed to initialize database manager")
                msg = "Database manager initialization failed"
                raise RuntimeError(msg)

            # Connect persistence service to database manager
            self._persistence_service.set_database_manager(self._database_manager)

            # Initialize repositories
            from backend.services.repositories import (
                ConfigRepository,
                DashboardRepository,
            )

            self._config_repository = ConfigRepository(self._database_manager)
            self._dashboard_repository = DashboardRepository(self._database_manager)

            # Create default dashboard if it doesn't exist
            await self._dashboard_repository.create_default_dashboard()

            logger.info("Persistence feature started successfully")

        except Exception as e:
            logger.exception("Failed to start persistence feature: %s", e)
            # Clean up partially initialized components
            await self._cleanup()
            raise

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        logger.info("Shutting down Persistence feature")
        await self._cleanup()

    async def _cleanup(self) -> None:
        """Clean up initialized components."""
        try:
            if self._database_manager:
                await self._database_manager.shutdown()
                self._database_manager = None

            if self._persistence_service:
                await self._persistence_service.shutdown()
                self._persistence_service = None

            self._config_repository = None
            self._dashboard_repository = None

        except Exception as e:
            logger.exception("Error during persistence feature cleanup: %s", e)

    @property
    def health(self) -> str:
        """Return the health status of the feature."""
        if not self._persistence_service or not self._database_manager:
            return "unhealthy"

        # Check if services are healthy
        try:
            # Simple health check - more details in health_details
            return "healthy"
        except Exception:
            return "unhealthy"

    @property
    def health_details(self) -> dict[str, Any]:
        """Return detailed health information for diagnostics."""
        if not self._persistence_service or not self._database_manager:
            return {"status": "unhealthy", "reason": "Services not initialized"}

        try:
            details = {
                "status": "healthy",
                "persistence_enabled": True,  # Always enabled in new architecture
                "database_backend": self._database_manager.backend,
                "components": {
                    "persistence_service": "initialized",
                    "database_manager": "initialized",
                    "config_repository": (
                        "initialized" if self._config_repository else "not_initialized"
                    ),
                    "dashboard_repository": (
                        "initialized" if self._dashboard_repository else "not_initialized"
                    ),
                },
            }

            # Add storage info if persistence is enabled (always in new architecture)
            if self._persistence_service:
                import asyncio

                try:
                    # Get storage info (but don't block on it)
                    storage_info = asyncio.create_task(self._persistence_service.get_storage_info())
                    if storage_info.done():
                        details["storage"] = storage_info.result()
                except Exception as e:
                    details["storage_error"] = str(e)

            return details

        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def get_persistence_service(self) -> "PersistenceService":
        """Get the PersistenceService instance."""
        if not self._persistence_service:
            msg = "Persistence service not initialized"
            raise RuntimeError(msg)
        return self._persistence_service

    def get_database_manager(self) -> "DatabaseManager":
        """Get the DatabaseManager instance."""
        if not self._database_manager:
            msg = "Database manager not initialized"
            raise RuntimeError(msg)
        return self._database_manager

    def get_config_repository(self) -> "ConfigRepository":
        """Get the ConfigRepository instance."""
        if not self._config_repository:
            msg = "Config repository not initialized"
            raise RuntimeError(msg)
        return self._config_repository

    def get_dashboard_repository(self) -> "DashboardRepository":
        """Get the DashboardRepository instance."""
        if not self._dashboard_repository:
            msg = "Dashboard repository not initialized"
            raise RuntimeError(msg)
        return self._dashboard_repository


# Singleton instance and accessor functions
_persistence_feature: PersistenceFeature | None = None


def initialize_persistence_feature(
    config: dict[str, Any] | None = None,
) -> PersistenceFeature:
    """
    Initialize the Persistence feature singleton.

    Args:
        config: Optional configuration dictionary

    Returns:
        The initialized PersistenceFeature instance
    """
    global _persistence_feature

    if _persistence_feature is None:
        _persistence_feature = PersistenceFeature(config=config)
        logger.info("Persistence feature singleton initialized")

    return _persistence_feature


def get_persistence_feature() -> PersistenceFeature:
    """
    Get the Persistence feature singleton.

    Returns:
        The PersistenceFeature instance

    Raises:
        RuntimeError: If the feature has not been initialized
    """
    if _persistence_feature is None:
        msg = "Persistence feature has not been initialized"
        raise RuntimeError(msg)

    return _persistence_feature


def get_persistence_service() -> "PersistenceService":
    """
    Get the PersistenceService instance from the feature.

    Returns:
        The PersistenceService instance

    Raises:
        RuntimeError: If the feature has not been initialized
    """
    feature = get_persistence_feature()
    return feature.get_persistence_service()


def get_database_manager() -> "DatabaseManager":
    """
    Get the DatabaseManager instance from the feature.

    Returns:
        The DatabaseManager instance

    Raises:
        RuntimeError: If the feature has not been initialized
    """
    feature = get_persistence_feature()
    return feature.get_database_manager()


def get_config_repository() -> "ConfigRepository":
    """
    Get the ConfigRepository instance from the feature.

    Returns:
        The ConfigRepository instance

    Raises:
        RuntimeError: If the feature has not been initialized
    """
    feature = get_persistence_feature()
    return feature.get_config_repository()


def get_dashboard_repository() -> "DashboardRepository":
    """
    Get the DashboardRepository instance from the feature.

    Returns:
        The DashboardRepository instance

    Raises:
        RuntimeError: If the feature has not been initialized
    """
    feature = get_persistence_feature()
    return feature.get_dashboard_repository()
