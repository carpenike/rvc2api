"""
Notification Feature Registration

Registration module for the notification feature following the established
feature management patterns.
"""

import logging
from typing import Any

from backend.integrations.notifications.feature import NotificationFeature
from backend.services.feature_models import SafetyClassification

logger = logging.getLogger(__name__)


def register_notification_feature(
    name: str,
    enabled: bool,
    core: bool,
    config: dict[str, Any],
    dependencies: list[str],
    friendly_name: str | None = None,
    safety_classification: SafetyClassification | None = None,
    log_state_transitions: bool = True,
) -> NotificationFeature:
    """
    Factory function to create and configure a notification feature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the notification feature.

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
        NotificationFeature: Configured notification feature instance
    """
    logger.info("Registering notification feature")

    try:
        feature = NotificationFeature(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies,
            friendly_name=friendly_name,
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )
        logger.info("Notification feature registered successfully")
        return feature

    except Exception as e:
        logger.error(f"Failed to register notification feature: {e}")
        raise
