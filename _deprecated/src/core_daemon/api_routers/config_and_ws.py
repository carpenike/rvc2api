"""
Manages API routes for configuration and WebSocket interactions.

This module provides FastAPI endpoints for:
- Retrieving the current application configuration.
- Managing WebSocket connections for real-time updates (e.g., CAN messages, logs).
- Providing server and application status.
- Streaming application logs to WebSocket clients.
- Checking for the latest GitHub release (server-side cache).
"""

import asyncio
import json
import logging
import os
import time  # Added for uptime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from core_daemon import app_state, feature_manager
from core_daemon._version import VERSION  # Import VERSION
from core_daemon.config import ACTUAL_MAP_PATH, ACTUAL_SPEC_PATH, get_actual_paths
from core_daemon.models import GitHubUpdateStatus
from core_daemon.websocket import (
    can_sniffer_ws_endpoint,
    features_ws_endpoint,
    websocket_endpoint,
    websocket_logs_endpoint,
)

logger = logging.getLogger(__name__)

api_router_config_ws = APIRouter()  # Router for configuration, status, and WebSocket endpoints

# Get actual paths once for this module
actual_spec_path_for_ui, actual_map_path_for_ui = get_actual_paths()

# Store startup time
SERVER_START_TIME = time.time()


@api_router_config_ws.get("/healthz")
async def healthz():
    """Liveness probe with feature health aggregation."""
    features = feature_manager.get_enabled_features()
    health_report = {name: f.health for name, f in features.items()}
    # Consider healthy if all enabled features are healthy/unknown/disabled
    unhealthy = {
        name: status
        for name, status in health_report.items()
        if status not in ("healthy", "unknown", "disabled")
    }
    if unhealthy:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "unhealthy_features": unhealthy,
                "all_features": health_report,
            },
        )
    return JSONResponse(status_code=200, content={"status": "ok", "features": health_report})


@api_router_config_ws.get("/readyz")
async def readyz():
    """
    Readiness probe: 200 once at least one frame decoded, else 503.
    """
    ready = len(app_state.state) > 0
    code = 200 if ready else 503
    return JSONResponse(
        status_code=code,
        content={"status": "ready" if ready else "pending", "entities": len(app_state.state)},
    )


