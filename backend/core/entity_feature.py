"""
EntityManager Feature for CoachIQ.

This module implements the EntityManager as a proper Feature that can be registered
with the FeatureManager, providing an independent entity management system that
completely removes legacy state dictionary dependencies.
"""

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.services.entity_persistence_service import EntityPersistenceService

from backend.core.entity_manager import EntityManager
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class EntityManagerFeature(Feature):
    """
    Feature that provides unified entity state management.

    This Feature wraps the EntityManager to integrate it properly with the
    FeatureManager system, providing an independent entity management system
    that completely replaces legacy state dictionaries.
    """

    def __init__(
        self,
        name: str = "entity_manager",
        enabled: bool = True,
        core: bool = True,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
        safety_classification=None,
        log_state_transitions: bool = True,
        **kwargs
    ) -> None:
        """
        Initialize the EntityManager feature.

        Args:
            name: Feature name (default: "entity_manager")
            enabled: Whether the feature is enabled (default: True)
            core: Whether this is a core feature (default: True)
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

        # Initialize the EntityManager
        self.entity_manager = EntityManager()

        # Initialize the persistence service (will be started in startup)
        self._persistence_service: EntityPersistenceService | None = None

    async def startup(self) -> None:
        """Initialize the EntityManager feature on startup."""
        logger.info("Starting EntityManager feature")

        # Load entities from coach mapping file
        try:
            logger.info("Loading entity configuration from coach mapping files...")

            # Get configuration paths from settings
            from backend.core.config import get_settings

            settings = get_settings()

            rvc_spec_path = str(settings.rvc_spec_path) if settings.rvc_spec_path else None
            device_mapping_path = (
                str(settings.rvc_coach_mapping_path) if settings.rvc_coach_mapping_path else None
            )

            logger.info("Using RV-C spec path: %s", rvc_spec_path)
            logger.info("Using device mapping path: %s", device_mapping_path)

            # Load entity configuration
            from backend.integrations.rvc import load_config_data

            config_result = load_config_data(
                rvc_spec_path_override=rvc_spec_path,
                device_mapping_path_override=device_mapping_path,
            )

            # Extract entity mapping and configuration data
            (
                _decoder_map,
                _spec_meta,
                _mapping_dict,
                entity_map,
                entity_ids,
                entity_id_lookup,
                _light_command_info,
                _pgn_hex_to_name_map,
                _dgn_pairs,
                _coach_info,
            ) = config_result

            # Register all entities with the EntityManager
            for entity_id in entity_ids:
                if entity_id in entity_id_lookup:
                    # Get DGN and instance from entity_id_lookup
                    dgn_instance_info = entity_id_lookup[entity_id]
                    dgn_hex = dgn_instance_info["dgn_hex"]
                    instance = dgn_instance_info["instance"]

                    # Get full entity configuration from entity_map
                    entity_key = (dgn_hex, instance)
                    if entity_key in entity_map:
                        config = entity_map[entity_key]
                        self.entity_manager.register_entity(entity_id, config)
                        logger.debug("Registered entity: %s from %s:%s", entity_id, dgn_hex, instance)
                    else:
                        logger.warning(
                            "Entity %s not found in entity_map for %s:%s", entity_id, dgn_hex, instance
                        )

            logger.info("Successfully loaded %d entities into EntityManager", len(entity_ids))

        except Exception as e:
            logger.error("Failed to load entity configuration during startup: %s", e)
            # Don't fail startup completely, but log the error

        # Initialize entity persistence service using CoreServices
        try:
            from backend.services.entity_persistence_service import EntityPersistenceService
            from backend.services.feature_manager import get_feature_manager

            # Get database manager from CoreServices
            feature_manager = get_feature_manager()
            core_services = feature_manager.get_core_services()
            database_manager = core_services.database_manager

            if database_manager:
                # Create and start the persistence service
                self._persistence_service = EntityPersistenceService(
                    entity_manager=self.entity_manager,
                    database_manager=database_manager,
                    debounce_delay=0.5,  # 500ms debounce for SSD optimization
                )
                await self._persistence_service.start()
                logger.info("Entity persistence service started successfully")
            else:
                logger.warning("Database manager not available - entity persistence disabled")

        except Exception as e:
            logger.error("Failed to initialize entity persistence service: %s", e)
            # Continue without persistence rather than failing startup
            self._persistence_service = None

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        logger.info("Shutting down EntityManager feature")

        # Stop the persistence service if it's running
        if self._persistence_service:
            try:
                await self._persistence_service.stop()
                logger.info("Entity persistence service stopped")
            except Exception as e:
                logger.error("Error stopping entity persistence service: %s", e)

        # EntityManager doesn't require explicit cleanup, but we could add it here if needed

    @property
    def health(self) -> str:
        """Return the health status of the feature."""
        if not self.enabled:
            return "healthy"  # Disabled is considered healthy

        # Return simple status - entity count details should be in health_details
        return "healthy"

    @property
    def health_details(self) -> dict[str, Any]:
        """Return detailed health information for diagnostics."""
        if not self.enabled:
            return {"status": "disabled", "reason": "Feature not enabled"}

        entity_count = len(self.entity_manager.get_entity_ids())
        return {
            "status": "healthy",
            "entity_count": entity_count,
            "description": (
                f"{entity_count} entities loaded" if entity_count > 0 else "No entities loaded"
            ),
        }

    def get_entity_manager(self) -> EntityManager:
        """Get the EntityManager instance."""
        return self.entity_manager


# Singleton instance and accessor functions
_entity_manager_feature: EntityManagerFeature | None = None


def initialize_entity_manager_feature(
    config: dict[str, Any] | None = None,
) -> EntityManagerFeature:
    """
    Initialize the EntityManager feature singleton.

    Args:
        config: Optional configuration dictionary

    Returns:
        The initialized EntityManagerFeature instance
    """
    global _entity_manager_feature

    if _entity_manager_feature is None:
        _entity_manager_feature = EntityManagerFeature(config=config)
        logger.info("EntityManager feature singleton initialized")

    return _entity_manager_feature


def get_entity_manager_feature() -> EntityManagerFeature:
    """
    Get the EntityManager feature singleton.

    Returns:
        The EntityManagerFeature instance

    Raises:
        RuntimeError: If the feature has not been initialized
    """
    if _entity_manager_feature is None:
        msg = "EntityManager feature has not been initialized"
        raise RuntimeError(msg)

    return _entity_manager_feature


def get_entity_manager() -> EntityManager:
    """
    Get the EntityManager instance from the feature.

    Returns:
        The EntityManager instance

    Raises:
        RuntimeError: If the feature has not been initialized
    """
    feature = get_entity_manager_feature()
    return feature.get_entity_manager()
