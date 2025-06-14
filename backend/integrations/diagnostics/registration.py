"""
Advanced Diagnostics Feature Registration

Registration module for the advanced diagnostics feature following the
established pattern from other features.
"""

import logging
from typing import Any

from backend.integrations.diagnostics.feature import AdvancedDiagnosticsFeature
from backend.services.feature_base import Feature
from backend.services.feature_models import SafetyClassification

logger = logging.getLogger(__name__)


def register_advanced_diagnostics_feature(
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
    Factory function for creating an AdvancedDiagnosticsFeature instance.

    This function is called by the feature manager when loading features from YAML.
    It allows custom instantiation logic for the advanced diagnostics feature.

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
        Initialized AdvancedDiagnosticsFeature instance
    """
    logger.info(
        f"Registering advanced diagnostics feature: {name} (enabled={enabled}, core={core})"
    )

    # Create the advanced diagnostics feature with the provided configuration
    diagnostics_feature = AdvancedDiagnosticsFeature(
        name=name,
        enabled=enabled,
        core=core,
        config=config,
        dependencies=dependencies,
        friendly_name=friendly_name,
        safety_classification=safety_classification,
        log_state_transitions=log_state_transitions,
    )

    logger.info(f"Advanced diagnostics feature '{name}' created successfully")
    return diagnostics_feature


def is_advanced_diagnostics_enabled(settings) -> bool:
    """
    Check if advanced diagnostics feature should be enabled.

    Args:
        settings: Application settings

    Returns:
        True if feature should be enabled
    """
    diag_settings = getattr(settings, "advanced_diagnostics", None)
    return diag_settings is not None and getattr(diag_settings, "enabled", False)
