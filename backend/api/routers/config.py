"""
Config and Status API Router

FastAPI router for configuration and status monitoring.
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

Note: WebSocket endpoints are handled by backend.websocket.routes
"""

import logging
import time
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
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
    # Note: status can be "healthy" or start with "healthy (" for descriptive info
    unhealthy = {
        name: status
        for name, status in health_report.items()
        if not (status in ("unknown", "disabled") or status.startswith("healthy"))
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
        "can_listeners_status": (
            "likely_active" if can_listeners_active else "unknown_or_inactive"
        ),
        "websocket_clients": {
            "data_clients": 0,  # Will be updated once WebSocket manager is properly integrated
            "log_clients": 0,
            "status_clients": 0,
            "features_clients": 0,
            "can_sniffer_clients": 0,
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


# Note: WebSocket endpoints have been moved to backend.websocket.routes
# The endpoints /ws, /ws/logs, /ws/can-sniffer, /ws/features, and /ws/status
# are now handled by the proper WebSocket manager with feature integration