@api_router_config_ws.get("/metrics")
def metrics():
    """Prometheus metrics endpoint."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@api_router_config_ws.get("/config/device_mapping", response_class=PlainTextResponse)
async def get_device_mapping_config_content_api():
    if os.path.exists(actual_map_path_for_ui):
        try:
            with open(actual_map_path_for_ui) as f:
                return PlainTextResponse(f.read())
        except Exception as e:
            logger.error(
                f"API Error: Could not read device mapping from '{actual_map_path_for_ui}': {e}"
            )
            raise HTTPException(
                status_code=500, detail=f"Error reading device mapping file: {e!s}"
            ) from e
    else:
        logger.error(
            f"API Error: Device mapping file not found for UI display at '{actual_map_path_for_ui}'"
        )
        raise HTTPException(status_code=404, detail="Device mapping file not found.")


@api_router_config_ws.get("/config/rvc_spec_metadata")
async def get_rvc_spec_metadata():
    """Returns metadata (version and spec_document URL) from the rvc.json spec file."""
    if not os.path.exists(actual_spec_path_for_ui):
        logger.error(
            f"API Error: RVC spec file not found at '{actual_spec_path_for_ui}' "
            f"for metadata endpoint"
        )
        raise HTTPException(status_code=404, detail="RVC spec file not found.")
    try:
        with open(actual_spec_path_for_ui) as f:
            spec_data = json.load(f)
        return {
            "version": spec_data.get("version"),
            "spec_document": spec_data.get("spec_document"),
        }
    except json.JSONDecodeError:
        logger.error(f"API Error: Could not decode RVC spec from '{actual_spec_path_for_ui}'")
        raise HTTPException(status_code=500, detail="Error decoding RVC spec file.") from None
    except Exception as e:
        logger.error(f"API Error: Could not read RVC spec from '{actual_spec_path_for_ui}': {e}")
        raise HTTPException(status_code=500, detail=f"Error reading RVC spec file: {e!s}") from e


@api_router_config_ws.get("/config/rvc_spec", response_class=PlainTextResponse)
async def get_rvc_spec_config_content_api():
    if os.path.exists(actual_spec_path_for_ui):
        try:
            with open(actual_spec_path_for_ui) as f:
                return PlainTextResponse(f.read())
        except Exception as e:
            logger.error(
                f"API Error: Could not read RVC spec from '{actual_spec_path_for_ui}': {e}"
            )
            raise HTTPException(
                status_code=500, detail=f"Error reading RVC spec file: {e!s}"
            ) from e
    else:
        logger.error(
            f"API Error: RVC spec file not found for UI display at '{actual_spec_path_for_ui}'"
        )
        raise HTTPException(status_code=404, detail="RVC spec file not found.")


# --- New Status Endpoints ---
@api_router_config_ws.get("/status/server")
async def get_server_status():
    """Returns basic server status information."""
    uptime_seconds = time.time() - SERVER_START_TIME
    return {
        "status": "ok",
        "version": VERSION,
        "server_start_time_unix": SERVER_START_TIME,
        "uptime_seconds": uptime_seconds,
        "message": "rvc2api server is running.",
    }


@api_router_config_ws.get("/status/application")
async def get_application_status():
    """Returns application-specific status information."""
    # Check if config files were loaded (using the global ACTUAL_SPEC_PATH and ACTUAL_MAP_PATH)
    spec_loaded = ACTUAL_SPEC_PATH is not None and os.path.exists(ACTUAL_SPEC_PATH)
    map_loaded = ACTUAL_MAP_PATH is not None and os.path.exists(ACTUAL_MAP_PATH)

    # Basic check for CAN listeners (more detailed status could be added)
    # This is a placeholder; actual CAN listener status might need more complex state tracking.
    can_listeners_active = (
        len(app_state.state) > 0
    )  # Simple proxy: if entities exist, listeners likely ran

    return {
        "status": "ok",
        "rvc_spec_file_loaded": spec_loaded,
        "rvc_spec_file_path": ACTUAL_SPEC_PATH if spec_loaded else None,
        "device_mapping_file_loaded": map_loaded,
        "device_mapping_file_path": ACTUAL_MAP_PATH if map_loaded else None,
        "known_entity_count": len(app_state.entity_id_lookup),
        "active_entity_state_count": len(app_state.state),
        "unmapped_entry_count": len(app_state.unmapped_entries),
        "unknown_pgn_count": len(app_state.unknown_pgns),
        "can_listeners_status": "likely_active" if can_listeners_active else "unknown_or_inactive",
        "websocket_clients": {
            "data_clients": len(
                app_state.clients
            ),  # Assuming 'clients' is accessible or moved to app_state
            "log_clients": len(
                app_state.log_ws_clients
            ),  # Assuming 'log_ws_clients' is accessible or moved to app_state
        },
    }


@api_router_config_ws.get("/status/latest_release", response_model=GitHubUpdateStatus)
async def get_latest_github_release(request: Request):
    """
    Returns the latest GitHub release version and metadata as checked by the background task.

    Response example:
        {
            "latest_version": "0.2.0",
            "last_checked": 1715600000.0,
            "last_success": 1715600000.0,
            "error": null,
            "latest_release_info": {
                "tag_name": "v0.2.0",
                "name": "Release v0.2.0",
                "body": "Release notes...",
                "html_url": "https://github.com/owner/repo/releases/tag/v0.2.0",
                "published_at": "2025-05-13T12:00:00Z",
                "created_at": "2025-05-12T18:00:00Z",
                "assets": [
                    {"name": "asset.zip", "browser_download_url": "...", "size": 1234,
                    "download_count": 42}
                ],
                "tarball_url": "...",
                "zipball_url": "...",
                "prerelease": false,
                "draft": false,
                "author": {"login": "octocat", "html_url": "https://github.com/octocat"},
                "discussion_url": "..."
            }
        }
    """
    checker = request.app.state.update_checker
    # Use Pydantic model for serialization/validation
    return GitHubUpdateStatus.parse_obj(checker.get_status())


@api_router_config_ws.post("/status/force_update_check", response_model=GitHubUpdateStatus)
async def force_github_update_check(request: Request, background_tasks: BackgroundTasks):
    """
    Forces an immediate GitHub update check and returns the new status.
    This triggers the backend to fetch the latest release from GitHub now
    (not waiting for the next poll).
    """
    checker = request.app.state.update_checker
    await checker.force_check()
    return GitHubUpdateStatus.parse_obj(checker.get_status())


# --- End New Status Endpoints ---


@api_router_config_ws.websocket("/ws")
async def serve_websocket_endpoint(ws: WebSocket):
    """Handles WebSocket connections for general data streaming."""
    await websocket_endpoint(ws)


@api_router_config_ws.websocket("/ws/logs")
async def serve_websocket_logs_endpoint(ws: WebSocket):
    print("LOG WS HANDLER CALLED")  # Debug: confirm handler is hit
    await websocket_logs_endpoint(ws)


@api_router_config_ws.websocket("/ws/can-sniffer")
async def serve_can_sniffer_ws(ws: WebSocket):
    await can_sniffer_ws_endpoint(ws)


@api_router_config_ws.websocket("/ws/features")
async def serve_features_ws(ws: WebSocket):
    """WebSocket endpoint for live feature status updates."""
    await features_ws_endpoint(ws)


# --- WebSocket: Home Status Updates ---
@api_router_config_ws.websocket("/ws/status")
async def ws_status_updates(ws: WebSocket):
    """
    WebSocket endpoint that pushes combined status, health, and CAN status
    updates for the home view. Sends a JSON object with keys: server, application, can_status.
    """
    await ws.accept()
    send_task = None
    disconnect_event = asyncio.Event()

    async def send_status_periodically():
        try:
            while not disconnect_event.is_set():
                # Gather all three status payloads
                server = await get_server_status()
                application = await get_application_status()
                # CAN status is a GET endpoint in can.py, so import and call it
                from core_daemon.api_routers.can import get_can_status

                can_status = await get_can_status()
                # Compose and send
                await ws.send_json(
                    {
                        "server": server,
                        "application": application,
                        "can_status": can_status,
                    }
                )
                await asyncio.sleep(5)  # Adjustable interval
        except Exception as e:
            # Log and exit
            logger.info(f"/ws/status send loop ended: {e}")

    send_task = asyncio.create_task(send_status_periodically())
    try:
        while True:
            await ws.receive_text()  # Keep alive, ignore input
    except Exception:
        pass
    finally:
        disconnect_event.set()
        if send_task:
            await send_task
        logger.info("/ws/status client disconnected")
