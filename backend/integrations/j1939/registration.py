"""
J1939 feature registration module.

This module handles the registration of the J1939 feature with the feature management system,
following the same pattern as other protocol integrations.
"""

import logging

from backend.integrations.j1939.feature import J1939Feature
from backend.services.feature_manager import FeatureManager

logger = logging.getLogger(__name__)


def register_j1939_feature(feature_manager: FeatureManager) -> None:
    """
    Register the J1939 feature with the feature manager.

    Args:
        feature_manager: The FeatureManager instance to register with
    """
    try:
        # Get feature configuration from the feature manager's config
        feature_config = feature_manager.get_feature_config("j1939")

        if feature_config is None:
            logger.warning("J1939 feature configuration not found - registering with defaults")
            feature_config = {
                "enabled": False,
                "enable_cummins_extensions": True,
                "enable_allison_extensions": True,
                "enable_chassis_extensions": True,
                "enable_validator": True,
                "enable_security": True,
                "enable_performance": True,
                "enable_rvc_bridge": True,
                "max_queue_size": 10000,
            }

        # Create and register the J1939 feature
        j1939_feature = J1939Feature(
            name="j1939",
            enabled=feature_config.get("enabled", False),
            core=feature_config.get("core", False),
            config=feature_config,
            dependencies=feature_config.get("depends_on", ["can_interface"]),
            friendly_name=feature_config.get("friendly_name", "J1939 Protocol"),
        )

        # Register with the feature manager
        feature_manager.register_feature(j1939_feature)

        logger.info("J1939 feature registered successfully")

    except Exception as e:
        logger.error(f"Failed to register J1939 feature: {e}")
        raise
