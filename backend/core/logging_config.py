"""
Logging configuration module for the rvc2api backend.

This module provides comprehensive logging configuration that matches the functionality
of the old core_daemon system, including coloredlogs integration and WebSocket log handler support.
"""

import logging
import os
from typing import TYPE_CHECKING

try:
    import coloredlogs

    HAS_COLOREDLOGS = True
except ImportError:
    HAS_COLOREDLOGS = False

from backend.core.config import LoggingSettings

if TYPE_CHECKING:
    from backend.websocket.handlers import WebSocketManager

logger = logging.getLogger(__name__)


def configure_logging(
    settings: LoggingSettings | None = None,
    websocket_manager: "WebSocketManager | None" = None,
) -> logging.Logger:
    """
    Configure comprehensive logging for the backend application.

    This function sets up logging similar to the old core_daemon system with:
    - Proper log level configuration from environment variables
    - Coloredlogs integration for console output (if available)
    - Optional WebSocket log handler for real-time log streaming
    - Proper handler management to avoid duplicates

    Args:
        settings (LoggingSettings | None): Logging configuration settings.
                                         If None, defaults will be used.
        websocket_manager (WebSocketManager | None): WebSocket manager for log streaming.
                                                    If provided, adds WebSocket log handler.

    Returns:
        logging.Logger: The configured root logger
    """
    root_logger = logging.getLogger()

    # Get log level from environment or settings
    if settings:
        log_level_str = settings.level
        log_format = settings.format
    else:
        log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Convert log level string to integer
    log_level_int = getattr(logging, log_level_str, None)
    if not isinstance(log_level_int, int):
        logger.warning(f"Invalid LOG_LEVEL '{log_level_str}'. Defaulting to INFO.")
        log_level_int = logging.INFO

    # Set the root logger's level to DEBUG to allow all messages through
    # Individual handlers will filter based on their own levels
    root_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to prevent duplicates
    # Important: iterate over a copy of the list for safe removal
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    # Configure console logging
    if HAS_COLOREDLOGS:
        # Use coloredlogs for enhanced console output
        coloredlogs.install(
            level=log_level_int,
            fmt=log_format,
            logger=root_logger,
            reconfigure=True,
        )
        logger.info("Coloredlogs configured for enhanced console output")
    else:
        # Fallback to basic console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level_int)
        formatter = logging.Formatter(log_format)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        logger.info("Basic console logging configured (coloredlogs not available)")

    # Add WebSocket log handler if websocket_manager is provided
    if websocket_manager:
        try:
            import asyncio

            from backend.websocket.handlers import WebSocketLogHandler

            # Get the current event loop or create a new one
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            ws_handler = WebSocketLogHandler(websocket_manager, loop)
            ws_handler.setLevel(log_level_int)
            formatter = logging.Formatter(log_format)
            ws_handler.setFormatter(formatter)
            root_logger.addHandler(ws_handler)
            logger.info("WebSocket log handler configured for real-time log streaming")
        except Exception as e:
            logger.warning(f"Failed to configure WebSocket log handler: {e}")

    # Add file logging if configured
    if settings and settings.log_to_file and settings.log_file:
        try:
            # Ensure log directory exists
            settings.log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(settings.log_file)
            file_handler.setLevel(log_level_int)
            formatter = logging.Formatter(log_format)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            logger.info(f"File logging configured: {settings.log_file}")
        except Exception as e:
            logger.warning(f"Failed to configure file logging: {e}")

    logger.info(f"Logging configured with level: {log_level_str}")
    return root_logger


def setup_early_logging() -> None:
    """
    Set up basic logging early in the application startup process.

    This function provides minimal logging configuration before the full
    application configuration is loaded. It's useful for logging during
    the initial startup phase.
    """
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level_int = getattr(logging, log_level_str, logging.INFO)

    # Basic configuration for early startup
    logging.basicConfig(
        level=log_level_int,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,  # Override any existing configuration
    )

    logger.info(f"Early logging configured with level: {log_level_str}")


def update_websocket_logging(websocket_manager: "WebSocketManager") -> None:
    """
    Add or update WebSocket logging to an already configured logger.

    This function is useful when the WebSocket manager becomes available
    after the initial logging configuration.

    Args:
        websocket_manager (WebSocketManager): WebSocket manager for log streaming
    """
    root_logger = logging.getLogger()

    # Check if WebSocket handler already exists
    from backend.websocket.handlers import WebSocketLogHandler

    has_ws_handler = any(
        isinstance(handler, WebSocketLogHandler) for handler in root_logger.handlers
    )

    if not has_ws_handler:
        try:
            import asyncio

            from backend.websocket.handlers import WebSocketLogHandler

            # Get the current event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                logger.warning("No event loop available for WebSocket logging")
                return

            ws_handler = WebSocketLogHandler(websocket_manager, loop)
            # Use the same level as the root logger's first handler
            if root_logger.handlers:
                ws_handler.setLevel(root_logger.handlers[0].level)
            else:
                ws_handler.setLevel(logging.INFO)

            # Use the same formatter as existing handlers if available
            if root_logger.handlers and root_logger.handlers[0].formatter:
                ws_handler.setFormatter(root_logger.handlers[0].formatter)
            else:
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                ws_handler.setFormatter(formatter)

            root_logger.addHandler(ws_handler)
            logger.info("WebSocket log handler added to existing logging configuration")
        except Exception as e:
            logger.warning(f"Failed to add WebSocket log handler: {e}")
