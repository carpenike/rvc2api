"""
J1939 feature registration module.

This module handles the registration of the J1939 feature with the feature management system,
following the same pattern as other protocol integrations.
"""

import logging
from typing import Any

from backend.integrations.j1939.feature import J1939Feature

logger = logging.getLogger(__name__)


def register_j1939_feature(
    name: str,
    enabled: bool,
    core: bool,
    config: dict[str, Any],
    dependencies: list[str],
    friendly_name: str | None = None,
) -> J1939Feature:
    """
    Factory function for creating a J1939Feature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the J1939 feature.

    Args:
        name: Feature name
        enabled: Whether the feature is enabled
        core: Whether this is a core feature
        config: Feature configuration dictionary
        dependencies: List of feature dependencies
        friendly_name: Optional friendly name for the feature

    Returns:
        Configured J1939Feature instance
    """
    try:
        # Create and return the J1939 feature
        j1939_feature = J1939Feature(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies,
            friendly_name=friendly_name or "J1939 Protocol",
        )

        logger.info(f"J1939 feature '{name}' created successfully (enabled={enabled})")
        return j1939_feature

    except Exception as e:
        logger.error(f"Failed to create J1939 feature '{name}': {e}")
        raise
