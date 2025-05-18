"""
core_daemon

Core API service for rvc2api, providing a FastAPI-based backend daemon with
WebSocket support and a web UI for monitoring and controlling RV-C devices.

This package contains the main API service, including routers, models,
configuration, and the web UI components.

Modules:
    - app_state: Application state management and initialization
    - can_manager: CAN bus connection and message handling
    - can_processing: RV-C message processing and routing
    - config: Application configuration and environment setup
    - main: FastAPI application setup and server entry point
    - models: Pydantic models for API request/response validation
    - websocket: WebSocket handler for real-time communication
"""

from core_daemon._version import VERSION
from core_daemon.app_state import initialize_app_from_config
from core_daemon.config import configure_logger, get_actual_paths
from core_daemon.main import app, create_app, main

__all__ = [
    "VERSION",
    "app",
    "create_app",
    "main",
    "initialize_app_from_config",
    "configure_logger",
    "get_actual_paths",
]
