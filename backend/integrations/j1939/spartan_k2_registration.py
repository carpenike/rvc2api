"""
Spartan K2 Chassis Feature Registration

This module handles the registration of the Spartan K2 chassis feature
with the application's feature management system.

Following the established patterns from RV-C, J1939, and Firefly implementations,
this provides seamless integration with the YAML-based feature system.
"""

import logging
from typing import TYPE_CHECKING, Any

from backend.services.feature_models import SafetyClassification

if TYPE_CHECKING:
    from backend.integrations.j1939.spartan_k2_feature import SpartanK2Feature

logger = logging.getLogger(__name__)


def register_spartan_k2_feature(
    name: str,
    enabled: bool,
    core: bool,
    config: dict[str, Any],
    dependencies: list[str],
    friendly_name: str | None = None,
    safety_classification: SafetyClassification | None = None,
    log_state_transitions: bool = True,
) -> "SpartanK2Feature":
    """
    Factory function for creating a SpartanK2Feature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the Spartan K2 feature.

    Args:
        name: Feature name
        enabled: Whether the feature is enabled
        core: Whether this is a core feature
        config: Feature configuration
        dependencies: List of feature dependencies
        friendly_name: Human-readable feature name
        safety_classification: Safety classification for state validation
        log_state_transitions: Whether to log state transitions for audit

    Returns:
        SpartanK2Feature instance
    """
    try:
        from backend.integrations.j1939.spartan_k2_feature import SpartanK2Feature

        # Create Spartan K2 feature instance
        spartan_k2_feature = SpartanK2Feature(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies,
            friendly_name=friendly_name or "Spartan K2 Chassis",
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )

        logger.info("Spartan K2 chassis feature created successfully")
        return spartan_k2_feature

    except Exception as e:
        logger.error(f"Failed to create Spartan K2 chassis feature: {e}")
        raise
