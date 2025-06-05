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
from datetime import UTC, datetime
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
    logger.info("GET /config/device_mapping - Retrieving device mapping configuration")
    config_service = get_config_service(request)
    try:
        content = await config_service.get_device_mapping_content()
        logger.info(
            f"Device mapping configuration retrieved successfully - {len(content)} characters"
        )
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
    logger.info("GET /config/spec - Retrieving RV-C specification configuration")
    config_service = get_config_service(request)
    try:
        content = await config_service.get_spec_content()
        logger.info(
            f"RV-C specification configuration retrieved successfully - {len(content)} characters"
        )
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
    description="Returns IETF-compliant health status with feature health aggregation. Returns 503 if any features are unhealthy. Add ?details=true for comprehensive diagnostic information.",
)
async def healthz(request: Request, details: bool = False) -> Response:
    """
    IETF-compliant liveness probe with feature health aggregation.

    Returns health status using industry-standard nomenclature and format following
    IETF draft "Health Check Response Format for HTTP APIs".

    Status values:
    - healthy: All systems operational
    - degraded: Some issues but service still functional
    - failed: Critical issues requiring attention
    """
    logger.debug(f"GET /healthz - Health check requested with details={details}")
    import json
    import os
    import platform
    import time
    from pathlib import Path

    start_time = time.time()
    feature_manager = get_feature_manager_from_request(request)
    features = feature_manager.features
    health_report = {name: f.health for name, f in features.items() if getattr(f, "enabled", False)}

    # Determine overall status using industry standards
    failed_features = {name: status for name, status in health_report.items() if status == "failed"}
    degraded_features = {
        name: status for name, status in health_report.items() if status == "degraded"
    }

    # Overall status logic: failed if any failed, degraded if any degraded, else healthy
    if failed_features:
        overall_status = "failed"
    elif degraded_features:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    # Log health status
    if failed_features:
        logger.warning(
            f"Health check shows FAILED status - failed features: {list(failed_features.keys())}"
        )
    elif degraded_features:
        logger.warning(
            f"Health check shows DEGRADED status - degraded features: {list(degraded_features.keys())}"
        )
    else:
        logger.debug("Health check shows HEALTHY status - all features operational")

    # Get service version from VERSION file if available
    version = "unknown"
    try:
        version_file = Path(__file__).parent.parent.parent.parent / "VERSION"
        if version_file.exists():
            version = version_file.read_text().strip()
        else:
            version = os.getenv("VERSION", "development")
    except Exception:
        version = "unknown"

    # IETF-compliant response structure
    response_data = {
        "status": overall_status,
        "version": "1",  # Health check format version
        "releaseId": version,
        "serviceId": "rvc2api",
        "description": _get_status_description(overall_status, failed_features, degraded_features),
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {name: {"status": status} for name, status in health_report.items()},
        # Backward compatibility for frontend
        "features": health_report,
        "response_time_ms": round((time.time() - start_time) * 1000, 2),
    }

    # Add service metadata
    response_data["service"] = {
        "name": "rvc2api",
        "version": version,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "hostname": platform.node(),
        "platform": platform.system(),
    }

    # Add problematic features info
    if failed_features or degraded_features:
        response_data["issues"] = {}
        if failed_features:
            response_data["issues"]["failed"] = list(failed_features.keys())
        if degraded_features:
            response_data["issues"]["degraded"] = list(degraded_features.keys())

    # Add detailed diagnostics if requested
    if details:
        feature_details = {}
        for name, feature in features.items():
            if getattr(feature, "enabled", False) and hasattr(feature, "health_details"):
                feature_details[name] = feature.health_details

        if feature_details:
            response_data["details"] = feature_details

        # Add system diagnostics
        response_data["diagnostics"] = {
            "active_features": len([f for f in features.values() if getattr(f, "enabled", False)]),
            "total_features": len(features),
            "python_version": platform.python_version(),
            "uptime_seconds": round(time.time() - SERVER_START_TIME, 2),
        }

    # Use proper HTTP status codes and IETF content type
    status_code = 503 if overall_status == "failed" else 200
    response_time_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"Health check completed - status: {overall_status}, "
        f"features_checked: {len(health_report)}, "
        f"response_time: {response_time_ms}ms, "
        f"status_code: {status_code}"
    )

    return Response(
        content=json.dumps(response_data),
        status_code=status_code,
        media_type="application/health+json",
        headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
    )


def _get_status_description(status: str, failed_features: dict, degraded_features: dict) -> str:
    """Generate human-readable status description."""
    if status == "failed":
        return f"Service critical: {len(failed_features)} feature(s) failed"
    elif status == "degraded":
        desc_parts = []
        if failed_features:
            desc_parts.append(f"{len(failed_features)} failed")
        if degraded_features:
            desc_parts.append(f"{len(degraded_features)} degraded")
        return f"Service degraded: {', '.join(desc_parts)} feature(s)"
    else:
        return "All systems operational"


