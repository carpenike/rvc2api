#!/usr/bin/env python3
"""
Main entry point and central orchestrator for the rvc2api daemon.

This script initializes and runs the FastAPI application that bridges RV-C (Recreational
Vehicle Controller Area Network) messages to a modern web API and WebSocket interface.

Key responsibilities include:
- Configuring application-wide logging.
- Loading RV-C specification and device mapping configurations.
- Initializing and managing shared application state (see app_state.py).
- Setting up and starting CAN bus listeners to receive RV-C messages (see can_manager.py).
- Starting a CAN bus writer task to send commands to the RV-C bus.
- Processing incoming CAN messages, decoding them, and updating entity states
  (see can_processing.py).
- Initializing the FastAPI application, including:
    - Setting up Prometheus metrics middleware.
    - Registering API routers for various functionalities
      (entities, CAN control, config, WebSockets).
    - Defining startup and shutdown event handlers.
- Providing a command-line interface to start the Uvicorn server.
"""

import asyncio
import functools
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from rvc_decoder import decode_payload, load_config_data

# Import application state variables and initialization function
from core_daemon import app_state  # Import the module itself

# Import the API routers
from core_daemon.api_routers import (
    api_router_can,
    api_router_config_ws,
    api_router_docs,
    api_router_entities,
)
from core_daemon.app_state import initialize_app_from_config

# Import CAN components from can_manager
from core_daemon.can_manager import initialize_can_listeners, initialize_can_writer_task

# Import the CAN processing function
from core_daemon.can_processing import process_can_message
from core_daemon.config import (
    configure_logger,
    get_actual_paths,
    get_canbus_config,
    get_fastapi_config,
    get_static_paths,
)

# Import the feature manager
from core_daemon.feature_manager import shutdown_all as feature_shutdown_all
from core_daemon.feature_manager import startup_all as feature_startup_all

# Import the GitHub update checker
from core_daemon.github_update_checker import update_checker

# Import the middleware
from core_daemon.middleware import configure_cors, prometheus_http_middleware
from core_daemon.websocket import WebSocketLogHandler

# ── Logging ──────────────────────────────────────────────────────────────────
logger = configure_logger()

logger.info("rvc2api starting up...")

# ── Determine actual config paths for core logic and UI display ────────────────
actual_spec_path_for_ui, actual_map_path_for_ui = get_actual_paths()

# ── Load spec & mappings for core logic ──────────────────────────────────────
logger.info(
    "Core logic attempting to load CAN spec from: %s, mapping from: %s",
    os.getenv("CAN_SPEC_PATH") or "(default)",
    os.getenv("CAN_MAP_PATH") or "(default)",
)
# Load all configuration data into a tuple
config_data_tuple = load_config_data(
    rvc_spec_path_override=os.getenv("CAN_SPEC_PATH"),
    device_mapping_path_override=os.getenv("CAN_MAP_PATH"),
)

