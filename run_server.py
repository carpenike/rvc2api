#!/usr/bin/env python3
"""
Entry point to run the rvc2api backend server.

This script runs the modernized backend using the new FastAPI application
structure with proper service-oriented architecture.
"""
import argparse
import logging
import os

import uvicorn
from dotenv import load_dotenv

from backend.core.config import get_settings
from backend.core.logging_config import configure_unified_logging, setup_early_logging

# Load environment variables from .env if present
load_dotenv()

if __name__ == "__main__":
    # Set up early logging before anything else
    setup_early_logging()

    # Parse CLI arguments with env var defaults
    parser = argparse.ArgumentParser(description="Run the rvc2api backend server.")
    parser.add_argument(
        "--host",
        type=str,
        default=os.getenv("RVC2API_HOST", "0.0.0.0"),
        help="Host to bind (default: RVC2API_HOST env var or 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("RVC2API_PORT", "8000")),
        help="Port to bind (default: RVC2API_PORT env var or 8000)",
    )
    parser.add_argument(
        "--reload",
        action=(
            "store_true"
            if os.getenv("RVC2API_RELOAD", "false").lower() in ("1", "true", "yes")
            else "store_false"
        ),
        help="Enable auto-reload (default: RVC2API_RELOAD env var)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "info"),
        help="Uvicorn log level (default: LOG_LEVEL env var or 'info')",
    )
    args = parser.parse_args()

    # Get settings and configure unified logging for both app and Uvicorn
    settings = get_settings()
    log_config, root_logger = configure_unified_logging(settings.logging)

    logger = logging.getLogger(__name__)
    logger.info("Starting rvc2api backend server")
    logger.info("Unified logging with consistent formatting enabled for all loggers")

    # Normalize and validate log level for uvicorn
    valid_log_levels = {"critical", "error", "warning", "info", "debug", "trace"}
    log_level = str(args.log_level).lower()
    if log_level not in valid_log_levels:
        logger.warning(f"Invalid log level '{args.log_level}' provided. Falling back to 'info'.")
        log_level = "info"

    # Run the modernized backend with unified logging configuration
    uvicorn.run(
        "backend.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=log_level,
        log_config=log_config,
    )
