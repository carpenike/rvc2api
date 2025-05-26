"""
Config and Status API Router

FastAPI router for configuration, status monitoring, and WebSocket connections.
This router delegates business logic to appropriate services.

Routes:
- GET /config/device_mapping: Get device mapping configuration
- GET /config/spec: Get RV-C specification configuration
- GET /healthz: Liveness probe with feature health aggregation
- GET /readyz: Readiness probe for application startup
- GET /metrics: Prometheus metrics endpoint
- GET /status/server: Get server status information
- GET /status/application: Get application status information
- GET /status/latest_release: Get latest GitHub release information
- POST /status/force_update_check: Force GitHub update check
- WebSocket /ws: General data streaming
- WebSocket /ws/logs: Application log streaming
- WebSocket /ws/can-sniffer: CAN bus sniffer
- WebSocket /ws/features: Feature status updates
- WebSocket /ws/status: Combined status updates
"""

import asyncio
import logging
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, WebSocket
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.core.dependencies import (
    get_app_state,
    get_config_service,
    get_feature_manager_from_request,
    get_github_update_checker,
)
from backend.models.github_update import GitHubUpdateStatus

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/api", tags=["config", "status"])

# Store startup time
SERVER_START_TIME = time.time()

# WebSocket client sets
log_ws_clients: set[WebSocket] = set()
status_ws_clients: set[WebSocket] = set()
features_ws_clients: set[WebSocket] = set()
can_sniffer_ws_clients: set[WebSocket] = set()
data_ws_clients: set[WebSocket] = set()


@router.get(
    "/config/device_mapping",
    response_class=PlainTextResponse,
    summary="Get device mapping configuration",
    description="Returns the current device mapping configuration file content.",
)
async def get_device_mapping_config(request: Request) -> PlainTextResponse:
    """Get device mapping configuration content."""
    config_service = get_config_service(request)
    try:
        content = await config_service.get_device_mapping_content()
        return PlainTextResponse(content)
    except FileNotFoundError as e:
        logger.error(f"Device mapping file not found: {e}")
        raise HTTPException(status_code=404, detail="Device mapping file not found") from e
    except Exception as e:
        logger.error(f"Error reading device mapping file: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error reading device mapping file: {e}"
        ) from e


@router.get(
    "/config/spec",
    response_class=PlainTextResponse,
    summary="Get RV-C specification configuration",
    description="Returns the current RV-C specification file content.",
)
async def get_spec_config(request: Request) -> PlainTextResponse:
    """Get RV-C specification configuration content."""
    config_service = get_config_service(request)
    try:
        content = await config_service.get_spec_content()
        return PlainTextResponse(content)
    except FileNotFoundError as e:
        logger.error(f"Spec file not found: {e}")
        raise HTTPException(status_code=404, detail="RV-C specification file not found") from e
    except Exception as e:
        logger.error(f"Error reading spec file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading spec file: {e}") from e


@router.get(
    "/healthz",
    summary="Liveness probe",
    description="Returns health status with feature health aggregation. Returns 503 if any features are unhealthy.",
)
async def healthz(request: Request) -> JSONResponse:
    """Liveness probe with feature health aggregation."""
    feature_manager = get_feature_manager_from_request(request)
    features = feature_manager.features
    health_report = {name: f.health for name, f in features.items() if getattr(f, "enabled", False)}

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


@router.get(
    "/readyz",
    summary="Readiness probe",
    description="Returns 200 once at least one frame is decoded, else 503.",
)
async def readyz(request: Request) -> JSONResponse:
    """Readiness probe: 200 once at least one frame decoded, else 503."""
    app_state = get_app_state(request)
    ready = len(app_state.entity_manager.get_entity_ids()) > 0
    code = 200 if ready else 503

    return JSONResponse(
        status_code=code,
        content={
            "status": "ready" if ready else "pending",
            "entities": len(app_state.entity_manager.get_entity_ids()),
        },
    )


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Returns Prometheus-format metrics for monitoring.",
)
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@router.get(
    "/status/server",
    response_model=dict[str, Any],
    summary="Get server status",
    description="Returns basic server status information including uptime and version.",
)
async def get_server_status() -> dict[str, Any]:
    """Returns basic server status information."""
    uptime_seconds = time.time() - SERVER_START_TIME

    # Import VERSION here to avoid circular imports
    try:
        from backend.core.version import VERSION

        version = VERSION
    except ImportError:
        version = "unknown"

    return {
        "status": "ok",
        "version": version,
        "server_start_time_unix": SERVER_START_TIME,
        "uptime_seconds": uptime_seconds,
        "message": "rvc2api server is running.",
    }


