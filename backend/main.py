#!/usr/bin/env python3
"""
Clean main application entry point for the coachiq backend.

This module provides a simplified FastAPI application setup with proper
initialization order to avoid metrics collisions and circular imports.
"""

import argparse
import logging
import platform
import signal
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from backend.api.router_config import configure_routers
from backend.core.config import get_settings
from backend.core.dependencies import (
    get_app_state,
    get_feature_manager_from_request,
)
from backend.core.logging_config import configure_unified_logging, setup_early_logging
from backend.core.metrics import initialize_backend_metrics
from backend.integrations.registration import register_custom_features
from backend.middleware.http import configure_cors
from backend.services.can_interface_service import CANInterfaceService
from backend.services.can_service import CANService
from backend.services.config_service import ConfigService
from backend.services.docs_service import DocsService
from backend.services.entity_service import EntityService
from backend.services.feature_manager import get_feature_manager
from backend.services.rvc_service import RVCService
from backend.services.vector_service import VectorService

# Set up early logging before anything else
setup_early_logging()

logger = logging.getLogger(__name__)

# Store startup time for health checks
SERVER_START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown logic for the FastAPI application,
    including service initialization and cleanup.
    """
    logger.info("Starting coachiq backend application")

    # Initialize backend metrics FIRST to avoid collisions
    initialize_backend_metrics()

    try:
        # Get application settings
        settings = get_settings()
        logger.info("Application settings loaded successfully")

        # Note: Unified logging is already configured in run_server.py
        # No need to reconfigure here to avoid overriding early setup

        # Initialize feature manager
        feature_manager = get_feature_manager()
        logger.info("Feature manager initialized")

        # Note: Features will be initialized from YAML configuration
        # This ensures proper dependency resolution with entity_manager → app_state
        logger.info("Features will be initialized from YAML configuration")

        # Start all enabled features (this will initialize entity_manager, app_state, websocket, etc.)
        await feature_manager.startup()
        logger.info("All features started successfully")

        # Get initialized features from feature manager
        app_state = feature_manager.get_feature("app_state")
        websocket_manager = feature_manager.get_feature("websocket")
        entity_manager_feature = feature_manager.get_feature("entity_manager")
        if not app_state or not websocket_manager or not entity_manager_feature:
            raise RuntimeError(
                "Required features (app_state, websocket, entity_manager) failed to initialize"
            )

        # Update logging configuration to include WebSocket handler now that manager is available
        from backend.core.logging_config import update_websocket_logging

        update_websocket_logging(websocket_manager)
        logger.info("WebSocket logging integration completed")

        # Initialize services with correct constructor signatures
        config_service = ConfigService(app_state)
        entity_service = EntityService(
            websocket_manager, entity_manager_feature.get_entity_manager()
        )
        can_service = CANService(app_state)
        rvc_service = RVCService(app_state)
        docs_service = DocsService()
        vector_service = VectorService() if settings.features.enable_vector_search else None
        can_interface_service = CANInterfaceService()
        logger.info("Backend services initialized")

        # Start CAN service with proper multi-interface initialization
        try:
            can_startup_result = await can_service.startup()
            logger.info(f"CAN service started: {can_startup_result}")
        except Exception as e:
            logger.error(f"Failed to start CAN service: {e}")
            logger.warning("CAN service will continue without proper initialization")

        # Register custom features with the feature manager
        register_custom_features()
        logger.info("Custom features registered")

        # Store services in app state for dependency injection
        app.state.app_state = app_state
        # --- Ensure global app_state is the same instance ---
        import backend.core.state as core_state

        core_state.app_state = app_state
        # ---------------------------------------------------
        app.state.feature_manager = feature_manager
        app.state.config_service = config_service
        app.state.entity_service = entity_service
        app.state.can_service = can_service
        app.state.rvc_service = rvc_service
        app.state.docs_service = docs_service
        app.state.vector_service = vector_service
        app.state.can_interface_service = can_interface_service

        logger.info("Backend services initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down coachiq backend application")

        # Shut down all enabled features
        if hasattr(app.state, "feature_manager"):
            await app.state.feature_manager.shutdown()

        logger.info("Backend services stopped")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    app = FastAPI(
        title="CoachIQ Backend",
        description="Modernized backend API for RV-C CANbus monitoring and control",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS middleware using settings
    configure_cors(app)

    # Configure and include routers
    configure_routers(app)

    return app


# Create the FastAPI application
app = create_app()


@app.get("/")
async def root():
    """Root endpoint for health checking."""
    return {"message": "CoachIQ Backend is running", "version": "2.0.0"}


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    app_state = get_app_state(request)
    return {
        "status": "healthy",
        "entities": len(app_state.entity_manager.get_entity_ids()),
        "services": "operational",
    }


@app.get(
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
        version_file = Path(__file__).parent.parent / "VERSION"
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


@app.get(
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


@app.get(
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


def main():
    """
    Main entry point for running the backend as a script.

    This function is used when the backend is run via the project scripts
    defined in pyproject.toml.
    """
    import os

    # Set up signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        raise KeyboardInterrupt()

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Get settings to use as CLI defaults
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Start the coachiq backend server.")
    parser.add_argument(
        "--host",
        type=str,
        default=settings.server.host,
        help=f"Host to bind the server (default: {settings.server.host})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.server.port,
        help=f"Port to bind the server (default: {settings.server.port})",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        default=os.getenv("COACHIQ_RELOAD", "false").lower() == "true",
        help="Enable auto-reload (development only, or COACHIQ_RELOAD=true)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=settings.logging.level.lower(),
        help=f"Uvicorn log level (default: {settings.logging.level.lower()})",
    )
    args = parser.parse_args()

    # Set up early logging before anything else
    setup_early_logging()

    # Get settings to potentially configure more comprehensive logging
    settings = get_settings()

    # Configure unified logging for standalone script execution
    log_config, root_logger = configure_unified_logging(settings.logging)

    logger.info("Starting coachiq backend server in standalone mode")

    # Get SSL configuration if available
    ssl_config = settings.get_uvicorn_ssl_config()

    # Build uvicorn run arguments
    uvicorn_args = {
        "app": "backend.main:app",
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "log_level": args.log_level,
        "log_config": log_config,
    }

    # Add reload directories to prevent PermissionError on protected directories
    if args.reload:
        # Use absolute path to backend directory to handle cases where working directory is /
        import os

        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uvicorn_args["reload_dirs"] = [os.path.join(backend_dir, "backend")]

    # Add SSL configuration if available
    uvicorn_args.update(ssl_config)

    # Log SSL status
    if ssl_config:
        logger.info("SSL/TLS enabled - server will run on HTTPS")
    else:
        logger.info("SSL/TLS not configured - server will run on HTTP")

    # Run the application using the top-level uvicorn import with unified log config
    uvicorn.run(**uvicorn_args)


if __name__ == "__main__":
    main()
