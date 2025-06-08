"""
Multi-Network CAN Feature Registration

Registers the multi-network CAN feature with the feature management system.
"""

from typing import Any

from backend.integrations.can.multi_network_feature import MultiNetworkCANFeature


def register_multi_network_feature(
    name: str,
    enabled: bool,
    core: bool,
    config: dict[str, Any],
    dependencies: list[str],
    friendly_name: str | None = None,
) -> MultiNetworkCANFeature:
    """
    Factory function for creating a MultiNetworkCANFeature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the multi-network CAN feature.

    Args:
        name: Feature name
        enabled: Whether the feature is enabled
        core: Whether this is a core feature
        config: Feature configuration dictionary
        dependencies: List of feature dependencies
        friendly_name: Optional friendly name for the feature

    Returns:
        Configured MultiNetworkCANFeature instance
    """
    return MultiNetworkCANFeature(
        name=name,
        enabled=enabled,
        core=core,
        config=config,
        dependencies=dependencies,
        friendly_name=friendly_name,
    )
