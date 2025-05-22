"""
WebSocket setup module for rvc2api.

This module provides functions to set up and integrate WebSocket functionality with the FastAPI
application, including WebSocket routes, handlers, and the WebSocketManager feature.

Usage Example:
    >>> setup_websocket(app, feature_manager)
"""

import logging
from typing import Any

from fastapi import FastAPI

from backend.core.state import app_state
from backend.services.feature_manager import FeatureManager
from backend.websocket.handlers import (
    WebSocketLogHandler,
    WebSocketManager,
    initialize_websocket_manager,
)
from backend.websocket.routes import setup_websocket_routes

logger = logging.getLogger(__name__)


def setup_websocket(
    app: FastAPI,
    feature_manager: FeatureManager,
    config: dict[str, Any] | None = None,
) -> WebSocketManager:
    """
    Set up WebSocket functionality for the FastAPI application.

    This function:
      1. Initializes the WebSocketManager feature
      2. Sets up WebSocket routes
      3. Configures the WebSocketLogHandler

    Args:
        app (FastAPI): The FastAPI application instance.
        feature_manager (FeatureManager): The feature manager instance.
        config (dict[str, Any] | None): Optional configuration dictionary.

    Returns:
        WebSocketManager: The initialized WebSocketManager instance.

    Example:
        >>> ws_manager = setup_websocket(app, feature_manager)
    """
    ws_manager = initialize_websocket_manager(
        app_state=app_state,  # Use the global app_state singleton
        feature_manager=feature_manager,
        config=config or {},
    )
    setup_websocket_routes(app, app_state)
    WebSocketLogHandler(ws_manager)  # Attach log handler for WebSocket logs
    logger.info("WebSocket setup complete.")
    return ws_manager


def shutdown_websocket() -> None:
    """
    Clean up WebSocket resources.

    This function should be called when shutting down the application
    to ensure proper cleanup of WebSocket connections and resources.
    """
    logger.info("WebSocket shutdown complete")