@router.get(
    "/status/application",
    response_model=dict[str, Any],
    summary="Get application status",
    description="Returns application-specific status information including configuration and entity counts.",
)
async def get_application_status(request: Request) -> dict[str, Any]:
    """Returns application-specific status information."""
    config_service = get_config_service(request)
    app_state = get_app_state(request)

    # Get configuration status
    config_status = await config_service.get_config_status()

    # Basic check for CAN listeners (simple proxy: if entities exist, listeners likely ran)
    can_listeners_active = len(app_state.entity_manager.get_entity_ids()) > 0

    return {
        "status": "ok",
        "rvc_spec_file_loaded": config_status["spec_loaded"],
        "rvc_spec_file_path": config_status.get("spec_path"),
        "device_mapping_file_loaded": config_status["mapping_loaded"],
        "device_mapping_file_path": config_status.get("mapping_path"),
        "known_entity_count": len(app_state.entity_manager.get_entity_ids()),
        "active_entity_state_count": len(app_state.entity_manager.get_entity_ids()),
        "unmapped_entry_count": len(app_state.unmapped_entries),
        "unknown_pgn_count": len(app_state.unknown_pgns),
        "can_listeners_status": "likely_active" if can_listeners_active else "unknown_or_inactive",
        "websocket_clients": {
            "data_clients": len(data_ws_clients),
            "log_clients": len(log_ws_clients),
            "status_clients": len(status_ws_clients),
            "features_clients": len(features_ws_clients),
            "can_sniffer_clients": len(can_sniffer_ws_clients),
        },
    }


@router.get(
    "/status/latest_release",
    response_model=GitHubUpdateStatus,
    summary="Get latest GitHub release",
    description="Returns the latest GitHub release version and metadata.",
)
async def get_latest_github_release(request: Request) -> GitHubUpdateStatus:
    """Returns the latest GitHub release version and metadata."""
    update_checker = get_github_update_checker(request)
    status_data = update_checker.get_status()
    return GitHubUpdateStatus.parse_obj(status_data)


@router.post(
    "/status/force_update_check",
    response_model=GitHubUpdateStatus,
    summary="Force GitHub update check",
    description="Forces an immediate GitHub update check and returns the new status.",
)
async def force_github_update_check(
    request: Request, background_tasks: BackgroundTasks
) -> GitHubUpdateStatus:
    """Forces an immediate GitHub update check and returns the new status."""
    update_checker = get_github_update_checker(request)
    await update_checker.force_check()
    status_data = update_checker.get_status()
    return GitHubUpdateStatus.parse_obj(status_data)


@router.get(
    "/status/features",
    response_model=dict[str, Any],
    summary="Get feature status",
    description="Returns the current status of all features in the system.",
    response_description="Dictionary containing feature states and metadata",
)
async def get_feature_status(request: Request) -> dict[str, Any]:
    """
    Returns the current status of all features in the system.

    This endpoint provides information about enabled/disabled features,
    their health status, and configuration details.
    """
    feature_manager = get_feature_manager_from_request(request)

    all_features = feature_manager.get_all_features()
    enabled_features = feature_manager.get_enabled_features()
    core_features = feature_manager.get_core_features()
    optional_features = feature_manager.get_optional_features()

    # Build health report
    health_report = {}
    for name, feature in all_features.items():
        try:
            health_status = getattr(feature, "health", "unknown")
        except AttributeError:
            health_status = "unknown"
        health_report[name] = health_status

    return {
        "total_features": len(all_features),
        "enabled_count": len(enabled_features),
        "core_count": len(core_features),
        "optional_count": len(optional_features),
        "features": {
            name: {
                "enabled": name in enabled_features,
                "core": name in core_features,
                "health": health_report.get(name, "unknown"),
                "type": type(feature).__name__ if feature else "Unknown",
            }
            for name, feature in all_features.items()
        },
    }


