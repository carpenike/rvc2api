"""
Multi-Network CAN Feature Registration

Registers the multi-network CAN feature with the feature management system.
"""

from typing import Any

from backend.integrations.can.multi_network_feature import MultiNetworkCANFeature
from backend.services.feature_models import SafetyClassification


def register_multi_network_feature(
    name: str,
    enabled: bool,
    core: bool,
    config: dict[str, Any],
    dependencies: list[str],
    friendly_name: str | None = None,
    safety_classification: SafetyClassification | None = None,
    log_state_transitions: bool = True,
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
        safety_classification: Safety classification for state validation
        log_state_transitions: Whether to log state transitions for audit

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
        safety_classification=safety_classification,
        log_state_transitions=log_state_transitions,
    )
