"""
Spartan K2 Chassis Feature Registration

This module handles the registration of the Spartan K2 chassis feature
with the application's feature management system.

Following the established patterns from RV-C, J1939, and Firefly implementations,
this provides seamless integration with the YAML-based feature system.
"""

import logging

from backend.integrations.j1939.spartan_k2_feature import SpartanK2Feature
from backend.services.feature_manager import FeatureManager

logger = logging.getLogger(__name__)


def register_spartan_k2_feature(feature_manager: FeatureManager) -> None:
    """
    Register the Spartan K2 chassis feature with the feature manager.

    Args:
        feature_manager: The application's feature manager instance
    """
    try:
        feature_manager.register_feature("spartan_k2", SpartanK2Feature)
        logger.info("Spartan K2 chassis feature registered successfully")
    except Exception as e:
        logger.error(f"Failed to register Spartan K2 chassis feature: {e}")
        raise
