"""
Integration registrations for rvc2api.

This module registers custom feature implementations with the feature manager.
"""

import logging

from backend.can.feature import CANBusFeature
from backend.core.state import AppState
from backend.integrations.rvc.registration import register_rvc_feature
from backend.services.feature_manager import FeatureManager
from backend.services.github_update_checker import register_github_update_checker_feature
from backend.services.persistence_feature import PersistenceFeature, set_persistence_feature
from backend.websocket.handlers import WebSocketManager

logger = logging.getLogger(__name__)


def _create_websocket_feature(**kwargs):
    """Factory function for WebSocketManager feature."""
    return WebSocketManager(**kwargs)


def _create_can_feature(**kwargs):
    """Factory function for CANBusFeature."""
    return CANBusFeature(**kwargs)


def _create_app_state_feature(**kwargs):
    """Factory function for AppState feature."""
    return AppState(**kwargs)


def _create_persistence_feature(**kwargs):
    """Factory function for PersistenceFeature."""
    feature = PersistenceFeature(**kwargs)
    # Set the global instance for singleton access
    set_persistence_feature(feature)
    return feature


# Register custom feature factories
FeatureManager.register_feature_factory("persistence", _create_persistence_feature)
FeatureManager.register_feature_factory("websocket", _create_websocket_feature)
FeatureManager.register_feature_factory("can_feature", _create_can_feature)
FeatureManager.register_feature_factory("app_state", _create_app_state_feature)
FeatureManager.register_feature_factory("rvc", register_rvc_feature)
FeatureManager.register_feature_factory(
    "github_update_checker", register_github_update_checker_feature
)


def register_custom_features() -> None:
    """
    Register all custom features with the feature manager.

    This function is called during application startup to register
    any custom feature implementations that aren't loaded automatically
    from the feature_flags.yaml file.
    """
    logger.info("Registering custom feature implementations")
    # All feature factory registrations are done at module import time above
    # This function exists to provide a clear entry point during startup
    # and to allow for any additional dynamic registrations in the future
