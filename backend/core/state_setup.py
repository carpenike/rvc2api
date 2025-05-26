"""
State management registration and initialization module.

This module provides functions to register and initialize the AppState
feature with the FeatureManager, ensuring proper setup and integration
with the event system.
"""

import logging
from typing import Any

from backend.core.state import AppState, app_state, initialize_app_state
from backend.services.feature_manager import FeatureManager

logger = logging.getLogger(__name__)


def setup_app_state(
    feature_manager: FeatureManager,
    config: dict[str, Any] | None = None,
) -> AppState:
    """
    Set up the AppState feature and integrate with events system.

    This function:
    1. Initializes the app_state singleton
    2. Registers WebSocket broadcast functions
    3. Sets up event subscribers for state updates

    Args:
        feature_manager: The application's feature manager
        config: Optional configuration dictionary

    Returns:
        The initialized AppState instance
    """
    config = config or {}

    # Initialize the app_state singleton
    state_feature = initialize_app_state(feature_manager, config)

    # Setup WebSocket broadcast integration
    # This will be implemented once we migrate the WebSocket functionality

    logger.info("AppState feature initialized")

    return state_feature


async def _handle_entity_state_update(data: dict[str, Any]) -> None:
    """
    Handle entity state update events.

    This is called when an entity's state changes, and updates
    the AppState accordingly.

    Args:
        data: Event data with entity information
    """
    if not app_state:
        logger.warning("AppState not initialized, cannot handle entity state update")
        return

    entity_id = data.get("entity_id")
    payload = data.get("payload")

    if not entity_id or not payload:
        logger.warning("Invalid entity update data")
        return

    app_state.update_entity_state_and_history(entity_id, payload)
    logger.debug(f"Updated entity state for {entity_id}")


async def _handle_network_map_update(data: dict[str, Any]) -> None:
    """
    Handle network map update events.

    This is called when the network map changes (e.g., new source address observed).

    Args:
        data: Event data with network information
    """
    if not app_state:
        logger.warning("AppState not initialized, cannot handle network map update")
        return

    # The actual WebSocket notification will be handled in the WebSocket service
    app_state.notify_network_map_ws()
