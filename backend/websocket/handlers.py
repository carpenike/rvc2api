"""
WebSocket manager feature for rvc2api.

This module implements a Feature-based WebSocket manager that handles:
- WebSocket client connection management
- Broadcasting updates to connected clients
- Log streaming via WebSockets
- CAN sniffer data streaming
- Network map updates streaming
- Feature status updates streaming
"""

import asyncio
import contextlib
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from backend.core.state import AppState
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class WebSocketManager(Feature):
    """
    Feature that manages WebSocket connections and broadcasting.

    Responsible for:
      - Client connection management
      - Broadcasting updates to connected clients
      - Providing endpoints for WebSocket connections
    """

    def __init__(
        self,
        name: str = "websocket",
        enabled: bool = True,
        core: bool = True,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        app_state: AppState | None = None,
    ) -> None:
        """
        Initialize the WebSocket manager feature.

        Args:
            name (str): Feature name (default: "websocket")
            enabled (bool): Whether the feature is enabled (default: True)
            core (bool): Whether this is a core feature (default: True)
            config (dict[str, Any] | None): Configuration options
            dependencies (list[str] | None): Feature dependencies
            app_state (AppState | None): Application state instance
        """
        # Ensure we depend on app_state
        deps = dependencies or []
        if "app_state" not in deps:
            deps.append("app_state")

        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config or {},
            dependencies=deps,
        )

        # Store reference to app_state
        self._app_state = app_state

        # WebSocket client sets
        self.data_clients: set[WebSocket] = set()  # Main data stream
        self.log_clients: set[WebSocket] = set()  # Log stream
        self.can_sniffer_clients: set[WebSocket] = set()  # CAN sniffer stream
        self.network_map_clients: set[WebSocket] = set()  # Network map updates
        self.features_clients: set[WebSocket] = set()  # Features status updates

        # For background task management
        self.background_tasks: set[asyncio.Task] = set()

    async def startup(self) -> None:
        """Initialize WebSocket handlers."""
        logger.info("Starting WebSocket manager")

        # If we have app_state, wire up the broadcast function
        if self._app_state:
            self._app_state.set_broadcast_function(self.broadcast_can_sniffer_group)

    async def shutdown(self) -> None:
        """Clean up WebSocket connections and background tasks."""
        logger.info("Shutting down WebSocket manager")

        # Cancel any background tasks
        for task in self.background_tasks:
            task.cancel()

        # Close all WebSocket connections
        for client_set in [
            self.data_clients,
            self.log_clients,
            self.can_sniffer_clients,
            self.network_map_clients,
            self.features_clients,
        ]:
            for client in list(client_set):
                with contextlib.suppress(Exception):
                    await client.close()
            client_set.clear()

    @property
    def health(self) -> str:
        """Return the health status of the feature."""
        if not self.enabled:
            return "disabled"
        return "healthy"

    # ── Broadcasting Functions ──────────────────────────────────────────────────

    async def broadcast_to_data_clients(self, data: dict[str, Any]) -> None:
        """
        Broadcast data to all connected data WebSocket clients.

        Args:
            data (dict[str, Any]): The data to broadcast as JSON
        """
        to_remove = set()
        for client in self.data_clients:
            try:
                await client.send_json(data)
            except Exception:
                to_remove.add(client)
        for client in to_remove:
            self.data_clients.discard(client)

    async def broadcast_json_to_clients(
        self, clients: set[WebSocket], data: dict[str, Any]
    ) -> None:
        """
        Broadcast JSON data to a specific set of WebSocket clients.

        Args:
            clients (set[WebSocket]): Set of WebSocket clients to broadcast to
            data (dict[str, Any]): The data to broadcast as JSON
        """
        to_remove = set()
        for client in clients:
            try:
                await client.send_json(data)
            except Exception:
                to_remove.add(client)
        for client in to_remove:
            clients.discard(client)

    async def broadcast_text_to_log_clients(self, text: str) -> None:
        """
        Broadcast text to all connected log WebSocket clients.

        Args:
            text (str): The text to broadcast
        """
        to_remove = set()
        for client in self.log_clients:
            try:
                await client.send_text(text)
            except Exception:
                to_remove.add(client)
        for client in to_remove:
            self.log_clients.discard(client)

    async def broadcast_can_sniffer_group(self, group: dict[str, Any]) -> None:
        """
        Broadcast a CAN sniffer group to all connected CAN sniffer clients.

        Args:
            group (dict[str, Any]): The CAN sniffer group to broadcast
        """
        await self.broadcast_json_to_clients(self.can_sniffer_clients, group)

    async def broadcast_network_map(self, network_map: dict[str, Any]) -> None:
        """
        Broadcast network map data to all connected network map clients.

        Args:
            network_map (dict[str, Any]): The network map data to broadcast
        """
        await self.broadcast_json_to_clients(self.network_map_clients, network_map)

    async def broadcast_features_status(self, features_status: list[dict[str, Any]]) -> None:
        """
        Broadcast features status to all connected features clients.

        Args:
            features_status (list[dict[str, Any]]): The features status data to broadcast
        """
        await self.broadcast_json_to_clients(self.features_clients, features_status)

    # ── WebSocket Endpoints ─────────────────────────────────────────────────────

    async def handle_data_connection(self, websocket: WebSocket) -> None:
        """
        Handle a new data WebSocket connection.

        Args:
            websocket (WebSocket): The WebSocket connection
        """
        await websocket.accept()
        self.data_clients.add(websocket)
        logger.info(
            f"Data WebSocket client connected: {websocket.client.host}:{websocket.client.port}"
        )
        try:
            while True:
                await asyncio.sleep(60)
        except WebSocketDisconnect:
            logger.info(
                f"Data WebSocket client disconnected: {websocket.client.host}:{websocket.client.port}"
            )
        except Exception as e:
            logger.error(
                f"Data WebSocket error for client {websocket.client.host}:{websocket.client.port}: {e}"
            )
        finally:
            self.data_clients.discard(websocket)

    async def handle_log_connection(self, websocket: WebSocket) -> None:
        """
        Handle a new log WebSocket connection.

        Args:
            websocket (WebSocket): The WebSocket connection
        """
        await websocket.accept()
        self.log_clients.add(websocket)
        logger.info(
            f"Log WebSocket client connected: {websocket.client.host}:{websocket.client.port}"
        )
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info(
                f"Log WebSocket client disconnected: {websocket.client.host}:{websocket.client.port}"
            )
        except Exception as e:
            logger.error(
                f"Log WebSocket error for client {websocket.client.host}:{websocket.client.port}: {e}"
            )
        finally:
            self.log_clients.discard(websocket)

    async def handle_can_sniffer_connection(self, websocket: WebSocket) -> None:
        """
        Handle a new CAN sniffer WebSocket connection.

        Args:
            websocket (WebSocket): The WebSocket connection
        """
        await websocket.accept()
        self.can_sniffer_clients.add(websocket)
        logger.info(
            f"CAN sniffer WebSocket client connected: {websocket.client.host}:{websocket.client.port}"
        )
        try:
            if self._app_state:
                for group in self._app_state.get_can_sniffer_grouped():
                    await websocket.send_json(group)
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info(
                f"CAN sniffer WebSocket client disconnected: {websocket.client.host}:{websocket.client.port}"
            )
        except Exception as e:
            logger.error(
                f"CAN sniffer WebSocket error for client {websocket.client.host}:{websocket.client.port}: {e}"
            )
        finally:
            self.can_sniffer_clients.discard(websocket)

    async def handle_network_map_connection(self, websocket: WebSocket) -> None:
        """
        Handle a new network map WebSocket connection.

        Args:
            websocket (WebSocket): The WebSocket connection
        """
        await websocket.accept()
        self.network_map_clients.add(websocket)
        logger.info(
            f"Network map WebSocket client connected: {websocket.client.host}:{websocket.client.port}"
        )
        try:
            network_map = {"devices": [], "source_addresses": []}
            await websocket.send_json(network_map)
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info(
                f"Network map WebSocket client disconnected: {websocket.client.host}:{websocket.client.port}"
            )
        except Exception as e:
            logger.error(
                f"Network map WebSocket error for client {websocket.client.host}:{websocket.client.port}: {e}"
            )
        finally:
            self.network_map_clients.discard(websocket)

    async def handle_features_status_connection(self, websocket: WebSocket) -> None:
        """
        Handle a new features status WebSocket connection.

        Args:
            websocket (WebSocket): The WebSocket connection
        """
        await websocket.accept()
        self.features_clients.add(websocket)
        logger.info(
            f"Features status WebSocket client connected: {websocket.client.host}:{websocket.client.port}"
        )
        try:
            features_status = []
            await websocket.send_json(features_status)
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            logger.info(
                f"Features status WebSocket client disconnected: {websocket.client.host}:{websocket.client.port}"
            )
        except Exception as e:
            logger.error(
                f"Features status WebSocket error for client {websocket.client.host}:{websocket.client.port}: {e}"
            )
        finally:
            self.features_clients.discard(websocket)