@router.get(
    "/readyz",
    summary="Readiness probe",
    description="Returns 200 once at least one frame is decoded, else 503.",
)
async def readyz(request: Request) -> JSONResponse:
    """Readiness probe: 200 once at least one frame decoded, else 503."""
    logger.debug("GET /readyz - Readiness check requested")
    app_state = get_app_state(request)
    entity_count = len(app_state.entity_manager.get_entity_ids())
    ready = entity_count > 0
    code = 200 if ready else 503

    if ready:
        logger.debug(f"Readiness check passed - {entity_count} entities available")
    else:
        logger.warning("Readiness check failed - no entities decoded yet")

    return JSONResponse(
        status_code=code,
        content={
            "status": "ready" if ready else "pending",
            "entities": entity_count,
        },
    )


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="Returns Prometheus-format metrics for monitoring.",
)
def metrics() -> Response:
    """Prometheus metrics endpoint."""
    logger.debug("GET /metrics - Prometheus metrics requested")
    data = generate_latest()
    logger.debug(f"Prometheus metrics generated - {len(data)} bytes")
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


@router.get(
    "/status/server",
    response_model=dict[str, Any],
    summary="Get server status",
    description="Returns basic server status information including uptime and version.",
)
async def get_server_status() -> dict[str, Any]:
    """Returns basic server status information."""
    logger.debug("GET /status/server - Server status requested")
    uptime_seconds = time.time() - SERVER_START_TIME

    # Import VERSION here to avoid circular imports
    try:
        from backend.core.version import VERSION

        version = VERSION
    except ImportError:
        version = "unknown"

    status_data = {
        "status": "ok",
        "version": version,
        "server_start_time_unix": SERVER_START_TIME,
        "uptime_seconds": uptime_seconds,
        "message": "rvc2api server is running.",
    }

    logger.info(f"Server status retrieved - uptime: {uptime_seconds:.1f}s, version: {version}")
    return status_data


@router.get(
    "/status/application",
    response_model=dict[str, Any],
    summary="Get application status",
    description="Returns application-specific status information including configuration and entity counts.",
)
async def get_application_status(request: Request) -> dict[str, Any]:
    """Returns application-specific status information."""
    logger.debug("GET /status/application - Application status requested")
    config_service = get_config_service(request)
    app_state = get_app_state(request)

    # Get configuration status
    config_status = await config_service.get_config_status()

    # Basic check for CAN listeners (simple proxy: if entities exist, listeners likely ran)
    entity_count = len(app_state.entity_manager.get_entity_ids())
    can_listeners_active = entity_count > 0

    status_data = {
        "status": "ok",
        "rvc_spec_file_loaded": config_status["spec_loaded"],
        "rvc_spec_file_path": config_status.get("spec_path"),
        "device_mapping_file_loaded": config_status["mapping_loaded"],
        "device_mapping_file_path": config_status.get("mapping_path"),
        "known_entity_count": entity_count,
        "active_entity_state_count": entity_count,
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

    logger.info(
        f"Application status retrieved - entities: {entity_count}, "
        f"unmapped: {len(app_state.unmapped_entries)}, "
        f"unknown_pgns: {len(app_state.unknown_pgns)}, "
        f"spec_loaded: {config_status['spec_loaded']}, "
        f"mapping_loaded: {config_status['mapping_loaded']}"
    )

    return status_data


@router.get(
    "/status/latest_release",
    response_model=GitHubUpdateStatus,
    summary="Get latest GitHub release",
    description="Returns the latest GitHub release version and metadata.",
)
async def get_latest_github_release(request: Request) -> GitHubUpdateStatus:
    """Returns the latest GitHub release version and metadata."""
    logger.debug("GET /status/latest_release - GitHub release status requested")
    update_checker = get_github_update_checker(request)
    status_data = update_checker.get_status()

    logger.info(
        f"GitHub release status retrieved - current: {status_data.get('current_version')}, "
        f"latest: {status_data.get('latest_version')}, "
        f"update_available: {status_data.get('update_available')}"
    )

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
    logger.info("POST /status/force_update_check - Forcing GitHub update check")
    update_checker = get_github_update_checker(request)

    try:
        await update_checker.force_check()
        status_data = update_checker.get_status()

        logger.info(
            f"GitHub update check completed - current: {status_data.get('current_version')}, "
            f"latest: {status_data.get('latest_version')}, "
            f"update_available: {status_data.get('update_available')}"
        )

        return GitHubUpdateStatus.parse_obj(status_data)
    except Exception as e:
        logger.error(f"Failed to force GitHub update check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check for updates: {e}") from e


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
    logger.debug("GET /status/features - Feature status requested")
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

    feature_status = {
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

    logger.info(
        f"Feature status retrieved - total: {len(all_features)}, "
        f"enabled: {len(enabled_features)}, "
        f"core: {len(core_features)}, "
        f"optional: {len(optional_features)}"
    )

    return feature_status


# Note: WebSocket endpoints have been moved to backend.websocket.routes
# The endpoints /ws, /ws/logs, /ws/can-sniffer, /ws/features, and /ws/status
# are now handled by the proper WebSocket manager with feature integration