# WebSocket endpoints
@router.websocket("/ws")
async def websocket_data_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for general data streaming."""
    await websocket.accept()
    data_ws_clients.add(websocket)

    try:
        while True:
            # Keep connection alive, actual data streaming handled by background tasks
            await websocket.receive_text()
    except Exception as e:
        logger.info(f"WebSocket client disconnected: {e}")
    finally:
        data_ws_clients.discard(websocket)


@router.websocket("/ws/logs")
async def websocket_logs_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming application logs."""
    await websocket.accept()
    log_ws_clients.add(websocket)

    try:
        while True:
            # Keep connection alive, actual log streaming handled by log handler
            await websocket.receive_text()
    except Exception as e:
        logger.info(f"Log WebSocket client disconnected: {e}")
    finally:
        log_ws_clients.discard(websocket)


@router.websocket("/ws/can-sniffer")
async def websocket_can_sniffer_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for CAN bus sniffing."""
    await websocket.accept()
    can_sniffer_ws_clients.add(websocket)

    try:
        while True:
            # Keep connection alive, actual CAN data handled by CAN manager
            await websocket.receive_text()
    except Exception as e:
        logger.info(f"CAN sniffer WebSocket client disconnected: {e}")
    finally:
        can_sniffer_ws_clients.discard(websocket)


@router.websocket("/ws/features")
async def websocket_features_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for live feature status updates."""
    await websocket.accept()
    features_ws_clients.add(websocket)

    try:
        while True:
            # Send feature status updates periodically
            # Use websocket's app instance to access app state
            feature_manager = get_feature_manager_from_request(websocket)
            features = feature_manager.features
            status_data = {
                name: f.health for name, f in features.items() if getattr(f, "enabled", False)
            }

            await websocket.send_json(
                {"type": "feature_status", "data": status_data, "timestamp": time.time()}
            )

            await asyncio.sleep(5)  # Update every 5 seconds
    except Exception as e:
        logger.info(f"Features WebSocket client disconnected: {e}")
    finally:
        features_ws_clients.discard(websocket)


@router.websocket("/ws/status")
async def websocket_status_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for combined status updates."""
    await websocket.accept()
    status_ws_clients.add(websocket)

    try:
        while True:
            # Gather all status information
            server_status = await get_server_status()

            # Build application status manually since we can't call the endpoint directly
            config_service = get_config_service(websocket)
            app_state = get_app_state(websocket)

            # Get configuration status
            config_status = await config_service.get_config_status()

            # Basic check for CAN listeners (simple proxy: if entities exist, listeners likely ran)
            can_listeners_active = len(app_state.entity_manager.get_entity_ids()) > 0

            application_status = {
                "status": "ok",
                "rvc_spec_file_loaded": config_status["spec_loaded"],
                "rvc_spec_file_path": config_status.get("spec_path"),
                "device_mapping_file_loaded": config_status["mapping_loaded"],
                "device_mapping_file_path": config_status.get("mapping_path"),
                "known_entity_count": len(app_state.entity_manager.get_entity_ids()),
                "active_entity_state_count": len(app_state.entity_manager.get_entity_ids()),
                "unmapped_entry_count": len(app_state.unmapped_entries),
                "unknown_pgn_count": len(app_state.unknown_pgns),
                "can_listeners_status": "likely_active"
                if can_listeners_active
                else "unknown_or_inactive",
                "websocket_clients": {
                    "data_clients": len(data_ws_clients),
                    "log_clients": len(log_ws_clients),
                    "status_clients": len(status_ws_clients),
                    "features_clients": len(features_ws_clients),
                    "can_sniffer_clients": len(can_sniffer_ws_clients),
                },
            }

            # Send combined status
            await websocket.send_json(
                {
                    "server": server_status,
                    "application": application_status,
                    "timestamp": time.time(),
                }
            )

            await asyncio.sleep(5)  # Update every 5 seconds
    except Exception as e:
        logger.info(f"Status WebSocket client disconnected: {e}")
    finally:
        status_ws_clients.discard(websocket)