class WebSocketLogHandler(logging.Handler):
    """
    A custom logging handler that forwards log messages to WebSocket clients.

    This handler formats log records and sends them as text messages to all
    connected log WebSocket clients.
    """

    def __init__(
        self, websocket_manager: WebSocketManager, loop: asyncio.AbstractEventLoop | None = None
    ):
        """
        Initialize the WebSocket log handler.

        Args:
            websocket_manager (WebSocketManager): The WebSocket manager instance
            loop (asyncio.AbstractEventLoop | None): Optional event loop for asynchronous operations
        """
        super().__init__()
        self.websocket_manager = websocket_manager
        self.loop = loop or asyncio.get_event_loop()

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record to all connected log WebSocket clients.

        Args:
            record (logging.LogRecord): The log record to emit
        """
        try:
            log_entry = self.format(record)
            if self.loop and self.loop.is_running():
                coro = self.websocket_manager.broadcast_text_to_log_clients(log_entry)
                asyncio.run_coroutine_threadsafe(coro, self.loop)
        except Exception:
            self.handleError(record)


websocket_manager: WebSocketManager | None = None


def initialize_websocket_manager(
    app_state: AppState | None = None,
    feature_manager: Any | None = None,  # Type hint omitted to avoid circular import
    config: dict[str, Any] | None = None,
) -> WebSocketManager:
    """
    Initialize the WebSocket manager singleton.

    Args:
        app_state (AppState | None): The application state instance
        feature_manager (Any | None): The feature manager instance
        config (dict[str, Any] | None): Configuration dictionary

    Returns:
        WebSocketManager: The initialized WebSocketManager instance
    """
    global websocket_manager
    if websocket_manager is None:
        websocket_manager = WebSocketManager(
            name="websocket",
            enabled=True,
            core=True,
            config=config or {},
            dependencies=["app_state"],
            app_state=app_state,
        )
        if feature_manager:
            feature_manager.register_feature(websocket_manager)
    return websocket_manager


def get_websocket_manager() -> WebSocketManager:
    """
    Get the WebSocket manager singleton instance.

    Returns:
        WebSocketManager: The WebSocketManager instance

    Raises:
        RuntimeError: If the WebSocketManager has not been initialized
    """
    if websocket_manager is None:
        raise RuntimeError(
            "WebSocketManager not initialized. Call initialize_websocket_manager first."
        )
    return websocket_manager
