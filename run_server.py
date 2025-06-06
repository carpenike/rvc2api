#!/usr/bin/env python3
"""
Entry point to run the rvc2api backend server.

This script runs the modernized backend using the new FastAPI application
structure with proper service-oriented architecture and centralized configuration.
"""

import argparse
import logging
import sys

import uvicorn
from dotenv import load_dotenv

from backend.core.config import get_settings
from backend.core.logging_config import configure_unified_logging, setup_early_logging

# Load environment variables from .env if present
load_dotenv()


def create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(description="Run the rvc2api backend server.")

    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind (overrides configuration)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind (overrides configuration)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload (overrides configuration)",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload (overrides configuration)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (overrides configuration)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        help="Number of worker processes (overrides configuration)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["critical", "error", "warning", "info", "debug", "trace"],
        help="Uvicorn log level (overrides configuration)",
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Show current configuration and exit",
    )

    return parser


def override_settings_from_args(settings, args):
    """Override settings with command line arguments if provided."""
    # Create a copy of server settings to modify
    server_config = settings.server.model_copy()

    if args.host is not None:
        server_config.host = args.host
    if args.port is not None:
        server_config.port = args.port
    if args.reload:
        server_config.reload = True
    if args.no_reload:
        server_config.reload = False
    if args.debug:
        server_config.debug = True
    if args.workers is not None:
        server_config.workers = args.workers

    # Update the settings object
    settings.server = server_config

    # Override logging level if provided
    if args.log_level is not None:
        logging_config = settings.logging.model_copy()
        logging_config.level = args.log_level.upper()
        settings.logging = logging_config

    return settings


def show_configuration(settings):
    """Display current configuration."""
    print("Current RVC2API Configuration:")
    print("=" * 50)
    print(f"App Name: {settings.app_name}")
    print(f"App Version: {settings.app_version}")
    print(f"App Title: {settings.app_title}")
    print()

    print("Server Configuration:")
    print(f"  Host: {settings.server.host}")
    print(f"  Port: {settings.server.port}")
    print(f"  Workers: {settings.server.workers}")
    print(f"  Reload: {settings.server.reload}")
    print(f"  Debug: {settings.server.debug}")
    print(f"  Root Path: {settings.server.root_path or '(none)'}")
    print(f"  Access Log: {settings.server.access_log}")
    print(f"  Keep Alive Timeout: {settings.server.timeout_keep_alive}s")
    print(f"  Graceful Shutdown Timeout: {settings.server.timeout_graceful_shutdown}s")
    print()

    print("CORS Configuration:")
    print(f"  Allowed Origins: {', '.join(settings.cors.allowed_origins)}")
    print(f"  Allow Credentials: {settings.cors.allowed_credentials}")
    print(f"  Allowed Methods: {', '.join(settings.cors.allowed_methods)}")
    print(f"  Allowed Headers: {', '.join(settings.cors.allowed_headers)}")
    print()

    print("CAN Bus Configuration:")
    print(f"  Bus Type: {settings.canbus.bustype}")
    print(f"  Channels: {', '.join(settings.canbus.channels)}")
    print(f"  Bitrate: {settings.canbus.bitrate}")
    print()

    print("Logging Configuration:")
    print(f"  Level: {settings.logging.level}")
    print(f"  Log to File: {settings.logging.log_to_file}")
    if settings.logging.log_file:
        print(f"  Log File: {settings.logging.log_file}")
    print()

    print("Feature Flags:")
    print(f"  Maintenance Tracking: {settings.features.enable_maintenance_tracking}")
    print(f"  Notifications: {settings.features.enable_notifications}")
    print(f"  API Docs: {settings.features.enable_api_docs}")
    print(f"  Metrics: {settings.features.enable_metrics}")
    print()


if __name__ == "__main__":
    # Set up early logging before anything else
    setup_early_logging()

    # Parse CLI arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    try:
        # Get settings from configuration
        settings = get_settings()

        # Show configuration if requested
        if args.config:
            show_configuration(settings)
            sys.exit(0)

        # Override settings with command line arguments
        settings = override_settings_from_args(settings, args)

        # Configure unified logging for both app and Uvicorn
        log_config, root_logger = configure_unified_logging(settings.logging)

        logger = logging.getLogger(__name__)
        logger.info("Starting rvc2api backend server")
        logger.info("Unified logging with consistent formatting enabled for all loggers")

        if settings.is_development:
            logger.info("Running in development mode")
        else:
            logger.info("Running in production mode")

        # Get Uvicorn configuration from settings
        uvicorn_config = settings.get_uvicorn_config()

        # Add SSL configuration if available
        ssl_config = settings.get_uvicorn_ssl_config()
        uvicorn_config.update(ssl_config)

        # Add log configuration
        uvicorn_config.update(
            {
                "log_level": settings.logging.level.lower(),
                "log_config": log_config,
            }
        )

        # Log SSL status
        if ssl_config:
            logger.info("SSL/TLS enabled - server will run on HTTPS")
        else:
            logger.info("SSL/TLS not configured - server will run on HTTP")

        logger.info(f"Server starting on {uvicorn_config['host']}:{uvicorn_config['port']}")

        # Run the modernized backend with unified logging configuration
        uvicorn.run(
            "backend.main:app",
            **uvicorn_config,
        )

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.exception(f"Failed to start server: {e}")
        sys.exit(1)
