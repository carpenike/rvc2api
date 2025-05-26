#!/usr/bin/env python3
"""
Entry point to run the rvc2api backend server.

This script runs the modernized backend using the new FastAPI application
structure with proper service-oriented architecture.
"""
import logging

import uvicorn

from backend.core.config import get_settings
from backend.core.logging_config import configure_logging, setup_early_logging

if __name__ == "__main__":
    # Set up early logging before anything else
    setup_early_logging()

    # Get settings and configure comprehensive logging
    settings = get_settings()
    configure_logging(settings.logging)

    logger = logging.getLogger(__name__)
    logger.info("Starting rvc2api backend server")

    # Run the modernized backend
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
