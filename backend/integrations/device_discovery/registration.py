"""
Device Discovery Feature Registration

Registers the device discovery feature with the feature management system.
"""

import logging
from typing import Any

from backend.integrations.device_discovery.feature import DeviceDiscoveryFeature
from backend.services.feature_base import Feature
from backend.services.feature_models import SafetyClassification

logger = logging.getLogger(__name__)


def register_device_discovery_feature(
    name: str,
    enabled: bool,
    core: bool,
    config: dict[str, Any],
    dependencies: list[str],
    friendly_name: str | None = None,
    safety_classification: SafetyClassification | None = None,
    log_state_transitions: bool = True,
) -> Feature:
    """
    Factory function for creating a DeviceDiscoveryFeature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the device discovery feature.

    Args:
        name: Feature name
        enabled: Whether the feature is enabled
        core: Whether this is a core feature
        config: Feature configuration dictionary
        dependencies: List of feature dependencies
        friendly_name: Optional human-readable name
        safety_classification: Safety classification for state validation
        log_state_transitions: Whether to log state transitions for audit

    Returns:
        DeviceDiscoveryFeature instance
    """
    try:
        logger.info(f"Registering device discovery feature: {name}")

        feature = DeviceDiscoveryFeature(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies,
            friendly_name=friendly_name,
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )

        logger.info("Device discovery feature registered successfully")
        return feature

    except Exception as e:
        logger.error(f"Failed to register device discovery feature: {e}", exc_info=True)
        raise
