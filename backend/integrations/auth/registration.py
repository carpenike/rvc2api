"""
Authentication feature registration.

This module provides the factory function for creating authentication feature instances
with the feature management system.
"""

import logging
from typing import Any

from backend.integrations.auth.feature import AuthenticationFeature
from backend.services.feature_models import SafetyClassification

logger = logging.getLogger(__name__)


def register_authentication_feature(
    name: str,
    enabled: bool,
    core: bool,
    config: dict[str, Any],
    dependencies: list[str],
    friendly_name: str | None = None,
    safety_classification: SafetyClassification | None = None,
    log_state_transitions: bool = True,
) -> AuthenticationFeature:
    """
    Factory function to create and configure an authentication feature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the authentication feature.

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
        AuthenticationFeature: Configured authentication feature instance
    """
    logger.info("Registering authentication feature")

    try:
        feature = AuthenticationFeature(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies,
            friendly_name=friendly_name,
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )
        logger.info("Authentication feature registered successfully")
        return feature

    except Exception as e:
        logger.error(f"Failed to register authentication feature: {e}")
        raise
