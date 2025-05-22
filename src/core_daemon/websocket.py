"""
Manages WebSocket communications for the rvc2api daemon.

This module provides:
- A custom logging handler (`WebSocketLogHandler`) to stream application logs
  to connected WebSocket clients.
- Functionality to broadcast data (typically entity updates) to another set of
  WebSocket clients.
- FastAPI WebSocket endpoint handlers for both data and log streaming.
- Management of active WebSocket client connections (now delegated to app_state).
- WebSocket endpoint and broadcast logic for live CAN Sniffer grouped events.
"""

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

# Import client sets from app_state
from core_daemon.app_state import clients, log_ws_clients

logger = logging.getLogger(__name__)


# ── Log WebSocket Handler ──────────────────────────────────────────────────
class WebSocketLogHandler(logging.Handler):
    """
    A custom logging.Handler subclass that formats log records and sends them
    as text messages to all connected log WebSocket clients.

    It uses an asyncio event loop to send messages asynchronously and thread-safely.
    If sending a message to a client fails, that client is removed from the set.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__()
        self.loop = loop

    def _handle_callback_result(self, fut: asyncio.Future, client: WebSocket) -> None:
        """Handle the result of an asynchronous send operation."""
        try:
            fut.result()
        except Exception:
            log_ws_clients.discard(client)

    def emit(self, record):
        log_entry = self.format(record)
        for ws_client in list(log_ws_clients):
            try:
                if self.loop and self.loop.is_running():
                    coro = ws_client.send_text(log_entry)
                    fut = asyncio.run_coroutine_threadsafe(coro, self.loop)

                    # Create a callback function with the client captured in closure
                    def create_callback(client):
                        def callback(future):
                            self._handle_callback_result(future, client)

                        return callback

                    fut.add_done_callback(create_callback(ws_client))
            except Exception:
                log_ws_clients.discard(ws_client)


# ── Broadcasting ────────────────────────────────────────────────────────────
async def broadcast_to_clients(text: str):
    """
    Asynchronously broadcasts a text message to all currently connected data WebSocket clients.

    Iterates over a copy of the active clients set for safe removal if a send operation fails.
    Metrics for WebSocket messages and client counts are assumed to be handled elsewhere
    (e.g., in the calling code or via a shared metrics module if directly used here).

    Args:
        text: The string message to send (typically a JSON payload).
    """
    # This function will need WS_MESSAGES and WS_CLIENTS if they are to be updated here.
    # For now, assuming they are handled by the caller or a shared metrics module.
    # from .metrics import WS_MESSAGES, WS_CLIENTS # Example if metrics were used directly

    active_clients = list(clients)  # Create a copy for safe iteration
    for ws in active_clients:
        try:
            await ws.send_text(text)
            # WS_MESSAGES.inc() # Increment if metrics are handled here
        except Exception:
            clients.discard(ws)  # Remove client if send fails
    # WS_CLIENTS.set(len(clients)) # Update count if metrics are handled here


# ── WebSocket Endpoints ────────────────────────────────────────────────────
async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket endpoint: push every new payload as JSON.
    Keeps the connection alive even if the client sends nothing.
    """
    await ws.accept()
    clients.add(ws)
    logger.info(f"WebSocket client connected: {ws.client.host}:{ws.client.port}")
    try:
        while True:
            await asyncio.sleep(60)  # Keep connection alive, no need for client to send
    except WebSocketDisconnect as e:
        clients.discard(ws)
        logger.info(
            f"WebSocket client disconnected: {ws.client.host}:{ws.client.port} "
            f"(code={getattr(e, 'code', None)}, reason={getattr(e, 'reason', None)})"
        )
    except Exception as e:
        clients.discard(ws)
        logger.error(
            f"WebSocket error for client {ws.client.host}:{ws.client.port}: {e}", exc_info=True
        )


async def websocket_logs_endpoint(ws: WebSocket):
    """
    WebSocket endpoint: stream all log messages in real time.
    """
    await ws.accept()
    log_ws_clients.add(ws)
    logger.info(f"Log WebSocket client connected: {ws.client.host}:{ws.client.port}")
    try:
        while True:
            await ws.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        log_ws_clients.discard(ws)
        logger.info(f"Log WebSocket client disconnected: {ws.client.host}:{ws.client.port}")
    except Exception as e:
        log_ws_clients.discard(ws)
        logger.error(f"Log WebSocket error for client {ws.client.host}:{ws.client.port}: {e}")


