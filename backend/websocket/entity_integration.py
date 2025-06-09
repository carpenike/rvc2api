"""
Entity-WebSocket integration for CoachIQ.

This module connects entity state changes to the WebSocket system. When an entity's state is updated,
it broadcasts the update to all connected WebSocket clients and handles event-driven integration
between the event bus and WebSocket notifications.
"""

import logging
from typing import Any

from backend.core.state import AppState
from backend.websocket.handlers import get_websocket_manager

logger = logging.getLogger(__name__)


async def notify_entity_update(entity_id: str, payload: dict[str, Any]) -> None:
    """
    Notify WebSocket clients about an entity state update.

    This function:
      1. Broadcasts the entity update to data WebSocket clients
      2. Publishes an entity_state_updated event

    Args:
        entity_id (str): The ID of the updated entity.
        payload (dict[str, Any]): The updated entity payload.

    Example:
        >>> await notify_entity_update("light_123", {"state": "on", "brightness": 80})
    """
    try:
        ws_manager = get_websocket_manager()
        broadcast_data = {
            "type": "entity_update",
            "entity_id": entity_id,
            "data": payload,
        }
        await ws_manager.broadcast_to_data_clients(broadcast_data)
        logger.debug(f"Entity update for {entity_id} broadcasted to WebSocket clients")
    except Exception as exc:
        logger.error(f"Failed to notify entity update via WebSocket: {exc}")


def setup_entity_websocket_integration(app_state: AppState) -> None:
    """
    Set up integration between entity state updates and WebSockets.

    This is a placeholder for future integration between entity state and WebSocket broadcasting.

    Args:
        app_state (AppState): The application state instance.

    Example:
        >>> setup_entity_websocket_integration(app_state)
    """
    logger.info("Entity WebSocket integration set up (placeholder)")


# Legacy event handler - kept for potential future use
async def _handle_entity_state_updated(data: dict[str, Any]) -> None:
    """
    Handle entity state update events.

    Args:
        data (dict[str, Any]): Event data with entity information. Should include 'entity_id' and 'payload'.

    Example event data:
        {
            "entity_id": "light_123",
            "payload": {"state": "on", "brightness": 80}
        }
    """
    entity_id = data.get("entity_id")
    payload = data.get("payload")
    if entity_id and payload:
        await notify_entity_update(entity_id, payload)
    else:
        logger.warning(f"Malformed entity_state_updated event: {data}")