# Initialize application state using the loaded configuration data
# and the decode_payload function from rvc_decoder
initialize_app_from_config(config_data_tuple, decode_payload)


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    # ── FastAPI setup ──────────────────────────────────────────────────────────
    fastapi_config = get_fastapi_config()
    api_title = fastapi_config["title"]
    api_server_description = fastapi_config["server_description"]
    api_root_path = fastapi_config["root_path"]

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        """
        Manage the lifespan of the FastAPI application.

        Handles startup and shutdown events for the application.

        Args:
            app: The FastAPI application instance

        Yields:
            None: Control is yielded to the application during its lifecycle
        """
        # --- Startup ---
        initialize_can_writer_task()
        try:
            main_loop = asyncio.get_running_loop()
            log_ws_handler = WebSocketLogHandler(loop=main_loop)
            log_ws_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            log_ws_handler.setFormatter(formatter)
            logging.getLogger().addHandler(log_ws_handler)
            logger.info("WebSocketLogHandler initialized and added to the root logger.")
        except Exception as e:
            logger.error(f"Failed to setup WebSocket logging: {e}", exc_info=True)

        # Start GitHub update checker
        await update_checker.start()
        app.state.update_checker = update_checker

        # Check vector service status
        from core_daemon.services.vector_service import get_vector_service

        vector_service = get_vector_service()
        if vector_service.is_available():
            logger.info("FAISS vector search service initialized successfully")
        else:
            status = vector_service.get_status()
            logger.warning(
                "FAISS vector search service is not available: %s. "
                "Documentation search will be disabled. "
                "Run 'python scripts/setup_faiss.py --setup' to configure.",
                status.get("error", "Unknown error"),
            )

        loop = asyncio.get_running_loop()
        canbus_config = get_canbus_config()
        interfaces = canbus_config["channels"]
        bustype = canbus_config["bustype"]
        bitrate = canbus_config["bitrate"]
        message_handler_with_args = functools.partial(
            process_can_message,
            loop=loop,
            decoder_map=app_state.decoder_map,
            device_lookup=app_state.device_lookup,
            status_lookup=app_state.status_lookup,
            pgn_hex_to_name_map=app_state.pgn_hex_to_name_map,
            raw_device_mapping=app_state.raw_device_mapping,
        )
        initialize_can_listeners(
            interfaces=interfaces,
            bustype=bustype,
            bitrate=bitrate,
            message_handler_callback=message_handler_with_args,
            logger_instance=logger,
        )
        await feature_startup_all()
        yield
        # --- Shutdown ---
        await feature_shutdown_all()
        logger.info("rvc2api shutting down...")

    app = FastAPI(
        title=api_title,
        servers=[{"url": "/", "description": api_server_description}],
        root_path=api_root_path,
        lifespan=lifespan,
    )

    # ── Add CORS middleware (see core_daemon/middleware.py for details) ──
    configure_cors(app)

    # ── Static files for API documentation ───────────────────────────────────────────
    static_paths = get_static_paths()
    static_dir = static_paths["static_dir"]

    # Ensure the static directory exists
    os.makedirs(static_dir, exist_ok=True)

    if os.path.isdir(static_dir):
        app.mount(
            "/static",
            StaticFiles(
                directory=static_dir,
                follow_symlink=True,
            ),
            name="static",
        )
        logger.info(f"Successfully mounted /static to directory: {static_dir}")
    else:
        logger.warning(
            f"Static directory ('{static_dir}') is invalid or not found; "
            f"static files will not be served."
        )

    # ── Middleware ─────────────────────────────────────────────────────────────
    @app.middleware("http")
    async def prometheus_middleware_handler(request: Any, call_next: Any) -> Any:
        """
        Prometheus metrics middleware for HTTP requests.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler

        Returns:
            The HTTP response with metrics recorded
        """
        return await prometheus_http_middleware(request, call_next)

    # ── Exception Handlers ─────────────────────────────────────────────────────
    @app.exception_handler(ResponseValidationError)
    async def validation_exception_handler(
        request: Any, exc: ResponseValidationError
    ) -> PlainTextResponse:
        """
        Handles response validation errors with a plain text message.

        Args:
            request: The incoming HTTP request
            exc: The validation error

        Returns:
            PlainTextResponse: A plain text response with the error message
        """
        return PlainTextResponse(f"Validation error: {exc}", status_code=500)

    # ── API Health Check Route ─────────────────────────────────────────────────────
    @app.get("/api/health")
    async def api_health() -> JSONResponse:
        """
        Health check endpoint for API monitoring.

        Returns:
            JSONResponse: A JSON response indicating the API is running
        """
        return JSONResponse({"status": "ok"}, status_code=200)

    # ── API Routers ────────────────────────────────────────────────────────────
    app.include_router(api_router_can, prefix="/api")
    app.include_router(api_router_config_ws, prefix="/api")
    app.include_router(api_router_docs, prefix="")  # /api/docs is handled in the router prefix
    app.include_router(api_router_entities, prefix="/api")

    return app


app = create_app()


# ── Entrypoint ─────────────────────────────────────────────────────────────
def main() -> None:
    """
    Main function to run the Uvicorn server for the rvc2api application.

    Retrieves host, port, and log level from environment variables or defaults,
    then starts the Uvicorn server.
    """
    host = os.getenv("RVC2API_HOST", "0.0.0.0")
    port = int(os.getenv("RVC2API_PORT", "8000"))
    log_level = os.getenv("RVC2API_LOG_LEVEL", "info").lower()

    logger.info(f"Starting Uvicorn server on {host}:{port} with log level '{log_level}'")
    uvicorn.run("core_daemon.main:app", host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    # When running the script directly, adjust PYTHONPATH to ensure proper module resolution
    import sys
    from pathlib import Path

    # Add the src directory to the path
    src_dir = str(Path(__file__).parent.parent.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    main()
