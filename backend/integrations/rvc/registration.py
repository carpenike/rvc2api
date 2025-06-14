"""
RVC Feature Registration module.

This module handles registration of RVC features with the feature management system.
"""

import logging
from typing import Any

from backend.integrations.rvc.feature import RVCFeature
from backend.services.feature_base import Feature
from backend.services.feature_models import SafetyClassification

logger = logging.getLogger(__name__)


def register_rvc_feature(
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
    Factory function for creating an RVCFeature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the RVC feature.

    Args:
        name: Feature name
        enabled: Whether the feature is enabled
        core: Whether this is a core feature
        config: Feature configuration
        dependencies: Feature dependencies
        friendly_name: Human-readable name for the feature
        safety_classification: Safety classification for state validation
        log_state_transitions: Whether to log state transitions for audit

    Returns:
        Initialized RVCFeature instance
    """
    logger.info(f"Registering RVC feature: {name} (enabled={enabled}, core={core})")

    # Create the RVC feature with the provided configuration
    return RVCFeature(
        name=name,
        enabled=enabled,
        core=core,
        config=config,
        dependencies=dependencies,
        friendly_name=friendly_name,
        safety_classification=safety_classification,
        log_state_transitions=log_state_transitions,
    )