# ── CAN Sniffer WebSocket State and Endpoint ────────────────────────────────
can_sniffer_ws_clients = set()


async def can_sniffer_ws_endpoint(ws: WebSocket):
    """
    WebSocket endpoint for live CAN Sniffer grouped events.
    On connect, sends all current groupings, then streams new groupings as they occur.
    """
    await ws.accept()
    can_sniffer_ws_clients.add(ws)
    try:
        from core_daemon.app_state import get_can_sniffer_grouped

        # On connect, send the current grouped sniffer log
        for group in get_can_sniffer_grouped():
            await ws.send_json(group)
        while True:
            await ws.receive_text()  # Keep the connection open
    except WebSocketDisconnect:
        logger.info(f"CAN Sniffer WebSocket client disconnected: {ws.client.host}:{ws.client.port}")
    except Exception as e:
        client_info = f"{ws.client.host}:{ws.client.port}"
        logger.error(f"CAN Sniffer WebSocket error for client {client_info}: {e}")
    finally:
        can_sniffer_ws_clients.discard(ws)


async def broadcast_can_sniffer_group(group):
    """
    Broadcast a new CAN sniffer grouping to all connected WebSocket clients.
    Removes clients that have disconnected or errored.
    Args:
        group (dict): The grouped command/response event to broadcast.
    """
    to_remove = set()
    for ws in can_sniffer_ws_clients:
        try:
            await ws.send_json(group)
        except Exception:
            to_remove.add(ws)
    for ws in to_remove:
        can_sniffer_ws_clients.discard(ws)


# ── CAN Network Map WebSocket State and Endpoint ────────────────────────────────
network_map_ws_clients: set[WebSocket] = set()


async def broadcast_network_map():
    from core_daemon.api_routers.can import get_network_map

    # Get the same payload as the HTTP endpoint
    payload = await get_network_map()
    to_remove = set()
    for ws in network_map_ws_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            to_remove.add(ws)
    for ws in to_remove:
        network_map_ws_clients.discard(ws)


async def network_map_ws_endpoint(ws: WebSocket):
    await ws.accept()
    network_map_ws_clients.add(ws)
    try:
        from core_daemon.api_routers.can import get_network_map

        # On connect, send the current full network map
        payload = await get_network_map()
        await ws.send_json(payload)
        while True:
            await ws.receive_text()  # Keep the connection open
    except WebSocketDisconnect:
        logger.info(f"Network Map WebSocket client disconnected: {ws.client.host}:{ws.client.port}")
    except Exception as e:
        client_info = f"{ws.client.host}:{ws.client.port}"
        logger.error(f"Network Map WebSocket error for client {client_info}: {e}")
    finally:
        network_map_ws_clients.discard(ws)


# ── Features WebSocket State and Endpoint ────────────────────────────────
features_ws_clients: set[WebSocket] = set()


async def broadcast_features_status():
    from core_daemon.feature_manager import get_all_features

    features = get_all_features()
    payload = [
        {
            "name": f.name,
            "enabled": f.enabled,
            "core": f.core,
            "config": f.config,
            "health": f.health,  # Add health status
        }
        for f in features.values()
    ]
    to_remove = set()
    for ws in features_ws_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            to_remove.add(ws)
    for ws in to_remove:
        features_ws_clients.discard(ws)


async def features_ws_endpoint(ws: WebSocket):
    await ws.accept()
    features_ws_clients.add(ws)
    try:
        from core_daemon.feature_manager import get_all_features

        features = get_all_features()
        payload = [
            {
                "name": f.name,
                "enabled": f.enabled,
                "core": f.core,
                "config": f.config,
                "health": f.health,  # Add health status
            }
            for f in features.values()
        ]
        await ws.send_json(payload)
        while True:
            await ws.receive_text()  # Keep the connection open
    except WebSocketDisconnect:
        logger.info(f"Features WebSocket client disconnected: {ws.client.host}:{ws.client.port}")
    except Exception as e:
        client_info = f"{ws.client.host}:{ws.client.port}"
        logger.error(f"Features WebSocket error for client {client_info}: {e}")
    finally:
        features_ws_clients.discard(ws)
