"""
EntityManager Feature for rvc2api.

This module implements the EntityManager as a proper Feature that can be registered
with the FeatureManager, providing an independent entity management system that
completely removes legacy state dictionary dependencies.
"""

import logging
from typing import Any

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
    ) -> None:
        """
        Initialize the EntityManager feature.

        Args:
            name: Feature name (default: "entity_manager")
            enabled: Whether the feature is enabled (default: True)
            core: Whether this is a core feature (default: True)
            config: Configuration options
            dependencies: Feature dependencies
        """
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config or {},
            dependencies=dependencies or [],
        )

        # Initialize the EntityManager
        self.entity_manager = EntityManager()

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

            logger.info(f"Using RV-C spec path: {rvc_spec_path}")
            logger.info(f"Using device mapping path: {device_mapping_path}")

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
                        logger.debug(f"Registered entity: {entity_id} from {dgn_hex}:{instance}")
                    else:
                        logger.warning(
                            f"Entity {entity_id} not found in entity_map for {dgn_hex}:{instance}"
                        )

            logger.info(f"Successfully loaded {len(entity_ids)} entities into EntityManager")

        except Exception as e:
            logger.error(f"Failed to load entity configuration during startup: {e}")
            # Don't fail startup completely, but log the error
            pass

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        logger.info("Shutting down EntityManager feature")
        # EntityManager doesn't require explicit cleanup, but we could add it here if needed

    @property
    def health(self) -> str:
        """Return the health status of the feature."""
        if not self.enabled:
            return "disabled"

        entity_count = len(self.entity_manager.get_entity_ids())
        if entity_count > 0:
            return f"healthy ({entity_count} entities)"
        else:
            return "healthy (no entities loaded)"

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
        raise RuntimeError("EntityManager feature has not been initialized")

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
