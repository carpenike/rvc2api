#!/usr/bin/env python3
"""
Clean main application entry point for the rvc2api backend.

This module provides a simplified FastAPI application setup with proper
initialization order to avoid metrics collisions and circular imports.
"""

import argparse
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request

from backend.api.router_config import configure_routers
from backend.core.config import get_settings
from backend.core.dependencies import get_app_state
from backend.core.logging_config import configure_unified_logging, setup_early_logging
from backend.core.metrics import initialize_backend_metrics
from backend.integrations.registration import register_custom_features
from backend.middleware.http import configure_cors
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown logic for the FastAPI application,
    including service initialization and cleanup.
    """
    logger.info("Starting rvc2api backend application")

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
        logger.info("Backend services initialized")

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

        logger.info("Backend services initialized successfully")

        yield

    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise
    finally:
        # Cleanup
        logger.info("Shutting down rvc2api backend application")

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
        title="RVC2API Backend",
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
    return {"message": "RVC2API Backend is running", "version": "2.0.0"}


@app.get("/health")
async def health_check(request: Request):
    """Health check endpoint."""
    app_state = get_app_state(request)
    return {
        "status": "healthy",
        "entities": len(app_state.entity_manager.get_entity_ids()),
        "services": "operational",
    }


def main():
    """
    Main entry point for running the backend as a script.

    This function is used when the backend is run via the project scripts
    defined in pyproject.toml.
    """
    import os

    # Get settings to use as CLI defaults
    settings = get_settings()

    parser = argparse.ArgumentParser(description="Start the rvc2api backend server.")
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
        action=(
            "store_true"
            if os.getenv("RVC2API_RELOAD", "false").lower() == "true"
            else "store_false"
        ),
        help="Enable auto-reload (development only, or RVC2API_RELOAD=true)",
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

    logger.info("Starting rvc2api backend server in standalone mode")

    # Run the application using the top-level uvicorn import with unified log config
    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
        log_config=log_config,
    )


if __name__ == "__main__":
    main()
